"""
Unit tests for the response formatter node.

Tests cover:
- Success formatting (single and multi-step)
- Empty results formatting
- Error formatting
- Document and folder formatting
- Metadata calculation
"""

import pytest
from datetime import datetime

from search_agent.core.state import SearchAgentState
from search_agent.nodes.formatter import (
    response_formatter_node,
    _format_success_response,
    _format_empty_response,
    _format_error_response,
    _format_single_result,
    _format_document,
    _format_folder,
    _format_file_size,
    _format_date,
    _calculate_metadata,
    _build_transparency_note
)


class TestResponseFormatterNode:
    """Test cases for the response_formatter_node function."""

    def test_format_single_document_result(self):
        """Test formatting a single document result."""
        state: SearchAgentState = {
            "user_query": "Find W2 document",
            "conversation_id": "test-123",
            "conversation_history": [],
            "query_plan": {"plan_type": "single_step", "total_steps": 1},
            "final_results": {
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
            "step_results": {
                1: {"result": {}, "execution_time_ms": 100}
            }
        }

        result = response_formatter_node(state)

        assert "response_message" in result
        assert "Found 1 result" in result["response_message"]
        assert "📄 W2_2024.pdf" in result["response_message"]
        assert "Type: W2" in result["response_message"]
        assert "metadata" in result
        assert result["metadata"]["result_count"] == 1

    def test_format_multiple_document_results(self):
        """Test formatting multiple document results."""
        state: SearchAgentState = {
            "user_query": "Find W2 documents",
            "conversation_id": "test-123",
            "conversation_history": [],
            "query_plan": {"plan_type": "single_step", "total_steps": 1},
            "final_results": [
                {
                    "entityType": "DOCUMENT",
                    "commonAttributes": {"name": "W2_2024.pdf", "documentType": "W2"},
                    "systemAttributes": {"id": "doc-1"},
                    "organizationAttributes": {"folderPath": "root/Tax/2024"}
                },
                {
                    "entityType": "DOCUMENT",
                    "commonAttributes": {"name": "W2_2023.pdf", "documentType": "W2"},
                    "systemAttributes": {"id": "doc-2"},
                    "organizationAttributes": {"folderPath": "root/Tax/2023"}
                }
            ],
            "step_results": {
                1: {"result": [], "execution_time_ms": 150}
            }
        }

        result = response_formatter_node(state)

        assert "Found 2 results" in result["response_message"]
        assert "W2_2024.pdf" in result["response_message"]
        assert "W2_2023.pdf" in result["response_message"]
        assert result["metadata"]["result_count"] == 2

    def test_format_folder_result(self):
        """Test formatting a folder result."""
        state: SearchAgentState = {
            "user_query": "Find Tax folder",
            "conversation_id": "test-123",
            "conversation_history": [],
            "query_plan": {"plan_type": "single_step"},
            "final_results": {
                "entityType": "FOLDER",
                "commonAttributes": {"name": "Tax Documents"},
                "systemAttributes": {
                    "id": "folder-123",
                    "createDate": "2023-12-01T09:00:00Z"
                },
                "organizationAttributes": {
                    "folderPath": "root/Business/Tax Documents"
                }
            },
            "step_results": {
                1: {"result": {}, "execution_time_ms": 80}
            }
        }

        result = response_formatter_node(state)

        assert "📁 Tax Documents" in result["response_message"]
        assert "Path: root/Business/Tax Documents" in result["response_message"]
        assert "Dec 01, 2023" in result["response_message"]

    def test_format_empty_results(self):
        """Test formatting when no results found."""
        state: SearchAgentState = {
            "user_query": "Find nonexistent document",
            "conversation_id": "test-123",
            "conversation_history": [],
            "query_plan": {"plan_type": "single_step"},
            "final_results": [],
            "step_results": {
                1: {"result": [], "execution_time_ms": 50}
            }
        }

        result = response_formatter_node(state)

        assert "No documents or folders found" in result["response_message"]
        assert "Suggestions:" in result["response_message"]
        assert result["metadata"]["result_count"] == 0

    def test_format_error_response(self):
        """Test formatting error responses."""
        state: SearchAgentState = {
            "user_query": "Find documents",
            "conversation_id": "test-123",
            "conversation_history": [],
            "error": "Cannot proceed: Folder not found",
            "step_results": {}
        }

        result = response_formatter_node(state)

        assert "response_message" in result
        assert "couldn't find" in result["response_message"].lower()
        assert "metadata" in result
        assert "error" in result["metadata"]

    def test_multi_step_transparency_note(self):
        """Test transparency note for multi-step queries."""
        state: SearchAgentState = {
            "user_query": "List documents in Tax folder",
            "conversation_id": "test-123",
            "conversation_history": [],
            "query_plan": {"plan_type": "multi_step", "total_steps": 2},
            "final_results": [
                {
                    "entityType": "DOCUMENT",
                    "commonAttributes": {"name": "invoice.pdf"},
                    "systemAttributes": {"id": "doc-1"},
                    "organizationAttributes": {"folderPath": "root/Tax"}
                }
            ],
            "step_results": {
                1: {
                    "result": {
                        "commonAttributes": {"name": "Tax Documents"}
                    },
                    "execution_time_ms": 100
                },
                2: {
                    "result": [],
                    "execution_time_ms": 120
                }
            }
        }

        result = response_formatter_node(state)

        assert "Note: Resolved 'Tax Documents'" in result["response_message"]

    def test_no_results_no_error(self):
        """Test handling when final_results is None but no error."""
        state: SearchAgentState = {
            "user_query": "Find documents",
            "conversation_id": "test-123",
            "conversation_history": [],
            "step_results": {}
        }

        result = response_formatter_node(state)

        assert "error" in result.get("metadata", {})


class TestDocumentFormatting:
    """Test cases for document formatting."""

    def test_format_document_with_all_fields(self):
        """Test formatting document with all fields present."""
        doc = {
            "entityType": "DOCUMENT",
            "commonAttributes": {
                "name": "Report.pdf",
                "documentType": "Financial Report",
                "size": 2048000
            },
            "systemAttributes": {
                "id": "doc-123",
                "createDate": "2024-03-15T14:30:00Z"
            },
            "organizationAttributes": {
                "folderPath": "root/Reports/2024"
            }
        }

        formatted = _format_document(doc, 1)

        assert "1. 📄 Report.pdf" in formatted
        assert "Type: Financial Report" in formatted
        assert "Folder: root/Reports/2024" in formatted
        assert "Created: Mar 15, 2024" in formatted
        assert "Size: 2.0 MB" in formatted

    def test_format_document_with_missing_fields(self):
        """Test formatting document with missing optional fields."""
        doc = {
            "entityType": "DOCUMENT",
            "commonAttributes": {
                "name": "Document.txt"
            },
            "systemAttributes": {},
            "organizationAttributes": {}
        }

        formatted = _format_document(doc, 1)

        assert "📄 Document.txt" in formatted
        assert "Type: Unknown" in formatted
        # Should still format even with missing fields


class TestFolderFormatting:
    """Test cases for folder formatting."""

    def test_format_folder_with_all_fields(self):
        """Test formatting folder with all fields present."""
        folder = {
            "entityType": "FOLDER",
            "commonAttributes": {
                "name": "Projects"
            },
            "systemAttributes": {
                "id": "folder-123",
                "createDate": "2023-11-20T10:00:00Z"
            },
            "organizationAttributes": {
                "folderPath": "root/Work/Projects"
            }
        }

        formatted = _format_folder(folder, 1)

        assert "1. 📁 Projects" in formatted
        assert "Path: root/Work/Projects" in formatted
        assert "Created: Nov 20, 2023" in formatted

    def test_format_folder_with_missing_fields(self):
        """Test formatting folder with missing optional fields."""
        folder = {
            "entityType": "FOLDER",
            "commonAttributes": {
                "name": "Folder"
            },
            "systemAttributes": {},
            "organizationAttributes": {}
        }

        formatted = _format_folder(folder, 1)

        assert "📁 Folder" in formatted
        assert "Path: Unknown" in formatted


class TestHelperFunctions:
    """Test cases for helper functions."""

    def test_format_file_size_bytes(self):
        """Test file size formatting in bytes."""
        assert _format_file_size(500) == "500.0 B"

    def test_format_file_size_kb(self):
        """Test file size formatting in kilobytes."""
        assert _format_file_size(1024) == "1.0 KB"

    def test_format_file_size_mb(self):
        """Test file size formatting in megabytes."""
        assert _format_file_size(1048576) == "1.0 MB"

    def test_format_file_size_gb(self):
        """Test file size formatting in gigabytes."""
        assert _format_file_size(1073741824) == "1.0 GB"

    def test_format_file_size_zero(self):
        """Test file size formatting for zero."""
        assert _format_file_size(0) == ""
        assert _format_file_size(None) == ""

    def test_format_date_iso_format(self):
        """Test date formatting from ISO string."""
        date_str = "2024-01-15T10:30:00Z"
        formatted = _format_date(date_str)
        assert formatted == "Jan 15, 2024"

    def test_format_date_empty(self):
        """Test date formatting with empty string."""
        assert _format_date("") == ""
        assert _format_date(None) == ""

    def test_format_date_invalid(self):
        """Test date formatting with invalid string."""
        result = _format_date("invalid-date")
        # Should return original string or handle gracefully
        assert result == "invalid-date"

    def test_calculate_metadata_single_step(self):
        """Test metadata calculation for single-step query."""
        state = {
            "step_results": {
                1: {"execution_time_ms": 150}
            }
        }

        metadata = _calculate_metadata(state, 5)

        assert metadata["total_steps_executed"] == 1
        assert metadata["execution_time_ms"] == 150
        assert metadata["result_count"] == 5

    def test_calculate_metadata_multi_step(self):
        """Test metadata calculation for multi-step query."""
        state = {
            "step_results": {
                1: {"execution_time_ms": 100},
                2: {"execution_time_ms": 120}
            }
        }

        metadata = _calculate_metadata(state, 3)

        assert metadata["total_steps_executed"] == 2
        assert metadata["execution_time_ms"] == 220  # Sum of both steps
        assert metadata["result_count"] == 3

    def test_build_transparency_note_with_result(self):
        """Test building transparency note when step 1 has result."""
        state = {
            "step_results": {
                1: {
                    "result": {
                        "commonAttributes": {"name": "Tax Folder"}
                    }
                }
            }
        }

        note = _build_transparency_note(state)

        assert note is not None
        assert "Resolved 'Tax Folder'" in note

    def test_build_transparency_note_without_result(self):
        """Test building transparency note when no step results."""
        state = {"step_results": {}}

        note = _build_transparency_note(state)

        assert note is None


class TestErrorMapping:
    """Test cases for error message mapping."""

    def test_folder_not_found_error(self):
        """Test friendly message for folder not found error."""
        state: SearchAgentState = {
            "user_query": "Find documents",
            "conversation_id": "test-123",
            "conversation_history": [],
            "error": "Cannot proceed: folder_not_found",
            "step_results": {}
        }

        result = _format_error_response(state)

        assert "couldn't find a folder" in result["response_message"].lower()

    def test_service_unavailable_error(self):
        """Test friendly message for service unavailable error."""
        state: SearchAgentState = {
            "user_query": "Find documents",
            "conversation_id": "test-123",
            "conversation_history": [],
            "error": "service_unavailable",
            "step_results": {}
        }

        result = _format_error_response(state)

        assert "trouble reaching the search service" in result["response_message"].lower()

    def test_generic_error(self):
        """Test generic error message for unknown errors."""
        state: SearchAgentState = {
            "user_query": "Find documents",
            "conversation_id": "test-123",
            "conversation_history": [],
            "error": "Something unexpected happened",
            "step_results": {}
        }

        result = _format_error_response(state)

        assert "error occurred" in result["response_message"].lower()
        assert "Something unexpected happened" in result["response_message"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
