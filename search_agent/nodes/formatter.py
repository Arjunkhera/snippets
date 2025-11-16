"""
Response Formatter Node for the search agent LangGraph workflow.

The formatter creates user-friendly response messages from execution results,
handling success, empty results, and error cases.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from search_agent.core.state import SearchAgentState

# Set up logging
logger = logging.getLogger(__name__)


def response_formatter_node(state: SearchAgentState) -> SearchAgentState:
    """
    Format final results or errors into user-friendly response.

    Handles:
    - Success cases (single and multi-step)
    - Empty results
    - Error messages
    - Metadata collection

    Args:
        state: Current state with final_results, error, query_plan, etc.

    Returns:
        Updated state with response_message and metadata

    Example:
        >>> state = {
        ...     "final_results": [...],
        ...     "query_plan": {"plan_type": "single_step"},
        ...     "user_query": "Find W2 documents"
        ... }
        >>> result = response_formatter_node(state)
        >>> print(result["response_message"])
    """
    logger.info("Formatting response")

    # Check for errors first
    if state.get("error"):
        return _format_error_response(state)

    # Check for results
    final_results = state.get("final_results")
    if final_results is None:
        return _format_error_response({
            **state,
            "error": "No results available"
        })

    # Format success response
    return _format_success_response(state)


def _format_success_response(state: SearchAgentState) -> SearchAgentState:
    """
    Format successful query execution.

    Args:
        state: Current state with final_results

    Returns:
        Updated state with formatted response_message
    """
    final_results = state["final_results"]
    query_plan = state.get("query_plan", {})
    plan_type = query_plan.get("plan_type", "single_step")

    # Determine result count
    if isinstance(final_results, list):
        count = len(final_results)
        results_list = final_results
    elif isinstance(final_results, dict):
        count = 1
        results_list = [final_results]
    else:
        count = 0
        results_list = []

    # Handle empty results
    if count == 0:
        return _format_empty_response(state)

    # Build success message
    message_parts = []

    # Header
    message_parts.append(f"Found {count} result{'s' if count != 1 else ''}:\n")

    # Format each result
    for idx, result in enumerate(results_list, 1):
        formatted_result = _format_single_result(result, idx)
        message_parts.append(formatted_result)
        message_parts.append("")  # Empty line between results

    # Add multi-step transparency note
    if plan_type == "multi_step" and state.get("step_results"):
        transparency_note = _build_transparency_note(state)
        if transparency_note:
            message_parts.append(transparency_note)

    message = "\n".join(message_parts)

    # Calculate metadata
    metadata = _calculate_metadata(state, count)

    return {
        **state,
        "response_message": message,
        "metadata": metadata
    }


def _format_empty_response(state: SearchAgentState) -> SearchAgentState:
    """
    Format response for empty results.

    Args:
        state: Current state

    Returns:
        Updated state with empty results message
    """
    message = "No documents or folders found matching your criteria.\n\n"
    message += "Suggestions:\n"
    message += "- Try broader search terms\n"
    message += "- Check spelling of folder/document names\n"
    message += "- List all available folders to find the right one"

    metadata = _calculate_metadata(state, 0)

    return {
        **state,
        "response_message": message,
        "metadata": metadata
    }


def _format_error_response(state: SearchAgentState) -> SearchAgentState:
    """
    Format error response with user-friendly messages.

    Args:
        state: Current state with error

    Returns:
        Updated state with error message
    """
    error = state.get("error", "Unknown error")

    # Map common errors to user-friendly messages
    error_messages = {
        "folder_not_found": "I couldn't find a folder with that name. Would you like me to list all your folders?",
        "service_unavailable": "I'm having trouble reaching the search service. Please try again in a moment.",
        "invalid_query": "I had trouble understanding your search request. Could you rephrase it?",
        "Cannot proceed": "I couldn't find the folder or document you referenced. Please check the name and try again.",
    }

    # Try to match error patterns
    user_message = None
    for pattern, friendly_msg in error_messages.items():
        if pattern in error:
            user_message = friendly_msg
            break

    # Default message if no match
    if not user_message:
        user_message = f"An error occurred: {error}"

    metadata = _calculate_metadata(state, 0)
    metadata["error"] = error

    return {
        **state,
        "response_message": user_message,
        "metadata": metadata
    }


def _format_single_result(result: Dict[str, Any], index: int) -> str:
    """
    Format a single result (document or folder) for display.

    Args:
        result: ES document _source
        index: Result number (1-indexed)

    Returns:
        Formatted string representation
    """
    entity_type = result.get("entityType", "UNKNOWN")
    common_attrs = result.get("commonAttributes", {})
    system_attrs = result.get("systemAttributes", {})
    org_attrs = result.get("organizationAttributes", {})

    if entity_type == "DOCUMENT":
        return _format_document(result, index)
    elif entity_type == "FOLDER":
        return _format_folder(result, index)
    else:
        # Generic formatting
        name = common_attrs.get("name", "Unknown")
        return f"{index}. {entity_type}: {name}"


def _format_document(doc: Dict[str, Any], index: int) -> str:
    """
    Format a document result.

    Args:
        doc: Document source
        index: Result number

    Returns:
        Formatted document string
    """
    common = doc.get("commonAttributes", {})
    system = doc.get("systemAttributes", {})
    org = doc.get("organizationAttributes", {})

    name = common.get("name", "Unnamed Document")
    doc_type = common.get("documentType", "Unknown")
    folder_path = org.get("folderPath", "Unknown")
    create_date = system.get("createDate", "")
    size_bytes = common.get("size", 0)

    # Format size
    size_str = _format_file_size(size_bytes)

    # Format date
    date_str = _format_date(create_date)

    lines = [
        f"{index}. 📄 {name}",
        f"   Type: {doc_type}",
        f"   Folder: {folder_path}",
    ]

    if date_str:
        lines.append(f"   Created: {date_str}")

    if size_str:
        lines.append(f"   Size: {size_str}")

    return "\n".join(lines)


def _format_folder(folder: Dict[str, Any], index: int) -> str:
    """
    Format a folder result.

    Args:
        folder: Folder source
        index: Result number

    Returns:
        Formatted folder string
    """
    common = folder.get("commonAttributes", {})
    system = folder.get("systemAttributes", {})
    org = folder.get("organizationAttributes", {})

    name = common.get("name", "Unnamed Folder")
    folder_path = org.get("folderPath", "Unknown")
    create_date = system.get("createDate", "")

    # Format date
    date_str = _format_date(create_date)

    lines = [
        f"{index}. 📁 {name}",
        f"   Path: {folder_path}",
    ]

    if date_str:
        lines.append(f"   Created: {date_str}")

    return "\n".join(lines)


def _build_transparency_note(state: SearchAgentState) -> Optional[str]:
    """
    Build transparency note for multi-step queries.

    Args:
        state: Current state with step_results

    Returns:
        Transparency note or None
    """
    step_results = state.get("step_results", {})
    if not step_results or 1 not in step_results:
        return None

    try:
        # Get first step result
        step_1_result = step_results[1].get("result", {})
        if isinstance(step_1_result, dict):
            entity_name = step_1_result.get("commonAttributes", {}).get("name", "")
            if entity_name:
                return f"(Note: Resolved '{entity_name}' to complete your search)"
    except (KeyError, TypeError):
        pass

    return None


def _calculate_metadata(state: SearchAgentState, result_count: int) -> Dict[str, Any]:
    """
    Calculate execution metadata.

    Args:
        state: Current state
        result_count: Number of results

    Returns:
        Metadata dictionary
    """
    step_results = state.get("step_results", {})
    total_steps = len(step_results)

    # Calculate total execution time
    total_time_ms = 0
    for step_data in step_results.values():
        total_time_ms += step_data.get("execution_time_ms", 0)

    metadata = {
        "total_steps_executed": total_steps,
        "execution_time_ms": total_time_ms,
        "result_count": result_count
    }

    return metadata


def _format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.2 MB")
    """
    if not size_bytes or size_bytes == 0:
        return ""

    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"


