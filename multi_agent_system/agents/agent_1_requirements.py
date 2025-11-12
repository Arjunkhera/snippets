"""
Agent 1: Requirements Architect

This agent owns the complete requirements lifecycle from discovery through iterations.
It gathers requirements conversationally, generates PRD and JSON schema, handles user
review/iteration, and manages escalations from downstream agents.
"""

import json
import os
from typing import Any
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.types import Command, interrupt

from multi_agent_system.state import ToolBuilderState, update_state_timestamp


# Load the CreateTools.md prompt
PROMPT_FILE = "Prompts/CreateTools.md"


def load_requirements_prompt() -> str:
    """Load the Agent 1 system prompt from CreateTools.md"""
    prompt_path = os.path.join(os.getcwd(), PROMPT_FILE)
    with open(prompt_path, 'r') as f:
        return f.read()


class RequirementsArchitect:
    """
    Agent 1: Requirements Architect

    Handles:
    - Phase 1: Interactive Discovery (conversational Q&A)
    - Phase 2: Artifact Generation (PRD + JSON schema)
    - Phase 3: User Review & Iteration
    - Phase 4: Handoff Preparation (save files)
    - Phase 5: Escalation Handling (from downstream agents)
    """

    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.7):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.system_prompt = load_requirements_prompt()

    def discovery_phase(self, state: ToolBuilderState) -> dict:
        """
        Phase 1: Interactive Discovery

        Ask questions one at a time to gather complete requirements.
        This phase runs in a loop until all information is collected.
        """
        conversation = state["conversation_history"].copy()

        # Build conversation context
        messages = [SystemMessage(content=self.system_prompt)]

        # Add conversation history
        for msg in conversation:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        # Check if we're in escalation mode
        if state.get("escalation_active"):
            escalation_context = f"\n\nESCALATION FROM {state['escalation_from_agent']}: {state['escalation_question']}\n\nPlease address this question with the user and update the requirements accordingly."
            messages.append(HumanMessage(content=escalation_context))

        # Generate response
        response = self.llm.invoke(messages)
        assistant_message = response.content

        # Add assistant's question to conversation
        conversation.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Check if LLM indicates readiness to generate artifacts
        if self._is_discovery_complete(assistant_message, state):
            # Discovery complete - move to generation
            return {
                "conversation_history": conversation,
                "current_phase": "generation",
                "last_updated": datetime.now().isoformat()
            }

        # NOT ready yet - interrupt and wait for user response
        user_response = interrupt(assistant_message)

        # Process user response when resumed
        if user_response:
            conversation.append({
                "role": "user",
                "content": str(user_response)
            })

        # Return updated state fields
        return {
            "conversation_history": conversation,
            "current_phase": "discovery",
            "last_updated": datetime.now().isoformat()
        }

    def _is_discovery_complete(self, message: str, state: ToolBuilderState) -> bool:
        """
        Determine if discovery phase is complete based on LLM response.

        Looks for indicators that all information has been gathered.
        """
        indicators = [
            "all necessary details",
            "ready to generate",
            "final outputs",
            "markdown tool definition",
            "json schema"
        ]

        message_lower = message.lower()
        has_indicators = any(indicator in message_lower for indicator in indicators)

        # Also check if we have basic required information
        has_basics = (
            state.get("function_name") is not None or
            "function name" in message_lower
        )

        return has_indicators and has_basics

    def generate_artifacts(self, state: ToolBuilderState) -> ToolBuilderState:
        """
        Phase 2: Artifact Generation

        Generate PRD markdown and OpenAI JSON schema from gathered information.
        """
        conversation = state["conversation_history"]

        # Create a focused prompt for generation
        generation_prompt = f"""
Based on our conversation, please now generate the two required outputs:

1. **Markdown Tool Definition** - A comprehensive PRD following the format in PRDs/get_file_data.md
2. **OpenAI Function JSON Schema** - Following OpenAI's function calling format

Please provide both outputs clearly formatted.

Conversation summary:
{self._summarize_conversation(conversation)}
"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=generation_prompt)
        ]

        # Generate artifacts
        response = self.llm.invoke(messages)
        assistant_message = response.content

        # Update conversation
        state["conversation_history"].append({
            "role": "assistant",
            "content": assistant_message
        })

        # Extract artifacts from response
        prd_content, json_schema = self._extract_artifacts(assistant_message, state)

        state["prd_content"] = prd_content
        state["json_schema"] = json_schema
        state["current_phase"] = "review"
        state = update_state_timestamp(state)

        return state

    def _summarize_conversation(self, conversation: list[dict[str, str]]) -> str:
        """Create a summary of the conversation for context."""
        return "\n".join([f"{msg['role']}: {msg['content'][:200]}" for msg in conversation[-10:]])

    def _extract_artifacts(self, message: str, state: ToolBuilderState) -> tuple[str, dict]:
        """
        Extract PRD markdown and JSON schema from LLM response.

        Uses pattern matching and LLM assistance to extract structured artifacts.
        """
        # Try to extract JSON schema first
        json_schema = None
        prd_content = None

        # Look for JSON code blocks
        if "```json" in message:
            start = message.find("```json") + 7
            end = message.find("```", start)
            json_str = message[start:end].strip()
            try:
                json_schema = json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Look for markdown PRD
        if "# Tool:" in message or "**Description:**" in message:
            # Extract the PRD portion
            lines = message.split("\n")
            prd_lines = []
            in_prd = False

            for line in lines:
                if line.startswith("# Tool:") or "**Description:**" in line:
                    in_prd = True
                if in_prd and line.startswith("```json"):
                    break
                if in_prd:
                    prd_lines.append(line)

            prd_content = "\n".join(prd_lines).strip()

        # If extraction failed, store the full message and let review handle it
        if not prd_content:
            prd_content = message

        if not json_schema:
            json_schema = {"error": "Could not extract JSON schema"}

        return prd_content, json_schema

    def review_phase(self, state: ToolBuilderState) -> ToolBuilderState:
        """
        Phase 3: User Review & Iteration

        Present artifacts to user and handle approval/changes.
        Uses interrupt() to pause for human input.
        """
        state["current_phase"] = "review"
        state = update_state_timestamp(state)

        # Present artifacts to user
        presentation = f"""
