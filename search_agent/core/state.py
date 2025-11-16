"""
State schema for the search agent LangGraph workflow.

The state is a TypedDict that persists across all nodes in the graph.
Each node reads from and writes to this shared state.

Example:
    >>> state = create_initial_state(
    ...     user_query="List documents in Tax Documents folder",
    ...     conversation_id="conv-123"
    ... )
    >>> print(state["user_query"])
    'List documents in Tax Documents folder'
"""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

from .models import QueryPlan, StepResult, ClarificationRequest


class SearchAgentState(TypedDict, total=False):
    """
    Shared state for the search agent workflow.

    This state persists across all nodes and is checkpointed by LangGraph
    for multi-turn conversations and human-in-the-loop flows.

    All fields are optional (total=False) to allow incremental updates,
    but certain fields are required at initialization (see create_initial_state).

    State is organized into sections:
    1. INPUT - From user
    2. CLASSIFICATION - Node 1 outputs
    3. PLANNING - Node 2 outputs
    4. EXECUTION - Node 3 outputs
    5. ERROR HANDLING - Cross-cutting concerns
    6. HUMAN-IN-THE-LOOP - Clarification flows
    7. OUTPUT - Node 4 outputs
    8. METADATA - Tracking and debugging
    """

    # ============================================
    # INPUT - From User
    # ============================================

    user_query: str
    """Original natural language query from the user."""

    conversation_id: str
    """Unique identifier for this conversation."""

    conversation_history: List[Dict[str, str]]
    """
    Previous messages in the conversation.
    Format: [{"role": "user"/"assistant", "content": "..."}]
    """

    # ============================================
    # CLASSIFICATION - Node 1 (Query Classifier)
    # ============================================

    intent: str
    """
    Classified user intent.
    Values: "search", "move", "delete", "create", "other"
    """

    classification_confidence: str
    """
    Confidence in the classification.
    Values: "high", "medium", "low"
    """

    classification_reasoning: str
    """Explanation of why this classification was chosen."""

    # ============================================
    # PLANNING - Node 2 (Query Planner)
    # ============================================

    query_plan: Optional[QueryPlan]
    """
    Complete execution plan from the planner.
    Contains plan_type, reasoning, total_steps, and steps list.
    """

    total_steps: int
    """Total number of steps in the plan (extracted from query_plan)."""

    current_step: int
    """Current step being executed (1-indexed)."""

    # ============================================
    # EXECUTION - Node 3 (Query Executor)
    # ============================================

    step_results: Dict[int, StepResult]
    """
    Results from each completed step.
    Key: step number (1, 2, 3)
    Value: StepResult with complete ES document and metadata
    """

    final_results: Optional[Any]
    """
    Final results to return to the user.
    Can be a single document, list of documents, or None for errors.
    """

    # ============================================
    # ERROR HANDLING
    # ============================================

    error: Optional[str]
    """
    Fatal error message if execution failed.
    If set, execution stops and formatter generates error response.
    """

    retry_count: int
    """Current retry attempt for validation/execution errors."""

    max_retries: int
    """Maximum allowed retries (from config)."""

    # ============================================
    # HUMAN-IN-THE-LOOP
    # ============================================

    pending_clarification: Optional[ClarificationRequest]
    """
    Active clarification request.
    If set, LangGraph interrupts and waits for user response.
    """

    user_clarification_response: Optional[str]
    """User's response to a clarification request."""

    # ============================================
    # OUTPUT - Node 4 (Response Formatter)
    # ============================================

    response_message: str
    """Final formatted response message for the user."""

    metadata: Dict[str, Any]
    """
    Execution metadata for debugging and analytics.
    Contains: total_steps_executed, execution_time_ms, result_count, plan_type
    """

    # ============================================
    # METADATA - Tracking and Debugging
    # ============================================

    created_at: str
    """ISO timestamp when state was created."""

    last_updated: str
    """ISO timestamp of last state update."""

    errors: List[str]
    """List of all error messages encountered (non-fatal)."""