def _format_date(date_str: str) -> str:
    """
    Format ISO date string to readable format.

    Args:
        date_str: ISO format date string

    Returns:
        Formatted date string (e.g., "Jan 15, 2024")
    """
    if not date_str:
        return ""

    try:
        # Parse ISO format
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%b %d, %Y")
    except (ValueError, AttributeError):
        return date_str


if __name__ == "__main__":
    # Test the formatter node
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test success case
    test_state: SearchAgentState = {
        "user_query": "Find W2 documents",
        "conversation_id": "test-formatter",
        "conversation_history": [],
        "query_plan": {
            "plan_type": "single_step",
            "total_steps": 1
        },
        "final_results": [
            {
                "entityType": "DOCUMENT",
                "commonAttributes": {
                    "name": "W2_2024.pdf",
                    "documentType": "W2",
                    "size": 1234567
                },
                "systemAttributes": {
                    "id": "doc-123",
                    "createDate": "2024-01-15T10:30:00Z"
                },
                "organizationAttributes": {
                    "folderPath": "root/Tax Documents/2024"
                }
            },
            {
                "entityType": "DOCUMENT",
                "commonAttributes": {
                    "name": "W2_2023.pdf",
                    "documentType": "W2",
                    "size": 987654
                },
                "systemAttributes": {
                    "id": "doc-456",
                    "createDate": "2023-01-20T14:15:00Z"
                },
                "organizationAttributes": {
                    "folderPath": "root/Tax Documents/2023"
                }
            }
        ],
        "step_results": {
            1: {
                "result": {},
                "execution_time_ms": 150
            }
        }
    }

    print("\n" + "=" * 70)
    print("Testing Response Formatter - Success Case")
    print("=" * 70)

    result = response_formatter_node(test_state)
    print("\n" + result["response_message"])
    print(f"\nMetadata: {json.dumps(result['metadata'], indent=2)}")

    # Test empty case
    print("\n" + "=" * 70)
    print("Testing Response Formatter - Empty Results")
    print("=" * 70)

    empty_state: SearchAgentState = {
        **test_state,
        "final_results": []
    }

    result = response_formatter_node(empty_state)
    print("\n" + result["response_message"])

    # Test error case
    print("\n" + "=" * 70)
    print("Testing Response Formatter - Error Case")
    print("=" * 70)

    error_state: SearchAgentState = {
        **test_state,
        "error": "Cannot proceed: Folder not found",
        "final_results": None
    }

    result = response_formatter_node(error_state)
    print("\n" + result["response_message"])
