"""
Core module for search agent state and models.

This module contains the state schema and data models used throughout the agent.
"""

from .models import (
    QueryPlan,
    Step,
    StepResult,
    ClarificationRequest,
    ExecutionMetadata,
)
from .state import (
    SearchAgentState,
    create_initial_state,
    update_state_timestamp,
)

__all__ = [
    # State
    "SearchAgentState",
    "create_initial_state",
    "update_state_timestamp",
    # Models
    "QueryPlan",
    "Step",
    "StepResult",
    "ClarificationRequest",
    "ExecutionMetadata",
]