def create_initial_state(
    user_query: str,
    conversation_id: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> SearchAgentState:
    """
    Create a new initial state for a search agent workflow.

    This function initializes all required fields with sensible defaults.
    Nodes will populate additional fields as the workflow progresses.

    Args:
        user_query: Natural language query from the user
        conversation_id: Unique identifier for this conversation
        conversation_history: Optional previous messages in the conversation

    Returns:
        Initialized SearchAgentState ready for graph execution

    Example:
        >>> state = create_initial_state(
        ...     user_query="List documents in Tax Documents folder",
        ...     conversation_id="conv-123"
        ... )
        >>> state["user_query"]
        'List documents in Tax Documents folder'
    """
    now = datetime.now().isoformat()

    # Build conversation history
    history = conversation_history or []
    history.append({"role": "user", "content": user_query})

    return SearchAgentState(
        # Input
        user_query=user_query,
        conversation_id=conversation_id,
        conversation_history=history,

        # Classification (populated by Node 1)
        intent="",
        classification_confidence="",
        classification_reasoning="",

        # Planning (populated by Node 2)
        query_plan=None,
        total_steps=0,
        current_step=1,

        # Execution (populated by Node 3)
        step_results={},
        final_results=None,

        # Error handling
        error=None,
        retry_count=0,
        max_retries=3,  # Default, can be overridden

        # Human-in-the-loop
        pending_clarification=None,
        user_clarification_response=None,

        # Output (populated by Node 4)
        response_message="",
        metadata={},

        # Metadata
        created_at=now,
        last_updated=now,
        errors=[]
    )


def update_state_timestamp(state: SearchAgentState) -> SearchAgentState:
    """
    Update the last_updated timestamp to current time.

    This should be called by nodes that modify state to track when
    changes were made.

    Args:
        state: Current state

    Returns:
        Updated state with new last_updated timestamp

    Example:
        >>> state = create_initial_state("test", "conv-1")
        >>> updated = update_state_timestamp(state)
        >>> updated["last_updated"] != updated["created_at"]
        True
    """
    return {
        **state,
        "last_updated": datetime.now().isoformat()
    }


def add_error_to_state(state: SearchAgentState, error_message: str) -> SearchAgentState:
    """
    Add a non-fatal error message to the state's error list.

    Use this for warnings and non-fatal errors that don't stop execution.
    For fatal errors, set state["error"] instead.

    Args:
        state: Current state
        error_message: Error message to add

    Returns:
        Updated state with error appended to errors list

    Example:
        >>> state = create_initial_state("test", "conv-1")
        >>> state = add_error_to_state(state, "Validation warning: field may not exist")
        >>> len(state["errors"])
        1
    """
    errors = state.get("errors", [])
    errors.append(error_message)

    return {
        **state,
        "errors": errors,
        "last_updated": datetime.now().isoformat()
    }


def is_multi_step_query(state: SearchAgentState) -> bool:
    """
    Check if the current query is a multi-step query.

    Args:
        state: Current state

    Returns:
        True if query plan is multi-step, False otherwise

    Example:
        >>> state = create_initial_state("test", "conv-1")
        >>> state["total_steps"] = 2
        >>> is_multi_step_query(state)
        True
    """
    return state.get("total_steps", 0) > 1


def has_more_steps(state: SearchAgentState) -> bool:
    """
    Check if there are more steps to execute.

    Args:
        state: Current state

    Returns:
        True if current_step < total_steps, False otherwise

    Example:
        >>> state = create_initial_state("test", "conv-1")
        >>> state["total_steps"] = 2
        >>> state["current_step"] = 1
        >>> has_more_steps(state)
        True
    """
    return state.get("current_step", 0) < state.get("total_steps", 0)


def get_current_step_description(state: SearchAgentState) -> Optional[str]:
    """
    Get the description of the current step being executed.

    Args:
        state: Current state

    Returns:
        Description string or None if not available

    Example:
        >>> state = create_initial_state("test", "conv-1")
        >>> # After planner populates query_plan...
        >>> desc = get_current_step_description(state)
    """
    if not state.get("query_plan"):
        return None

    current_step = state.get("current_step", 1)
    plan = state["query_plan"]

    if not plan or current_step > len(plan.steps):
        return None

    return plan.steps[current_step - 1].description


def get_previous_step_result(state: SearchAgentState, step_number: int) -> Optional[StepResult]:
    """
    Get the result from a previous step.

    Args:
        state: Current state
        step_number: Step number to retrieve (1-indexed)

    Returns:
        StepResult or None if not found

    Example:
        >>> state = create_initial_state("test", "conv-1")
        >>> # After executor completes step 1...
        >>> result = get_previous_step_result(state, 1)
        >>> result.source["systemAttributes"]["id"]
        'folder-id-123'
    """
    return state.get("step_results", {}).get(step_number)
