"""
State management for the multi-agent tool builder system.

This module defines the shared state schema that persists across all agents
and workflow phases using LangGraph's state management.
"""

from typing import TypedDict, Optional, Any
from datetime import datetime


class ToolBuilderState(TypedDict):
    """
    Shared state schema for the tool builder workflow.

    This state is maintained throughout the entire workflow from requirements
    gathering through publishing, with each agent reading from and writing to
    this shared state.
    """

    # ===== User Input & Conversation =====
    user_input: str  # Initial user request
    conversation_history: list[dict[str, str]]  # Full chat history [{"role": "user/assistant", "content": "..."}]

    # ===== Requirements (Agent 1) =====
    function_name: Optional[str]  # Python function name
    prd_content: Optional[str]  # Full PRD markdown content
    json_schema: Optional[dict[str, Any]]  # OpenAI function schema
    prd_version: str  # Version string (e.g., "1.0", "1.1")
    prd_approved: bool  # User approval status

    # ===== Requirements Gathering Details =====
    # Collected information during Agent 1 discovery
    tool_description: Optional[str]
    input_parameters: list[dict[str, Any]]  # [{name, type, required, description, default}]
    success_output: Optional[dict[str, Any]]  # Expected success structure
    error_cases: list[dict[str, Any]]  # [{error_code, format, description}]
    constraints: list[str]  # List of constraints and behaviors

    # ===== Implementation (Agent 2) =====
    module_path: Optional[str]  # e.g., "ai_tools/file_system"
    implementation_code: Optional[str]  # Full function implementation
    implementation_approved: bool

    # ===== Testing (Agent 3) =====
    test_code: Optional[str]  # Test suite code
    test_results: Optional[dict[str, Any]]  # Execution results
    tests_passed: bool
    tests_approved: bool

    # ===== Publishing (Agent 4) =====
    version_number: Optional[str]  # Package version
    publish_target: str  # "test_pypi" or "pypi"
    package_url: Optional[str]  # Published package URL

    # ===== Workflow Control =====
    current_agent: str  # "agent_1", "agent_2", "agent_3", "agent_4"
    current_phase: str  # Specific phase within agent (e.g., "discovery", "generation", "review")
    escalation_active: bool  # Whether an escalation is in progress
    escalation_question: Optional[str]  # Question from downstream agent
    escalation_from_agent: Optional[str]  # Which agent escalated

    # ===== Metadata =====
    created_at: str  # ISO timestamp
    last_updated: str  # ISO timestamp
    errors: list[str]  # Error messages encountered


def create_initial_state(user_input: str) -> ToolBuilderState:
    """
    Create a new initial state for a tool builder workflow.

    Args:
        user_input: The user's initial request/description

    Returns:
        A new ToolBuilderState with initial values
    """
    now = datetime.now().isoformat()

    return ToolBuilderState(
        # User input
        user_input=user_input,
        conversation_history=[{"role": "user", "content": user_input}],

        # Requirements
        function_name=None,
        prd_content=None,
        json_schema=None,
        prd_version="1.0",
        prd_approved=False,

        # Requirements details
        tool_description=None,
        input_parameters=[],
        success_output=None,
        error_cases=[],
        constraints=[],

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
        publish_target="test_pypi",
        package_url=None,

        # Workflow control
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


def update_state_timestamp(state: ToolBuilderState) -> ToolBuilderState:
    """Update the last_updated timestamp to now."""
    state["last_updated"] = datetime.now().isoformat()
    return state
