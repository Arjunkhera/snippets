"""
Query Classifier Node for the search agent LangGraph workflow.

The classifier analyzes user intent and routes to appropriate handlers:
- "search" -> Query Planner (implemented)
- "move" -> Move handler (future)
- "delete" -> Delete handler (future)
- "create" -> Create handler (future)
- "other" -> End with help message
"""

import json
import logging
from typing import Dict, Any

from search_agent.core.state import SearchAgentState
from search_agent.services.llm_service import get_llm_service

# Set up logging
logger = logging.getLogger(__name__)


def query_classifier_node(state: SearchAgentState) -> SearchAgentState:
    """
    Classify user intent from natural language query.

    Determines whether the query is a search/list operation or
    a different type of operation (move, delete, create, etc.).

    Args:
        state: Current state with user_query and conversation_history

    Returns:
        Updated state with intent, classification_confidence, and classification_reasoning

    Example:
        >>> state = {
        ...     "user_query": "Find all W2 documents",
        ...     "conversation_history": [],
        ...     "conversation_id": "test-123"
        ... }
        >>> result = query_classifier_node(state)
        >>> result["intent"]
        'search'
    """
    logger.info(f"Classifying query: {state['user_query']}")

    # Build classification prompt
    prompt = _build_classifier_prompt(
        user_query=state["user_query"],
        conversation_history=state.get("conversation_history", [])
    )

    # Call LLM with retry logic
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            llm = get_llm_service()
            response_json = llm.call_with_json_response(
                prompt=prompt,
                max_tokens=500,
                temperature=0.0
            )

            # Validate response structure
            _validate_classification_response(response_json)

            # Success - update state
            logger.info(f"Classification: {response_json['intent']} (confidence: {response_json['confidence']})")

            return {
                **state,
                "intent": response_json["intent"],
                "classification_confidence": response_json["confidence"],
                "classification_reasoning": response_json["reasoning"]
            }

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Classification attempt {attempt + 1} failed: {e}")
            if attempt == max_attempts - 1:
                # Final attempt failed, default to "other"
                logger.error("Max classification attempts exceeded, defaulting to 'other'")
                return {
                    **state,
                    "intent": "other",
                    "classification_confidence": "low",
                    "classification_reasoning": f"Could not classify query: {str(e)}"
                }

    # Should not reach here, but handle it
    return {
        **state,
        "intent": "other",
        "classification_confidence": "low",
        "classification_reasoning": "Classification failed"
    }


def _build_classifier_prompt(user_query: str, conversation_history: list) -> str:
    """
    Build the classification prompt for the LLM.

    Args:
        user_query: User's natural language query
        conversation_history: Previous conversation messages

    Returns:
        Complete formatted prompt
    """
    # Format conversation history
    history_text = "None"
    if conversation_history:
        history_lines = []
        for msg in conversation_history[-5:]:  # Last 5 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")
        history_text = "\n".join(history_lines)

    prompt = f"""You are analyzing user queries for a document management system (similar to Google Drive).

Your task: Determine the user's intent.

INTENT CATEGORIES:

1. "search" - User wants to find/view/list existing documents or folders
   Keywords: find, show, list, get, search, display, where, which, what
   Examples:
   - "Show me all W2 documents"
   - "List folders in Business directory"
   - "Find documents created last week"
   - "Which folder contains invoice.pdf?"

2. "move" - User wants to relocate documents or folders
   Keywords: move, relocate, transfer
   Examples:
   - "Move document X to folder Y"
   - "Relocate all receipts to Archive"

3. "delete" - User wants to remove documents or folders
   Keywords: delete, remove, trash
   Examples:
   - "Delete old tax documents"
   - "Remove duplicate files"

4. "create" - User wants to create new folders or upload documents
   Keywords: create, add, upload, new
   Examples:
   - "Create a folder called Projects"
   - "Add a new document"

5. "other" - Queries about system capabilities, help, or unclear intent
   Examples:
   - "How does the system work?"
   - "What can I do here?"

CONTEXT:
Previous conversation: {history_text}

USER QUERY:
{user_query}

Respond with JSON:
{{
  "intent": "search" | "move" | "delete" | "create" | "other",
  "confidence": "high" | "medium" | "low",
  "reasoning": "Brief explanation of why you chose this intent"
}}

Return ONLY valid JSON with no additional text."""

    return prompt


def _validate_classification_response(response: Dict[str, Any]) -> None:
    """
    Validate the classification response from LLM.

    Args:
        response: JSON response from LLM

    Raises:
        ValueError: If response is invalid
    """
    # Check required fields
    required_fields = ["intent", "confidence", "reasoning"]
    for field in required_fields:
        if field not in response:
            raise ValueError(f"Missing required field: {field}")

    # Validate intent
    valid_intents = ["search", "move", "delete", "create", "other"]
    if response["intent"] not in valid_intents:
        raise ValueError(f"Invalid intent: {response['intent']}. Must be one of {valid_intents}")

    # Validate confidence
    valid_confidences = ["high", "medium", "low"]
    if response["confidence"] not in valid_confidences:
        raise ValueError(f"Invalid confidence: {response['confidence']}. Must be one of {valid_confidences}")

    # Validate reasoning (should be meaningful)
    if not response["reasoning"] or len(response["reasoning"].strip()) < 10:
        raise ValueError("Reasoning must be at least 10 characters")


if __name__ == "__main__":
    # Test the classifier node
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_queries = [
        "Find all W2 documents",
        "Move invoice.pdf to Archive folder",
        "Delete old receipts from 2020",
        "Create a new folder called Projects",
        "How does this system work?"
    ]

    print("\n" + "=" * 70)
    print("Testing Query Classifier")
    print("=" * 70)

    for query in test_queries:
        state: SearchAgentState = {
            "user_query": query,
            "conversation_id": "test-classifier",
            "conversation_history": []
        }

        result = query_classifier_node(state)

        print(f"\nQuery: {query}")
        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['classification_confidence']}")
        print(f"Reasoning: {result['classification_reasoning']}")
        print("-" * 70)
