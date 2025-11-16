"""
Query Executor Node for the search agent LangGraph workflow.

The executor is a loop node that executes query plans step-by-step, handling:
- ES query generation for each step
- Query validation
- Query execution via ES service
- Result analysis
- Human-in-the-loop clarifications
- Result storage
- Multi-step looping
"""

import json
import logging
import time
from typing import Dict, Any, List, Tuple, Optional

from search_agent.core.state import SearchAgentState
from search_agent.core.models import StepResult
from search_agent.services.llm_service import get_llm_service
from search_agent.services.elasticsearch_service import get_elasticsearch_service
from search_agent.prompts.executor_prompt import build_executor_prompt
from search_agent.utils.validation import (
    validate_elasticsearch_query,
    format_folder_for_display,
    format_document_for_display
)

# Set up logging
logger = logging.getLogger(__name__)


def query_executor_node(state: SearchAgentState) -> SearchAgentState:
    """
    Execute the query plan step-by-step (loop node).

    This node performs all operations for the current step:
    1. Generate ES query from step description
    2. Validate the query
    3. Execute against ES service
    4. Analyze results
    5. Handle clarifications if needed
    6. Store results
    7. Loop back for next step or proceed to formatter

    Args:
        state: Current state with query_plan, current_step, etc.

    Returns:
        Updated state with step_results, final_results, or pending_clarification

    Example:
        >>> state = {
        ...     "query_plan": {"steps": [...]},
        ...     "current_step": 1,
        ...     "total_steps": 2,
        ...     "user_query": "List documents in Tax folder"
        ... }
        >>> updated_state = query_executor_node(state)
    """
    logger.info(f"Executing step {state['current_step']} of {state['total_steps']}")

    # Get current step details
    current_step_num = state["current_step"]
    query_plan = state["query_plan"]
    step = query_plan["steps"][current_step_num - 1]  # 0-indexed list

    # Initialize retry_count if not present
    if "retry_count" not in state:
        state["retry_count"] = 0

    # Initialize step_results if not present
    if "step_results" not in state:
        state["step_results"] = {}

    # Operation 1: Generate ES Query
    logger.debug(f"Generating ES query for step {current_step_num}: {step['description']}")

    try:
        es_query, validation_errors = _generate_and_validate_query(
            step=step,
            user_query=state["user_query"],
            current_step=current_step_num,
            total_steps=state["total_steps"],
            step_results=state.get("step_results", {}),
            retry_count=state.get("retry_count", 0)
        )
    except Exception as e:
        logger.error(f"Failed to generate query: {e}")
        return {
            **state,
            "error": f"Failed to generate query for step {current_step_num}: {str(e)}"
        }

    # If validation failed and we haven't exceeded retries, retry
    if validation_errors:
        if state["retry_count"] < 3:
            logger.warning(f"Query validation failed (attempt {state['retry_count'] + 1}/3): {validation_errors}")
            return {
                **state,
                "retry_count": state["retry_count"] + 1,
                "validation_feedback": validation_errors
            }
        else:
            logger.error(f"Max retries exceeded for query validation")
            return {
                **state,
                "error": f"Could not generate valid query after 3 attempts. Errors: {'; '.join(validation_errors)}"
            }

    # Reset retry count after successful generation
    state["retry_count"] = 0

    # Operation 3: Execute Query
    logger.debug(f"Executing query: {json.dumps(es_query, indent=2)}")

    try:
        result, execution_time_ms = _execute_query(es_query)
    except Exception as e:
        logger.error(f"Query execution failed: {e}")

        # Retry logic for execution errors
        if state.get("execution_retry_count", 0) < 2:
            retry_count = state.get("execution_retry_count", 0) + 1
            delay = 2 ** retry_count  # Exponential backoff
            logger.info(f"Retrying execution after {delay}s (attempt {retry_count}/2)")
            time.sleep(delay)
            return {
                **state,
                "execution_retry_count": retry_count
            }
        else:
            return {
                **state,
                "error": f"Service unavailable after retries: {str(e)}"
            }

    # Reset execution retry count
    if "execution_retry_count" in state:
        state["execution_retry_count"] = 0

    # Operation 4: Analyze Result
    result_type, result_data, clarification = _analyze_result(
        result=result,
        current_step=current_step_num,
        total_steps=state["total_steps"],
        step_description=step["description"]
    )

    logger.info(f"Result analysis: {result_type}, count={_get_result_count(result)}")

    # Operation 5: Handle Clarification (if needed)
    if result_type == "needs_clarification":
        logger.info("Multiple results found, requesting user clarification")
        return {
            **state,
            "pending_clarification": clarification
        }

    # Handle critical errors (empty results in intermediate steps)
    if result_type == "critical_error":
        logger.error(f"Critical error: {result_data}")
        return {
            **state,
            "error": result_data
        }

    # Operation 6: Store Results
    step_result = StepResult(
        step=current_step_num,
        query=es_query,
        result=result_data,
        execution_time_ms=execution_time_ms,
        result_count=_get_result_count(result)
    )

    state["step_results"][current_step_num] = step_result.model_dump()

    # Operation 7: Loop Decision
    if state["current_step"] < state["total_steps"]:
        # More steps to execute
        logger.info(f"Proceeding to step {state['current_step'] + 1}")
        return {
            **state,
            "current_step": state["current_step"] + 1
        }
    else:
        # All steps complete
        logger.info("All steps complete, setting final results")

        # Final results are from the last step
        final_step_result = state["step_results"][state["total_steps"]]

        return {
            **state,
            "final_results": final_step_result["result"]
        }


