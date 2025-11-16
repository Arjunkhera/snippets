"""
Query Planner Node for the search agent LangGraph workflow.

The planner analyzes natural language queries and determines whether they
require single-step or multi-step execution by performing gap analysis.
"""

import json
import logging
from typing import Dict, Any

from pydantic import ValidationError

from search_agent.core.state import SearchAgentState
from search_agent.core.models import QueryPlan, Step
from search_agent.services.llm_service import get_llm_service
from search_agent.prompts.planner_prompt import build_planner_prompt

# Set up logging
logger = logging.getLogger(__name__)


def query_planner_node(state: SearchAgentState) -> SearchAgentState:
    """
    Analyze query and create execution plan.

    This node performs gap analysis to determine if the user's query can be
    answered with a single Elasticsearch query or requires multiple sequential
    queries to resolve missing information (e.g., folder name to ID resolution).

    Args:
        state: Current state with user_query and intent

    Returns:
        Updated state with query_plan, total_steps, and current_step

    Raises:
        Exception: If planning fails after retries

    Example:
        >>> state = {
        ...     "user_query": "List documents in Tax Documents folder",
        ...     "intent": "search",
        ...     "conversation_id": "conv-123"
        ... }
        >>> updated_state = query_planner_node(state)
        >>> print(updated_state["query_plan"]["plan_type"])
        'multi_step'
    """
    logger.info(f"Planning query: {state['user_query']}")

    # Build the planner prompt
    try:
        prompt = build_planner_prompt(state["user_query"])
    except Exception as e:
        logger.error(f"Failed to build planner prompt: {e}")
        return {
            **state,
            "error": f"Failed to build planner prompt: {str(e)}"
        }

    # Get LLM service
    llm = get_llm_service()

    # Try to get a valid plan from the LLM
    max_attempts = 3
    last_error = None

    for attempt in range(max_attempts):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_attempts} to generate plan")

            # Call LLM to generate plan
            response_json = llm.call_with_json_response(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.0
            )

            logger.debug(f"LLM response: {json.dumps(response_json, indent=2)}")

            # Parse response into QueryPlan model
            # The Pydantic model will validate the structure
            query_plan = QueryPlan(**response_json)

            logger.info(
                f"Generated {query_plan.plan_type} plan with "
                f"{query_plan.total_steps} step(s)"
            )

            # Update state with the plan
            return {
                **state,
                "query_plan": query_plan.model_dump(),
                "total_steps": query_plan.total_steps,
                "current_step": 1,  # Initialize to first step
            }

        except ValidationError as e:
            # Pydantic validation failed
            last_error = e
            logger.warning(
                f"Plan validation failed (attempt {attempt + 1}/{max_attempts}): {e}"
            )

            # If we have more attempts, add validation errors to the prompt
            if attempt < max_attempts - 1:
                # Extract validation errors
                error_messages = []
                for error in e.errors():
                    field = " -> ".join(str(x) for x in error["loc"])
                    message = error["msg"]
                    error_messages.append(f"- {field}: {message}")

                # Add error feedback to prompt for retry
                error_feedback = "\n".join(error_messages)
                prompt += f"""

# PREVIOUS ATTEMPT FAILED

Your previous response had validation errors:
{error_feedback}

Please fix these errors and generate a valid plan.
"""
                continue
            else:
                # Max attempts exceeded
                logger.error(f"Failed to generate valid plan after {max_attempts} attempts")
                return {
                    **state,
                    "error": f"Failed to generate valid query plan: {str(last_error)}"
                }

        except json.JSONDecodeError as e:
            # LLM didn't return valid JSON
            last_error = e
            logger.warning(
                f"Failed to parse LLM response as JSON (attempt {attempt + 1}/{max_attempts}): {e}"
            )

            # If we have more attempts, add feedback
            if attempt < max_attempts - 1:
                prompt += """

# PREVIOUS ATTEMPT FAILED

Your previous response was not valid JSON.
Please ensure you return ONLY valid JSON with no markdown code blocks or additional text.

Example format:
{
  "plan_type": "single_step",
  "reasoning": "...",
  "total_steps": 1,
  "steps": [...]
}
"""
                continue
            else:
                logger.error(f"LLM failed to return valid JSON after {max_attempts} attempts")
                return {
                    **state,
                    "error": f"Failed to parse plan from LLM response: {str(last_error)}"
                }

        except Exception as e:
            # Other errors (API failures, etc.)
            last_error = e
            logger.error(f"Unexpected error during planning: {e}")

            if attempt < max_attempts - 1:
                # Retry for transient errors
                continue
            else:
                return {
                    **state,
                    "error": f"Planning failed: {str(last_error)}"
                }

    # Should not reach here, but handle just in case
    return {
        **state,
        "error": f"Planning failed after {max_attempts} attempts: {str(last_error)}"
    }


def validate_plan_dependencies(plan: QueryPlan) -> list[str]:
    """
    Validate that step dependencies are valid.

    Args:
        plan: Query plan to validate

    Returns:
        List of validation error messages (empty if valid)

    Example:
        >>> plan = QueryPlan(
        ...     plan_type="multi_step",
        ...     reasoning="Test",
        ...     total_steps=2,
        ...     steps=[
        ...         Step(step=1, description="Find folder"),
        ...         Step(step=2, description="Find docs", depends_on_step=1)
        ...     ]
        ... )
        >>> errors = validate_plan_dependencies(plan)
        >>> len(errors)
        0
    """
    errors = []

    # Check that all referenced step numbers exist
    step_numbers = {step.step for step in plan.steps}

    for step in plan.steps:
        if step.depends_on_step is not None:
            if step.depends_on_step not in step_numbers:
                errors.append(
                    f"Step {step.step} depends on non-existent step {step.depends_on_step}"
                )

            # Already validated by Pydantic: depends_on_step < step
            # But let's be explicit
            if step.depends_on_step >= step.step:
                errors.append(
                    f"Step {step.step} cannot depend on step {step.depends_on_step} "
                    f"(must depend on earlier step)"
                )

    # Validate plan_type matches step count
    if plan.plan_type == "single_step" and plan.total_steps != 1:
        errors.append(
            f"Plan type is 'single_step' but total_steps is {plan.total_steps}"
        )

    if plan.plan_type == "multi_step" and plan.total_steps < 2:
        errors.append(
            f"Plan type is 'multi_step' but total_steps is {plan.total_steps} (must be >= 2)"
        )

    return errors


if __name__ == "__main__":
    # Test the planner node
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test queries
    test_queries = [
        "Find all W2 documents",  # Should be single-step
        "List documents in Tax Documents folder",  # Should be multi-step
        "Show folders at root level",  # Should be single-step
    ]

    for query in test_queries:
        print("\n" + "=" * 70)
        print(f"Testing query: {query}")
        print("=" * 70)

        state: SearchAgentState = {
            "user_query": query,
            "intent": "search",
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        result = query_planner_node(state)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            plan = result.get("query_plan")
            print(f"✓ Plan type: {plan['plan_type']}")
            print(f"✓ Total steps: {plan['total_steps']}")
            print(f"✓ Reasoning: {plan['reasoning']}")
            print("\nSteps:")
            for step in plan['steps']:
                depends = f" (depends on step {step['depends_on_step']})" if step.get('depends_on_step') else ""
                print(f"  {step['step']}. {step['description']}{depends}")
