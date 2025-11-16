"""
State management for the Multi-Agent Tool Builder System.

This module defines the shared state schema used across all agents in the workflow.
"""

from typing import TypedDict, Optional, Any
from datetime import datetime


class ToolBuilderState(TypedDict, total=False):
    """
    Shared state schema for the entire tool building workflow.

    This state is maintained throughout the agent workflow and persists across
    agent transitions, approval gates, and escalations.
    """

    # User input and conversation
    user_input: str
    conversation_history: list[dict[str, str]]  # Full chat history

    # Requirements (Agent 1)
    function_name: Optional[str]
    prd_content: Optional[str]
    json_schema: Optional[dict[str, Any]]
    prd_version: str
    prd_approved: bool

    # Implementation (Agent 2) - prepared for Phase 2
    module_path: Optional[str]  # e.g., "ai_tools/file_system"
    implementation_code: Optional[str]
    implementation_approved: bool

    # Testing (Agent 3) - prepared for Phase 3
    test_code: Optional[str]
    test_results: Optional[dict[str, Any]]
    tests_passed: bool
    tests_approved: bool

    # Publishing (Agent 4) - prepared for Phase 4
    version_number: Optional[str]
    publish_target: Optional[str]  # "test_pypi" or "pypi"
    package_url: Optional[str]

    # Workflow control
    current_agent: str  # "agent_1", "agent_2", "agent_3", "agent_4"
    current_phase: str  # Specific phase within agent
    escalation_active: bool
    escalation_question: Optional[str]
    escalation_from_agent: Optional[str]

    # Metadata
    created_at: str
    last_updated: str
    errors: list[str]


def create_initial_state(user_input: str) -> ToolBuilderState:
    """
    Create initial state for a new tool building session.

    Args:
        user_input: The initial user request/description

    Returns:
        Initialized ToolBuilderState with default values
    """
    now = datetime.utcnow().isoformat()

    return ToolBuilderState(
        # User input
        user_input=user_input,
        conversation_history=[
            {
                "role": "user",
                "content": user_input,
                "timestamp": now
            }
        ],

        # Requirements
        function_name=None,
        prd_content=None,
        json_schema=None,
        prd_version="1.0",
        prd_approved=False,

        # Implementation
        module_path=None,
        implementation_code=None,
        implementation_approved=False,

        # Testing
        test_code=None,
        test_results=None,
        tests_passed=False,
        tests_approved=False,

        # Publishing
        version_number=None,
        publish_target=None,
        package_url=None,

        # Workflow
        current_agent="agent_1",
        current_phase="discovery",
        escalation_active=False,
        escalation_question=None,
        escalation_from_agent=None,

        # Metadata
        created_at=now,
        last_updated=now,
        errors=[]
    )


def add_conversation_message(
    state: ToolBuilderState,
    role: str,
    content: str
) -> ToolBuilderState:
    """
    Add a message to the conversation history.

    Args:
        state: Current state
        role: Message role ("user", "assistant", "system")
        content: Message content

    Returns:
        Updated state with new message
    """
    state["conversation_history"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    state["last_updated"] = datetime.utcnow().isoformat()
    return state


def update_state_phase(
    state: ToolBuilderState,
    agent: str,
    phase: str
) -> ToolBuilderState:
    """
    Update the current agent and phase.

    Args:
        state: Current state
        agent: Current agent identifier
        phase: Current phase within agent

    Returns:
        Updated state
    """
    state["current_agent"] = agent
    state["current_phase"] = phase
    state["last_updated"] = datetime.utcnow().isoformat()
    return state