def _generate_and_validate_query(
    step: Dict[str, Any],
    user_query: str,
    current_step: int,
    total_steps: int,
    step_results: Dict[int, Dict],
    retry_count: int
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Generate and validate an ES query for the current step.

    Args:
        step: Step description from query plan
        user_query: Original user query
        current_step: Current step number
        total_steps: Total steps in plan
        step_results: Results from previous steps
        retry_count: Current retry attempt

    Returns:
        Tuple of (es_query, validation_errors)
        validation_errors is empty list if valid

    Raises:
        Exception: If query generation fails
    """
    # Get previous step result if this step depends on it
    previous_result = None
    depends_on = step.get("depends_on_step")

    if depends_on is not None and depends_on in step_results:
        # Get the result from the previous step
        prev_step_data = step_results[depends_on]
        if "result" in prev_step_data:
            previous_result = prev_step_data["result"]

    # Build executor prompt
    prompt = build_executor_prompt(
        step_description=step["description"],
        user_query=user_query,
        current_step=current_step,
        total_steps=total_steps,
        previous_step_result=previous_result,
        depends_on_step=depends_on
    )

    # Call LLM to generate query
    llm = get_llm_service()

    try:
        response_json = llm.call_with_json_response(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.0
        )
    except json.JSONDecodeError as e:
        raise Exception(f"LLM returned invalid JSON: {str(e)}")

    # Check if LLM returned an error
    if "error" in response_json:
        error_type = response_json.get("error")
        error_msg = response_json.get("message", "Unknown error")
        raise Exception(f"LLM returned error ({error_type}): {error_msg}")

    # Validate the query
    validation_errors = validate_elasticsearch_query(response_json)

    return response_json, validation_errors


def _execute_query(es_query: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Execute an ES query via the ES service.

    Args:
        es_query: Elasticsearch DSL query

    Returns:
        Tuple of (result, execution_time_ms)

    Raises:
        Exception: If execution fails
    """
    es_service = get_elasticsearch_service()

    start_time = time.time()
    result = es_service.search(es_query)
    execution_time = int((time.time() - start_time) * 1000)

    return result, execution_time


def _analyze_result(
    result: Dict[str, Any],
    current_step: int,
    total_steps: int,
    step_description: str
) -> Tuple[str, Any, Optional[Dict]]:
    """
    Analyze query execution result and determine next action.

    Args:
        result: ES query result
        current_step: Current step number
        total_steps: Total steps in plan
        step_description: Description of what this step should do

    Returns:
        Tuple of (result_type, result_data, clarification)
        - result_type: "success", "critical_error", "needs_clarification", "empty_result"
        - result_data: The actual data or error message
        - clarification: Clarification request dict (if needed) or None

    Example:
        >>> result_type, data, clarif = _analyze_result(
        ...     result={"hits": {"total": {"value": 1}, "hits": [...]}},
        ...     current_step=1,
        ...     total_steps=2,
        ...     step_description="Find folder"
        ... )
        >>> result_type
        'success'
    """
    count = result["hits"]["total"]["value"]
    hits = result["hits"]["hits"]

    # Empty result
    if count == 0:
        if current_step < total_steps:
            # Critical: cannot proceed to next step
            return "critical_error", "Cannot proceed: Entity not found for intermediate step", None
        else:
            # Empty result on final step is acceptable
            return "empty_result", [], None

    # Single result
    elif count == 1:
        return "success", hits[0]["_source"], None

    # Multiple results
    elif count > 1:
        if current_step < total_steps:
            # Need clarification - which one to use for next step?
            clarification = _create_clarification(hits, step_description)
            return "needs_clarification", None, clarification
        else:
            # Multiple results OK for final step
            return "success", [hit["_source"] for hit in hits], None

    return "success", None, None


def _create_clarification(
    hits: List[Dict[str, Any]],
    step_description: str
) -> Dict[str, Any]:
    """
    Create a clarification request for user.

    Args:
        hits: List of ES hits (multiple results)
        step_description: Description of the step

    Returns:
        Clarification request dictionary

    Example:
        >>> clarification = _create_clarification(
        ...     hits=[{"_source": {"commonAttributes": {"name": "Tax"}}}],
        ...     step_description="Find folder named Tax"
        ... )
        >>> clarification["type"]
        'multiple_choice'
    """
    # Extract entity type from first hit
    entity_type = hits[0]["_source"].get("entityType", "entity")
    count = len(hits)

    # Create clarification message
    clarification = {
        "type": "multiple_choice",
        "question": f"I found {count} {entity_type.lower()}s matching '{step_description}'. Which one would you like?",
        "options": []
    }

    # Add each result as an option
    for idx, hit in enumerate(hits, 1):
        source = hit["_source"]

        # Format display based on entity type
        if entity_type == "FOLDER":
            display = format_folder_for_display(source)
        elif entity_type == "DOCUMENT":
            display = format_document_for_display(source)
        else:
            # Generic display
            name = source.get("commonAttributes", {}).get("name", "Unknown")
            display = f"{entity_type}: {name}"

        clarification["options"].append({
            "number": idx,
            "display": display,
            "value": source  # Store full document for later use
        })

    return clarification


def _get_result_count(result: Dict[str, Any]) -> int:
    """
    Get the count of results from an ES result.

    Args:
        result: Elasticsearch result

    Returns:
        Number of results
    """
    return result.get("hits", {}).get("total", {}).get("value", 0)


if __name__ == "__main__":
    # Test the executor node
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test state
    from search_agent.core.models import QueryPlan, Step

    plan = QueryPlan(
        plan_type="single_step",
        reasoning="Test plan for single-step execution",
        total_steps=1,
        steps=[
            Step(step=1, description="Find all documents where document type is W2")
        ]
    )

    state: SearchAgentState = {
        "user_query": "Find all W2 documents",
        "query_plan": plan.model_dump(),
        "total_steps": 1,
        "current_step": 1,
        "conversation_id": "test-exec",
        "conversation_history": [],
    }

    print("\n" + "=" * 70)
    print(f"Testing executor with query: {state['user_query']}")
    print("=" * 70)

    result = query_executor_node(state)

    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
    elif "pending_clarification" in result:
        print(f"\n❓ Clarification needed:")
        print(json.dumps(result["pending_clarification"], indent=2))
    elif "final_results" in result:
        print(f"\n✓ Execution complete!")
        print(f"Final results count: {len(result['final_results']) if isinstance(result['final_results'], list) else 1}")
    else:
        print(f"\n→ Step {result['current_step']} complete, continuing...")
