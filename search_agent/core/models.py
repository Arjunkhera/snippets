"""
Pydantic models for type-safe data structures in the search agent.

These models provide validation, serialization, and documentation for
all data structures used in the agent state and node interactions.

Example:
    >>> plan = QueryPlan(
    ...     plan_type="multi_step",
    ...     reasoning="Need to resolve folder name to ID",
    ...     total_steps=2,
    ...     steps=[
    ...         Step(step=1, description="Find folder by name"),
    ...         Step(step=2, description="Find documents in folder", depends_on_step=1)
    ...     ]
    ... )
    >>> print(plan.model_dump_json(indent=2))
"""

from typing import Any, Dict, List, Literal, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Step(BaseModel):
    """
    A single step in a query execution plan.

    Attributes:
        step: Step number (1-indexed)
        description: Natural language description of what this step should accomplish
        depends_on_step: Optional step number this step depends on (for multi-step queries)

    Example:
        >>> step = Step(
        ...     step=1,
        ...     description="Find the folder named 'Tax Documents'"
        ... )
    """

    step: int = Field(
        ...,
        ge=1,
        description="Step number (1-indexed)"
    )

    description: str = Field(
        ...,
        min_length=10,
        description="Natural language description of what to accomplish in this step"
    )

    depends_on_step: Optional[int] = Field(
        default=None,
        ge=1,
        description="Step number this step depends on (None for independent steps)"
    )

    @field_validator("depends_on_step")
    @classmethod
    def validate_dependency(cls, v, info):
        """Validate that depends_on_step is less than current step."""
        if v is not None and "step" in info.data:
            if v >= info.data["step"]:
                raise ValueError(
                    f"depends_on_step ({v}) must be less than current step ({info.data['step']})"
                )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "step": 1,
                "description": "Find the folder named 'Tax Documents' to get its folder ID",
                "depends_on_step": None
            }
        }


class QueryPlan(BaseModel):
    """
    Complete execution plan for a search query.

    The planner node generates this structure to describe how a query
    should be executed (single-step or multi-step).

    Attributes:
        plan_type: Type of plan ("single_step" or "multi_step")
        reasoning: Explanation of why this approach was chosen
        total_steps: Total number of steps in the plan
        steps: List of step descriptions

    Example:
        >>> plan = QueryPlan(
        ...     plan_type="multi_step",
        ...     reasoning="User references folder by name but documents need folder ID",
        ...     total_steps=2,
        ...     steps=[
        ...         Step(step=1, description="Find folder named 'Tax Documents'"),
        ...         Step(step=2, description="Find documents in that folder", depends_on_step=1)
        ...     ]
        ... )
    """

    plan_type: Literal["single_step", "multi_step"] = Field(
        ...,
        description="Whether the query requires single or multiple steps"
    )

    reasoning: str = Field(
        ...,
        min_length=20,
        description="Detailed explanation of the gap analysis and why this approach is needed"
    )

    total_steps: int = Field(
        ...,
        ge=1,
        le=3,
        description="Total number of steps (1-3)"
    )

    steps: List[Step] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="List of step descriptions"
    )

    @field_validator("total_steps")
    @classmethod
    def validate_total_steps(cls, v, info):
        """Validate that total_steps matches the length of steps array."""
        if "steps" in info.data:
            if v != len(info.data["steps"]):
                raise ValueError(
                    f"total_steps ({v}) must match length of steps array ({len(info.data['steps'])})"
                )
        return v

    @field_validator("steps")
    @classmethod
    def validate_steps_sequential(cls, v):
        """Validate that steps are numbered sequentially starting from 1."""
        expected_step = 1
        for step in v:
            if step.step != expected_step:
                raise ValueError(
                    f"Steps must be sequential starting from 1. "
                    f"Expected step {expected_step}, got {step.step}"
                )
            expected_step += 1
        return v

    @field_validator("plan_type")
    @classmethod
    def validate_plan_type_matches_steps(cls, v, info):
        """Validate that plan_type matches the number of steps."""
        if "total_steps" in info.data:
            if v == "single_step" and info.data["total_steps"] != 1:
                raise ValueError("single_step plan must have exactly 1 step")
            if v == "multi_step" and info.data["total_steps"] < 2:
                raise ValueError("multi_step plan must have at least 2 steps")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "plan_type": "multi_step",
                "reasoning": "User wants documents in folder 'Tax Documents' but documents only store parent folder ID. Need to resolve folder name to ID first.",
                "total_steps": 2,
                "steps": [
                    {
                        "step": 1,
                        "description": "Find the folder with name 'Tax Documents' to get its folder ID"
                    },
                    {
                        "step": 2,
                        "description": "Find all documents where the parent folder ID matches the ID from step 1",
                        "depends_on_step": 1
                    }
                ]
            }
        }


