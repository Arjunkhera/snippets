"""
LangGraph workflow for the Multi-Agent Tool Builder System.

Phase 1 (MVP): Agent 1 only
Phase 2+: Will add Agent 2, 3, 4
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ToolBuilderState, update_state_phase
from .agents.agent_1 import Agent1


class ToolBuilderWorkflow:
    """
    Main workflow orchestrator for the tool builder system.

    Phase 1: Implements Agent 1 (Requirements Architect) with approval gate.
    """

    def __init__(self, agent_1: Agent1):
        """
        Initialize the workflow.

        Args:
            agent_1: Initialized Agent 1 instance
        """
        self.agent_1 = agent_1
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Phase 1 structure:
        - agent_1_discovery: Interactive requirements gathering
        - agent_1_generate: Generate PRD and JSON schema
        - agent_1_review: User approval gate
        - end: Completion (ready for Agent 2 in Phase 2)

        Returns:
            Compiled StateGraph
        """
        # Create graph with our state schema
        workflow = StateGraph(ToolBuilderState)

        # Add Agent 1 nodes
        workflow.add_node("agent_1_discovery", self._agent_1_discovery_node)
        workflow.add_node("agent_1_generate", self._agent_1_generate_node)
        workflow.add_node("agent_1_review", self._agent_1_review_node)
        workflow.add_node("complete_phase_1", self._complete_phase_1_node)

        # Set entry point
        workflow.set_entry_point("agent_1_discovery")

        # Add edges
        # Discovery -> Generate (when user provides info for artifact generation)
        workflow.add_edge("agent_1_discovery", "agent_1_generate")

        # Generate -> Review (present artifacts to user)
        workflow.add_edge("agent_1_generate", "agent_1_review")

        # Review has conditional routing
        workflow.add_conditional_edges(
            "agent_1_review",
            self._route_after_review,
            {
                "approved": "complete_phase_1",
                "iterate": "agent_1_generate",
                "continue_discovery": "agent_1_discovery"
            }
        )

        # Complete -> END
        workflow.add_edge("complete_phase_1", END)

        return workflow

    def _agent_1_discovery_node(self, state: ToolBuilderState) -> ToolBuilderState:
        """
        Agent 1 Discovery Phase Node.

        Handles interactive requirements gathering.

        Args:
            state: Current state

        Returns:
            Updated state
        """
        state = update_state_phase(state, "agent_1", "discovery")
        state = self.agent_1.discovery(state)
        return state

    def _agent_1_generate_node(self, state: ToolBuilderState) -> ToolBuilderState:
        """
        Agent 1 Generate Phase Node.

        Generates PRD and JSON schema artifacts.

        Args:
            state: Current state

        Returns:
            Updated state
        """
        state = update_state_phase(state, "agent_1", "generate")
        state = self.agent_1.generate_artifacts(state)
        return state

    def _agent_1_review_node(self, state: ToolBuilderState) -> ToolBuilderState:
        """
        Agent 1 Review Phase Node.

        This is an interrupt point - the workflow will pause here for user feedback.

        Args:
            state: Current state

        Returns:
            Updated state
        """
        state = update_state_phase(state, "agent_1", "review")
        # The actual review happens when user provides feedback and workflow resumes
        return state

    def _complete_phase_1_node(self, state: ToolBuilderState) -> ToolBuilderState:
        """
        Complete Phase 1 Node.

        Marks Phase 1 as complete and prepares for Phase 2 (Agent 2).

        Args:
            state: Current state

        Returns:
            Updated state
        """
        state = update_state_phase(state, "agent_1", "completed")

        # Add completion message to conversation
        completion_message = """
Phase 1 Complete! ✓

The requirements have been gathered and approved:
- Function Name: {function_name}
- PRD: Generated and approved
- JSON Schema: Generated and approved

Phase 2 Preparation:
- Agent 2 (Implementation Specialist) will receive the PRD
- Agent 2 will implement the Python code matching the specification
- You will review and approve the implementation

[Phase 2 will be implemented in the next iteration]
""".format(function_name=state.get("function_name", "TBD"))

        state["conversation_history"].append({
            "role": "assistant",
            "content": completion_message
        })

        return state

    def _route_after_review(self, state: ToolBuilderState) -> Literal["approved", "iterate", "continue_discovery"]:
        """
        Route after user review.

        Determines next step based on approval status and user feedback.

        Args:
            state: Current state

        Returns:
            Next node to execute
        """
        # Check if PRD is approved
        if state.get("prd_approved", False):
            return "approved"

        # Check if we have artifacts to iterate on
        if state.get("prd_content") or state.get("json_schema"):
            # We have artifacts, iterate on them
            return "iterate"
        else:
            # No artifacts yet, continue discovery
            return "continue_discovery"

    def compile(self, checkpointer=None, interrupt_before=None):
        """
        Compile the workflow graph.

        Args:
            checkpointer: Optional checkpointer for state persistence
            interrupt_before: Optional list of nodes to interrupt before

        Returns:
            Compiled graph
        """
        if interrupt_before is None:
            # Default: interrupt before review for user approval
            interrupt_before = ["agent_1_review"]

        return self.graph.compile(
            checkpointer=checkpointer,
            interrupt_before=interrupt_before
        )
