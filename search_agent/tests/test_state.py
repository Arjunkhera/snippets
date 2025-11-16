"""
Unit tests for state management.

Tests the core state schema, initialization, and helper functions.
"""

import pytest
from datetime import datetime

from search_agent.core.state import (
    SearchAgentState,
    create_initial_state,
    update_state_timestamp,
    add_error_to_state,
    is_multi_step_query,
    has_more_steps,
    get_current_step_description,
)
from search_agent.core.models import QueryPlan, Step


def test_create_initial_state():
    """Test state initialization with required fields."""
    state = create_initial_state(
        user_query="List documents in Tax folder",
        conversation_id="conv-123"
    )

    # Check required fields
    assert state["user_query"] == "List documents in Tax folder"
    assert state["conversation_id"] == "conv-123"
    assert state["current_step"] == 1
    assert state["total_steps"] == 0
    assert state["retry_count"] == 0
    assert state["step_results"] == {}
    assert state["errors"] == []

    # Check timestamps
    assert state["created_at"]
    assert state["last_updated"]

    # Check conversation history
    assert len(state["conversation_history"]) == 1
    assert state["conversation_history"][0]["role"] == "user"
    assert state["conversation_history"][0]["content"] == "List documents in Tax folder"


def test_create_initial_state_with_history():
    """Test state initialization with existing conversation history."""
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]

    state = create_initial_state(
        user_query="List documents",
        conversation_id="conv-456",
        conversation_history=history
    )

    # Should append new message to history
    assert len(state["conversation_history"]) == 3
    assert state["conversation_history"][-1]["content"] == "List documents"


def test_update_state_timestamp():
    """Test timestamp update."""
    state = create_initial_state("test", "conv-1")
    original_timestamp = state["last_updated"]

    # Small delay to ensure timestamp changes
    import time
    time.sleep(0.01)

    updated = update_state_timestamp(state)
    assert updated["last_updated"] != original_timestamp
    assert updated["created_at"] == state["created_at"]  # Shouldn't change


def test_add_error_to_state():
    """Test adding errors to state."""
    state = create_initial_state("test", "conv-1")

    # Add first error
    state = add_error_to_state(state, "Error 1")
    assert len(state["errors"]) == 1
    assert state["errors"][0] == "Error 1"

    # Add second error
    state = add_error_to_state(state, "Error 2")
    assert len(state["errors"]) == 2
    assert state["errors"][1] == "Error 2"


def test_is_multi_step_query():
    """Test multi-step query detection."""
    state = create_initial_state("test", "conv-1")

    # Single-step
    state["total_steps"] = 1
    assert not is_multi_step_query(state)

    # Multi-step
    state["total_steps"] = 2
    assert is_multi_step_query(state)

    # No steps
    state["total_steps"] = 0
    assert not is_multi_step_query(state)


def test_has_more_steps():
    """Test step completion checking."""
    state = create_initial_state("test", "conv-1")
    state["total_steps"] = 3

    # Step 1 of 3
    state["current_step"] = 1
    assert has_more_steps(state)

    # Step 2 of 3
    state["current_step"] = 2
    assert has_more_steps(state)

    # Step 3 of 3
    state["current_step"] = 3
    assert not has_more_steps(state)

    # Beyond steps
    state["current_step"] = 4
    assert not has_more_steps(state)


def test_get_current_step_description():
    """Test retrieving current step description."""
    state = create_initial_state("test", "conv-1")

    # No plan yet
    assert get_current_step_description(state) is None

    # Add plan
    plan = QueryPlan(
        plan_type="multi_step",
        reasoning="Test reasoning",
        total_steps=2,
        steps=[
            Step(step=1, description="First step"),
            Step(step=2, description="Second step", depends_on_step=1)
        ]
    )
    state["query_plan"] = plan
    state["current_step"] = 1
    state["total_steps"] = 2

    # Get step 1 description
    assert get_current_step_description(state) == "First step"

    # Move to step 2
    state["current_step"] = 2
    assert get_current_step_description(state) == "Second step"

    # Beyond available steps
    state["current_step"] = 3
    assert get_current_step_description(state) is None


def test_state_immutability():
    """Test that state updates return new dict (immutability)."""
    state = create_initial_state("test", "conv-1")
    original_id = id(state)

    updated = update_state_timestamp(state)
    updated_id = id(updated)

    # Should be different objects
    assert original_id != updated_id

    # But original should be unchanged
    assert state["last_updated"] == updated["created_at"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