class StepResult(BaseModel):
    """
    Result from executing a single step.

    Stores the complete Elasticsearch document(s) returned from a step,
    along with metadata about the execution.

    Attributes:
        source: Complete Elasticsearch _source document(s)
        metadata: Execution metadata (query, timing, count)

    Example:
        >>> result = StepResult(
        ...     source={
        ...         "systemAttributes": {"id": "abc-123"},
        ...         "commonAttributes": {"name": "Tax Documents"},
        ...         "entityType": "FOLDER"
        ...     },
        ...     metadata=ExecutionMetadata(
        ...         query={"bool": {"must": [...]}},
        ...         execution_time_ms=150,
        ...         result_count=1
        ...     )
        ... )
    """

    source: Dict[str, Any] | List[Dict[str, Any]] = Field(
        ...,
        description="Complete Elasticsearch _source document(s)"
    )

    metadata: "ExecutionMetadata" = Field(
        ...,
        description="Execution metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "source": {
                    "systemAttributes": {
                        "id": "4d3a2df1-1678-498c-99ee-b55960542d30",
                        "parentId": "root"
                    },
                    "commonAttributes": {
                        "name": "Tax Documents"
                    },
                    "entityType": "FOLDER"
                },
                "metadata": {
                    "query": {"bool": {"must": []}},
                    "execution_time_ms": 150,
                    "result_count": 1
                }
            }
        }


class ExecutionMetadata(BaseModel):
    """
    Metadata about step execution.

    Attributes:
        query: The Elasticsearch query that was executed
        execution_time_ms: Time taken to execute the query in milliseconds
        result_count: Number of results returned

    Example:
        >>> metadata = ExecutionMetadata(
        ...     query={"bool": {"must": [...]}},
        ...     execution_time_ms=150,
        ...     result_count=1
        ... )
    """

    query: Dict[str, Any] = Field(
        ...,
        description="The Elasticsearch query that was executed"
    )

    execution_time_ms: int = Field(
        ...,
        ge=0,
        description="Execution time in milliseconds"
    )

    result_count: int = Field(
        ...,
        ge=0,
        description="Number of results returned"
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this step was executed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"entityType.keyword": "FOLDER"}},
                            {"term": {"commonAttributes.name.keyword": "Tax Documents"}}
                        ]
                    }
                },
                "execution_time_ms": 150,
                "result_count": 1,
                "timestamp": "2025-01-15T10:30:00"
            }
        }


class ClarificationOption(BaseModel):
    """
    A single option in a multiple-choice clarification.

    Attributes:
        number: Option number (1-indexed)
        display: User-friendly display text
        value: The actual value to use if selected (typically full ES document)
    """

    number: int = Field(..., ge=1, description="Option number (1-indexed)")
    display: str = Field(..., min_length=1, description="User-friendly display text")
    value: Dict[str, Any] = Field(..., description="Full ES document for this option")


class ClarificationRequest(BaseModel):
    """
    Request for user clarification when query is ambiguous.

    Triggered when a step returns multiple results but only one is expected
    (e.g., multiple folders with the same name in step 1 of a multi-step query).

    Attributes:
        type: Type of clarification needed
        question: Question to ask the user
        options: List of options to choose from

    Example:
        >>> clarification = ClarificationRequest(
        ...     type="multiple_choice",
        ...     question="I found 3 folders named 'Tax'. Which one would you like?",
        ...     options=[
        ...         ClarificationOption(
        ...             number=1,
        ...             display="/root/Personal/Tax",
        ...             value={...}  # Full ES document
        ...         ),
        ...         ClarificationOption(
        ...             number=2,
        ...             display="/root/Business/Tax",
        ...             value={...}
        ...         )
        ...     ]
        ... )
    """

    type: Literal["multiple_choice", "free_text"] = Field(
        ...,
        description="Type of clarification needed"
    )

    question: str = Field(
        ...,
        min_length=10,
        description="Question to ask the user"
    )

    options: Optional[List[ClarificationOption]] = Field(
        default=None,
        description="List of options for multiple_choice type"
    )

    @field_validator("options")
    @classmethod
    def validate_options(cls, v, info):
        """Validate that multiple_choice has options."""
        if "type" in info.data:
            if info.data["type"] == "multiple_choice" and not v:
                raise ValueError("multiple_choice clarification must have options")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "multiple_choice",
                "question": "I found 3 folders named 'Tax Documents'. Which one would you like?",
                "options": [
                    {
                        "number": 1,
                        "display": "/root/Personal/Tax Documents",
                        "value": {"systemAttributes": {"id": "abc-123"}}
                    },
                    {
                        "number": 2,
                        "display": "/root/Business/Tax Documents",
                        "value": {"systemAttributes": {"id": "def-456"}}
                    }
                ]
            }
        }


# Update forward references
StepResult.model_rebuild()
