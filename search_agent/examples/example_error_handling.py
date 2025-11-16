"""
Comprehensive Error Handling Examples.

This demonstrates all error handling scenarios in the search agent:
1. Validation errors with retry logic
2. Execution errors with exponential backoff
3. Critical errors that cannot be recovered
4. Service unavailability
5. LLM response errors

Each scenario shows how the agent gracefully handles and recovers from errors.
"""

import logging
from unittest.mock import Mock, patch

from search_agent.graph import create_search_agent_graph
from search_agent.core.state import SearchAgentState

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demonstrate_validation_error_retry():
    """
    Scenario 1: Validation Error with Retry

    The executor generates an invalid ES query (e.g., wrong field name).
    The validator catches it and provides feedback.
    The executor retries with the feedback, generating a valid query.
    """
    print("\n" + "=" * 80)
    print("SCENARIO 1: Validation Error with Retry")
    print("=" * 80)

    print("""
Flow:
1. Executor generates ES query
2. Validator detects invalid field: "document_type.keyword" (should be "commonAttributes.documentType.keyword")
3. Validation feedback added to state
4. Executor regenerates query with feedback
5. New query passes validation
6. Query executes successfully

Error Handling:
- MAX_RETRIES: 3 attempts
- Feedback loop: Validation errors sent back to LLM
- Graceful degradation: After 3 failures, returns error to formatter

Expected Outcome:
✓ Query regenerated successfully
✓ Valid query executed
✓ Results returned to user
""")


def demonstrate_execution_error_retry():
    """
    Scenario 2: Execution Error with Exponential Backoff

    The ES service is temporarily unavailable (500 error).
    The executor retries with exponential backoff: 2s, 4s.
    After retry, service is available and query succeeds.
    """
    print("\n" + "=" * 80)
    print("SCENARIO 2: Execution Error with Exponential Backoff")
    print("=" * 80)

    print("""
Flow:
1. Executor generates valid ES query
2. ES service returns 500 error (service unavailable)
3. Executor waits 2 seconds (first retry delay)
4. Executor retries query
5. ES service still unavailable
6. Executor waits 4 seconds (second retry delay)
7. Executor retries query
8. ES service responds successfully

Error Handling:
- MAX_EXECUTION_RETRIES: 2 attempts
- Exponential backoff: 2^retry_count seconds
- Retry delays: [2s, 4s]
- After 2 failures: Return error to formatter

Expected Outcome:
✓ Query retried with backoff
✓ Service recovered
✓ Results returned successfully
""")


def demonstrate_critical_error():
    """
    Scenario 3: Critical Error - Cannot Proceed

    Multi-step query: Step 1 returns 0 results.
    Step 2 depends on Step 1 result (folder ID).
    Cannot proceed without Step 1 result.
    This is a critical error that cannot be recovered.
    """
    print("\n" + "=" * 80)
    print("SCENARIO 3: Critical Error - Cannot Proceed")
    print("=" * 80)

    print("""
Flow:
1. User Query: "List documents in NonExistent folder"
2. Planner creates 2-step plan:
   - Step 1: Find folder named "NonExistent"
   - Step 2: Find documents in that folder
3. Executor executes Step 1
4. ES returns 0 results (folder doesn't exist)
5. Analyzer detects: intermediate step returned 0 results
6. Critical error: "Cannot proceed: Entity not found for intermediate step"
7. Execution stops, error sent to formatter

Error Handling:
- Empty result detection
- Step dependency analysis
- Critical vs. acceptable empty results
  * Critical: Empty result in intermediate step
  * Acceptable: Empty result in final step

Expected Outcome:
✗ Step 1 returns no results
✗ Cannot proceed to Step 2
✓ User-friendly error message from formatter
    "I couldn't find the folder or document you referenced. Please check the name and try again."
""")


def demonstrate_max_retries_exceeded():
    """
    Scenario 4: Max Retries Exceeded

    The LLM consistently generates invalid queries.
    After 3 attempts, the system gives up.
    """
    print("\n" + "=" * 80)
    print("SCENARIO 4: Max Retries Exceeded")
    print("=" * 80)

    print("""
Flow:
1. Executor generates ES query
2. Validator finds errors: ["Query must contain entityType filter"]
3. Retry 1: Regenerate with feedback
4. Validator still finds errors
5. Retry 2: Regenerate with feedback
6. Validator still finds errors
7. Retry 3: Regenerate with feedback
8. Validator still finds errors
9. MAX_RETRIES exceeded (3 attempts)
10. Return error to formatter

Error Handling:
- Retry counter tracked in state
- Feedback provided on each retry
- Hard limit: 3 attempts maximum
- Graceful failure: Error message to user

Expected Outcome:
✗ Query generation failed after 3 attempts
✓ Clear error message to user
    "I had trouble understanding your search request. Could you rephrase it?"
""")


