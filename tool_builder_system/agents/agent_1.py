"""
Agent 1: Requirements Architect

Handles requirements gathering, PRD generation, and user approval.
"""

import json
import os
from pathlib import Path
from typing import Optional
from anthropic import Anthropic

# Load system prompt
AGENT_1_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "agent_1_system_prompt.md"
with open(AGENT_1_PROMPT_PATH, 'r') as f:
    AGENT_1_SYSTEM_PROMPT = f.read()


class Agent1:
    """Requirements Architect Agent."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Agent 1.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.system_prompt = AGENT_1_SYSTEM_PROMPT

    def discovery(self, state: dict) -> dict:
        """
        Phase 1: Interactive Discovery
        Gather requirements through conversation with the user.

        Args:
            state: Current workflow state

        Returns:
            Updated state with agent response
        """
        # Build conversation history for Claude
        messages = self._build_messages(state)

        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=messages
        )

        # Extract response text
        response_text = response.content[0].text

        # Update state
        state["conversation_history"].append({
            "role": "assistant",
            "content": response_text
        })
        state["current_phase"] = "discovery"

        return state

    def generate_artifacts(self, state: dict) -> dict:
        """
        Phase 2: Artifact Generation
        Generate PRD and JSON schema based on gathered requirements.

        Args:
            state: Current workflow state

        Returns:
            Updated state with generated artifacts
        """
        # Add instruction to generate artifacts
        generation_prompt = """
Now that we have all the necessary information, please generate:

1. The complete PRD markdown document
2. The OpenAI function JSON schema

Please present both artifacts clearly for my review.
"""

        messages = self._build_messages(state)
        messages.append({
            "role": "user",
            "content": generation_prompt
        })

        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=self.system_prompt,
            messages=messages
        )

        response_text = response.content[0].text

        # Try to extract PRD and JSON from response
        prd_content, json_schema = self._extract_artifacts(response_text, state)

        # Update state
        state["conversation_history"].append({
            "role": "user",
            "content": generation_prompt
        })
        state["conversation_history"].append({
            "role": "assistant",
            "content": response_text
        })

        if prd_content:
            state["prd_content"] = prd_content
        if json_schema:
            state["json_schema"] = json_schema

        state["current_phase"] = "review"

        return state

    def review(self, state: dict, user_feedback: str) -> dict:
        """
        Phase 3: User Review & Iteration
        Handle user feedback on generated artifacts.

        Args:
            state: Current workflow state
            user_feedback: User's response to the artifacts

        Returns:
            Updated state with approval status or iteration request
        """
        # Check if user approved
        approval_phrases = [
            "approve", "looks good", "lgtm", "proceed",
            "yes", "continue", "perfect", "great"
        ]

        user_feedback_lower = user_feedback.lower()
        is_approved = any(phrase in user_feedback_lower for phrase in approval_phrases)

        # Update conversation history
        state["conversation_history"].append({
            "role": "user",
            "content": user_feedback
        })

        if is_approved:
            # User approved
            state["prd_approved"] = True
            state["current_phase"] = "approved"

            # Add confirmation message
            confirmation = "Great! The PRD and JSON schema have been approved. Ready to proceed to implementation (Agent 2)."
            state["conversation_history"].append({
                "role": "assistant",
                "content": confirmation
            })

            return state
        else:
            # User wants changes - continue conversation
            messages = self._build_messages(state)

            # Call Claude to handle the feedback
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=self.system_prompt,
                messages=messages
            )

            response_text = response.content[0].text

            # Try to extract updated artifacts if present
            prd_content, json_schema = self._extract_artifacts(response_text, state)

            state["conversation_history"].append({
                "role": "assistant",
                "content": response_text
            })

            if prd_content:
                state["prd_content"] = prd_content
            if json_schema:
                state["json_schema"] = json_schema

            state["current_phase"] = "review"

            return state

    def handle_escalation(self, state: dict, escalation_question: str) -> dict:
        """
        Phase 5: Reactivation (Escalation Handling)
        Handle clarification requests from downstream agents.

        Args:
            state: Current workflow state
            escalation_question: Question from downstream agent

        Returns:
            Updated state with escalation response
        """
        # Add escalation context to conversation
        escalation_context = f"""
[ESCALATION from {state.get('escalation_from_agent', 'downstream agent')}]

The implementation/testing agent has encountered an ambiguity in the PRD:

{escalation_question}

Please discuss this with me to clarify the requirements, then update the PRD and JSON schema accordingly.
"""

        messages = self._build_messages(state)
        messages.append({
            "role": "user",
            "content": escalation_context
        })

        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=messages
        )

        response_text = response.content[0].text

        state["conversation_history"].append({
            "role": "user",
            "content": escalation_context
        })
        state["conversation_history"].append({
            "role": "assistant",
            "content": response_text
        })

        state["current_phase"] = "escalation_handling"

        return state

    def _build_messages(self, state: dict) -> list[dict]:
        """
        Build message list for Claude API from conversation history.

        Args:
            state: Current workflow state

        Returns:
            List of messages in Claude format
        """
        messages = []

        for msg in state.get("conversation_history", []):
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        return messages

    def _extract_artifacts(self, response_text: str, state: dict) -> tuple[Optional[str], Optional[dict]]:
        """
        Extract PRD markdown and JSON schema from agent response.

        Args:
            response_text: Agent's response text
            state: Current state (for fallback values)

        Returns:
            Tuple of (prd_content, json_schema)
        """
        prd_content = None
        json_schema = None

        # Try to extract PRD (look for markdown code block or ## PRD section)
        if "# Tool:" in response_text or "## PRD:" in response_text:
            # Extract the PRD section
            lines = response_text.split('\n')
            prd_lines = []
            in_prd = False

            for line in lines:
                if line.startswith("# Tool:") or line.startswith("## PRD"):
                    in_prd = True
                    if line.startswith("## PRD"):
                        continue  # Skip the header
                elif in_prd and (line.startswith("---") or line.startswith("## JSON")):
                    break
                elif in_prd:
                    prd_lines.append(line)

            if prd_lines:
                prd_content = '\n'.join(prd_lines).strip()

        # Try to extract JSON schema
        # Look for JSON code blocks
        if "```json" in response_text:
            json_blocks = []
            lines = response_text.split('\n')
            in_json_block = False
            current_block = []

            for line in lines:
                if line.strip().startswith("```json"):
                    in_json_block = True
                    current_block = []
                elif in_json_block and line.strip().startswith("```"):
                    in_json_block = False
                    json_blocks.append('\n'.join(current_block))
                elif in_json_block:
                    current_block.append(line)

            # Try to parse JSON blocks
            for block in json_blocks:
                try:
                    parsed = json.loads(block)
                    # Check if it looks like a function schema
                    if isinstance(parsed, dict):
                        # Could be the outer wrapper or direct schema
                        if "type" in parsed and parsed["type"] == "function":
                            # Direct schema
                            func_name = parsed.get("name", state.get("function_name"))
                            json_schema = {func_name: parsed}
                            break
                        else:
                            # Might be wrapper with function_name as key
                            for key, value in parsed.items():
                                if isinstance(value, dict) and value.get("type") == "function":
                                    json_schema = parsed
                                    # Extract function name if not already set
                                    if not state.get("function_name"):
                                        state["function_name"] = key
                                    break
                            if json_schema:
                                break
                except json.JSONDecodeError:
                    continue

        return prd_content, json_schema