I've generated the following artifacts for your review:

## PRD (Markdown Tool Definition)

{state['prd_content']}

---

## JSON Schema (OpenAI Function)

```json
{json.dumps(state['json_schema'], indent=2)}
```

---

Please review and let me know:
- **Approve**: Say "approve", "looks good", "proceed", or "LGTM" to continue
- **Request changes**: Provide specific feedback (e.g., "change max file size to 50MB")
- **Ask questions**: Any clarifications needed

What would you like to do?
"""

        # Add to conversation history
        state["conversation_history"].append({
            "role": "assistant",
            "content": presentation
        })

        # Interrupt for human review
        user_feedback = interrupt(presentation)

        # Process user feedback
        if user_feedback:
            state["conversation_history"].append({
                "role": "user",
                "content": str(user_feedback)
            })

            # Check if approved
            feedback_lower = str(user_feedback).lower()
            approval_keywords = ["approve", "looks good", "proceed", "lgtm", "yes", "continue"]

            if any(keyword in feedback_lower for keyword in approval_keywords):
                state["prd_approved"] = True
                state["current_phase"] = "save"
            else:
                # User wants changes - go back to discovery/generation
                state["prd_approved"] = False
                state["current_phase"] = "discovery"

        state = update_state_timestamp(state)
        return state

    def save_artifacts(self, state: ToolBuilderState) -> ToolBuilderState:
        """
        Phase 4: Handoff Preparation

        Save PRD to file and update tool_registry.json
        """
        function_name = state["function_name"]

        if not function_name:
            # Try to extract from JSON schema
            if state["json_schema"] and "name" in state["json_schema"]:
                function_name = state["json_schema"]["name"]
            else:
                state["errors"].append("Cannot save: function_name not determined")
                return state

        # Ensure PRDs directory exists
        prd_dir = os.path.join(os.getcwd(), "PRDs")
        os.makedirs(prd_dir, exist_ok=True)

        # Save PRD
        prd_path = os.path.join(prd_dir, f"{function_name}.md")
        with open(prd_path, 'w') as f:
            f.write(state["prd_content"])

        # Update tool_registry.json
        registry_path = os.path.join(os.getcwd(), "tool_registry.json")

        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
        except FileNotFoundError:
            registry = {}

        registry[function_name] = state["json_schema"]

        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        # Update state
        state["function_name"] = function_name
        state["current_phase"] = "complete"
        state = update_state_timestamp(state)

        # Add success message to conversation
        state["conversation_history"].append({
            "role": "assistant",
            "content": f"✅ Artifacts saved successfully!\n\n- PRD: {prd_path}\n- Registry updated: {registry_path}\n\nReady to proceed to Agent 2 (Implementation)."
        })

        return state

    def handle_escalation(self, state: ToolBuilderState) -> ToolBuilderState:
        """
        Phase 5: Escalation Handling

        Handle clarification questions from downstream agents.
        """
        if not state.get("escalation_active"):
            return state

        # Process the escalation through discovery phase
        state = self.discovery_phase(state)

        # If discovery leads to new artifacts, regenerate
        if state["current_phase"] == "generation":
            state = self.generate_artifacts(state)
            # Bump version
            current_version = float(state["prd_version"])
            state["prd_version"] = str(current_version + 0.1)

        # Clear escalation flag after handling
        state["escalation_active"] = False
        state["escalation_question"] = None
        state["escalation_from_agent"] = None

        return state


# Node functions for LangGraph


def agent_1_discovery(state: ToolBuilderState) -> ToolBuilderState:
    """LangGraph node: Agent 1 discovery phase"""
    agent = RequirementsArchitect()
    return agent.discovery_phase(state)


def agent_1_generate(state: ToolBuilderState) -> ToolBuilderState:
    """LangGraph node: Agent 1 artifact generation"""
    agent = RequirementsArchitect()
    return agent.generate_artifacts(state)


def agent_1_review(state: ToolBuilderState) -> ToolBuilderState:
    """LangGraph node: Agent 1 user review"""
    agent = RequirementsArchitect()
    return agent.review_phase(state)


def agent_1_save(state: ToolBuilderState) -> ToolBuilderState:
    """LangGraph node: Agent 1 save artifacts"""
    agent = RequirementsArchitect()
    return agent.save_artifacts(state)