def demonstrate_service_unavailable():
    """
    Scenario 5: Service Permanently Unavailable

    ES service is down and doesn't recover within retry window.
    """
    print("\n" + "=" * 80)
    print("SCENARIO 5: Service Permanently Unavailable")
    print("=" * 80)

    print("""
Flow:
1. Executor generates valid ES query
2. ES service call fails (connection error)
3. Wait 2 seconds, retry
4. ES service call fails again
5. Wait 4 seconds, retry
6. ES service call fails again
7. Max execution retries exceeded (2 attempts)
8. Return service unavailable error

Error Handling:
- Network error detection
- Exponential backoff retry
- Retry limit enforcement
- Service health status

Expected Outcome:
✗ Service unavailable after retries
✓ User-friendly error message
    "I'm having trouble reaching the search service. Please try again in a moment."
""")


def demonstrate_llm_error_handling():
    """
    Scenario 6: LLM Response Errors

    Various LLM-related errors and how they're handled.
    """
    print("\n" + "=" * 80)
    print("SCENARIO 6: LLM Response Errors")
    print("=" * 80)

    print("""
Possible LLM Errors:
1. Invalid JSON response
2. Missing required fields
3. Timeout
4. API error (rate limit, auth error)

Example - Classifier Invalid JSON:
Flow:
1. Classifier calls LLM for intent classification
2. LLM returns invalid JSON: {"intent": "search"}  (missing confidence, reasoning)
3. Validation catches missing fields
4. Retry with same prompt
5. LLM returns valid JSON
6. Classification succeeds

Error Handling:
- JSON validation before processing
- Field presence validation
- Retry logic (max 2 attempts for classifier)
- Default fallback: intent="other", confidence="low"

Example - Planner Timeout:
Flow:
1. Planner calls LLM for query plan
2. LLM request times out (60 seconds)
3. Timeout exception caught
4. Retry once
5. If still fails: Return error to formatter

Expected Outcomes:
✓ Most JSON errors recoverable via retry
✓ Timeouts handled with retry
✓ API errors propagated with clear messages
✗ After max retries: Graceful degradation
""")


def show_error_state_transitions():
    """
    Show how errors affect state transitions in the graph.
    """
    print("\n" + "=" * 80)
    print("Error State Transitions")
    print("=" * 80)

    print("""
Normal Flow:
Classifier -> Planner -> Executor -> Formatter -> END

With Validation Error (Recoverable):
Classifier -> Planner -> Executor (attempt 1) -> Executor (attempt 2) -> Formatter -> END
                           └─ retry_count=1 ──┘

With Critical Error (Non-Recoverable):
Classifier -> Planner -> Executor (Step 1: 0 results) -> Formatter (error) -> END
                           └─ error="Cannot proceed" ──┘

With Service Error (Retry):
Classifier -> Planner -> Executor (503 error) -> Executor (retry) -> Formatter -> END
                           └─ execution_retry_count=1 ──┘

State Fields for Error Handling:
- retry_count: Validation error retry counter (max 3)
- execution_retry_count: Execution error retry counter (max 2)
- validation_feedback: Errors from validator (sent to LLM)
- error: Fatal error message (terminates execution)
- pending_clarification: HITL clarification (interrupts execution)

Routing Based on Errors:
route_after_executor(state):
    if state.get("error"):
        return "formatter"  # Fatal error, stop execution
    if state.get("pending_clarification"):
        return "executor"  # HITL interrupt, wait for user
    if state["current_step"] < state["total_steps"]:
        return "executor"  # More steps, continue
    return "formatter"  # All done
""")


def main():
    """
    Run all error handling demonstrations.
    """
    print("\n" + "█" * 80)
    print("Comprehensive Error Handling Guide")
    print("█" * 80)

    # Demonstrate all error scenarios
    demonstrate_validation_error_retry()
    demonstrate_execution_error_retry()
    demonstrate_critical_error()
    demonstrate_max_retries_exceeded()
    demonstrate_service_unavailable()
    demonstrate_llm_error_handling()
    show_error_state_transitions()

    print("\n" + "█" * 80)
    print("Error Handling Summary")
    print("█" * 80)

    print("""
Implemented Error Handling:

1. Validation Errors (Recoverable)
   - Detection: Query validator checks ES syntax
   - Recovery: Retry with feedback to LLM (max 3 attempts)
   - Fallback: Error message to user

2. Execution Errors (Recoverable)
   - Detection: ES service call failures
   - Recovery: Exponential backoff retry (2s, 4s)
   - Fallback: Service unavailable error

3. Critical Errors (Non-Recoverable)
   - Detection: Empty intermediate step results
   - Recovery: None (cannot proceed)
   - Fallback: Clear error message explaining issue

4. LLM Errors (Recoverable)
   - Detection: JSON validation, field validation
   - Recovery: Retry LLM call
   - Fallback: Default values or error message

5. Timeout Errors
   - Detection: Request timeout exceptions
   - Recovery: Retry once
   - Fallback: Timeout error message

Error Handling Best Practices:
✓ Clear error messages for users
✓ Graceful degradation (try multiple strategies)
✓ Retry with intelligent backoff
✓ Feedback loops (validation errors to LLM)
✓ Hard limits on retries (prevent infinite loops)
✓ State preservation (retry counts in state)
✓ Comprehensive logging for debugging

Next Steps:
- Monitor error rates in production
- Add alerting for high error rates
- Collect error patterns for LLM fine-tuning
- Implement circuit breaker for service failures
- Add error analytics dashboard
""")


if __name__ == "__main__":
    main()
