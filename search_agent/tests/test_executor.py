"""
Unit tests for the query executor node.

Tests cover:
- Single-step execution
- Multi-step execution with dependencies
- ES query generation and validation
- Result analysis and clarification
- Error handling and retries
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager

from search_agent.core.state import SearchAgentState
from search_agent.core.models import QueryPlan, Step
from search_agent.nodes.executor import (
    query_executor_node,
    _analyze_result,
    _create_clarification,
    _get_result_count
)


@contextmanager
def mock_executor_dependencies():
    """Context manager to mock all executor dependencies for testing."""
    with patch('search_agent.nodes.executor.get_llm_service') as mock_get_llm, \
         patch('search_agent.nodes.executor.get_elasticsearch_service') as mock_get_es, \
         patch('search_agent.nodes.executor.validate_elasticsearch_query') as mock_validate, \
         patch('search_agent.nodes.executor.build_executor_prompt') as mock_build_prompt:

        # Setup default mocks
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm

        mock_es = Mock()
        mock_get_es.return_value = mock_es

        # Default to no validation errors
        mock_validate.return_value = []

        # Default prompt
        mock_build_prompt.return_value = "mocked prompt"

        yield {
            'llm': mock_llm,
            'es': mock_es,
            'validate': mock_validate,
            'prompt': mock_build_prompt
        }


class TestQueryExecutorNode:
    """Test cases for the query_executor_node function."""

    def test_single_step_execution_success(self):
        """Test successful single-step query execution."""
        # Setup plan
        plan = QueryPlan(
            plan_type="single_step",
            reasoning="Direct query for W2 documents",
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
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        # Mock LLM to return a valid query
        mock_es_query = {
            "bool": {
                "must": [
                    {"term": {"entityType.keyword": "DOCUMENT"}},
                    {"term": {"commonAttributes.documentType.keyword": "W2"}}
                ]
            }
        }

        # Mock ES service to return results
        mock_es_result = {
            "took": 10,
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {
                        "_source": {
                            "entityType": "DOCUMENT",
                            "commonAttributes": {"name": "W2_2024.pdf", "documentType": "W2"}
                        }
                    },
                    {
                        "_source": {
                            "entityType": "DOCUMENT",
                            "commonAttributes": {"name": "W2_2023.pdf", "documentType": "W2"}
                        }
                    }
                ]
            }
        }

        with mock_executor_dependencies() as mocks:
            # Configure mocks for this test
            mocks['llm'].call_with_json_response.return_value = mock_es_query
            mocks['es'].search.return_value = mock_es_result

            # Execute
            result = query_executor_node(state)

            # Assertions
            assert "error" not in result
            assert "final_results" in result
            assert len(result["final_results"]) == 2
            assert result["step_results"][1]["result_count"] == 2
            assert result["current_step"] == 1  # Stays at step 1 (complete)

    def test_multi_step_execution(self):
        """Test multi-step query execution with dependencies."""
        # Setup 2-step plan
        plan = QueryPlan(
            plan_type="multi_step",
            reasoning="Need to resolve folder name to ID",
            total_steps=2,
            steps=[
                Step(step=1, description="Find the folder named 'Tax Documents'"),
                Step(step=2, description="Find documents in that folder", depends_on_step=1)
            ]
        )

        state: SearchAgentState = {
            "user_query": "List documents in Tax Documents folder",
            "query_plan": plan.model_dump(),
            "total_steps": 2,
            "current_step": 1,
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        # Mock responses for step 1
        step1_query = {
            "bool": {
                "must": [
                    {"term": {"entityType.keyword": "FOLDER"}},
                    {"term": {"commonAttributes.name.keyword": "Tax Documents"}}
                ]
            }
        }

        step1_result = {
            "hits": {
                "total": {"value": 1},
                "hits": [{
                    "_source": {
                        "entityType": "FOLDER",
                        "systemAttributes": {"id": "folder-123"},
                        "commonAttributes": {"name": "Tax Documents"}
                    }
                }]
            }
        }

        with patch('search_agent.nodes.executor.get_llm_service') as mock_get_llm, \
             patch('search_agent.nodes.executor.get_elasticsearch_service') as mock_get_es, \
             patch('search_agent.nodes.executor.validate_elasticsearch_query') as mock_validate:

            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = step1_query
            mock_get_llm.return_value = mock_llm

            mock_es = Mock()
            mock_es.search.return_value = step1_result
            mock_get_es.return_value = mock_es

            # Mock validation to pass
            mock_validate.return_value = []

            # Execute step 1
            result = query_executor_node(state)

            # Should advance to step 2
            assert "error" not in result
            assert result["current_step"] == 2
            assert 1 in result["step_results"]
            assert result["step_results"][1]["result"]["systemAttributes"]["id"] == "folder-123"

    def test_validation_error_with_retry(self):
        """Test that executor retries on validation errors."""
        plan = QueryPlan(
            plan_type="single_step",
            reasoning="Testing validation retry mechanism for query generation errors",
            total_steps=1,
            steps=[Step(step=1, description="Find documents in the system")]
        )

        state: SearchAgentState = {
            "user_query": "Find documents",
            "query_plan": plan.model_dump(),
            "total_steps": 1,
            "current_step": 1,
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        # Mock LLM to return invalid query (missing required structure)
        invalid_query = {"invalid": "query"}

        with patch('search_agent.nodes.executor.get_llm_service') as mock_get_llm, \
             patch('search_agent.nodes.executor.validate_elasticsearch_query') as mock_validate:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = invalid_query
            mock_get_llm.return_value = mock_llm

            # Mock validation to return errors
            mock_validate.return_value = ["Query must contain at least one of: bool, match, term"]

            # Execute
            result = query_executor_node(state)

            # Should increment retry count
            assert "retry_count" in result
            assert result["retry_count"] == 1
            assert "validation_feedback" in result

    def test_max_retries_exceeded(self):
        """Test that executor fails after max retries."""
        plan = QueryPlan(
            plan_type="single_step",
            reasoning="Testing maximum retry limit for validation failures in query generation",
            total_steps=1,
            steps=[Step(step=1, description="Find documents in the system")]
        )

        state: SearchAgentState = {
            "user_query": "Find documents",
            "query_plan": plan.model_dump(),
            "total_steps": 1,
            "current_step": 1,
            "retry_count": 3,  # Already at max
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        invalid_query = {"invalid": "query"}

        with patch('search_agent.nodes.executor.get_llm_service') as mock_get_llm, \
             patch('search_agent.nodes.executor.validate_elasticsearch_query') as mock_validate:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = invalid_query
            mock_get_llm.return_value = mock_llm

            # Mock validation to return errors
            mock_validate.return_value = ["Query must contain at least one of: bool, match, term"]

            # Execute
            result = query_executor_node(state)

            # Should set error
            assert "error" in result
            assert "Could not generate valid query" in result["error"]

    def test_empty_result_intermediate_step(self):
        """Test empty result in intermediate step causes critical error."""
        plan = QueryPlan(
            plan_type="multi_step",
            reasoning="Testing empty intermediate result handling for multi-step queries",
            total_steps=2,
            steps=[
                Step(step=1, description="Find folder named NonExistent"),
                Step(step=2, description="Find documents in that folder", depends_on_step=1)
            ]
        )

        state: SearchAgentState = {
            "user_query": "List documents in NonExistent folder",
            "query_plan": plan.model_dump(),
            "total_steps": 2,
            "current_step": 1,
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        valid_query = {"bool": {"must": [{"term": {"entityType.keyword": "FOLDER"}}]}}
        empty_result = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch('search_agent.nodes.executor.get_llm_service') as mock_get_llm, \
             patch('search_agent.nodes.executor.get_elasticsearch_service') as mock_get_es, \
             patch('search_agent.nodes.executor.validate_elasticsearch_query') as mock_validate:

            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = valid_query
            mock_get_llm.return_value = mock_llm

            mock_es = Mock()
            mock_es.search.return_value = empty_result
            mock_get_es.return_value = mock_es

            # Mock validation to pass
            mock_validate.return_value = []

            # Execute
            result = query_executor_node(state)

            # Should set critical error
            assert "error" in result
            assert "Cannot proceed" in result["error"]


class TestResultAnalysis:
    """Test cases for result analysis functions."""

    def test_analyze_single_result_success(self):
        """Test analysis of single result."""
        result = {
            "hits": {
                "total": {"value": 1},
                "hits": [{
                    "_source": {"entityType": "FOLDER", "commonAttributes": {"name": "Test"}}
                }]
            }
        }

        result_type, data, clarif = _analyze_result(
            result=result,
            current_step=1,
            total_steps=2,
            step_description="Find folder"
        )

        assert result_type == "success"
        assert data["entityType"] == "FOLDER"
        assert clarif is None

    def test_analyze_multiple_results_intermediate_step(self):
        """Test multiple results in intermediate step triggers clarification."""
        result = {
            "hits": {
                "total": {"value": 3},
                "hits": [
                    {"_source": {"entityType": "FOLDER", "commonAttributes": {"name": "Folder1"}}},
                    {"_source": {"entityType": "FOLDER", "commonAttributes": {"name": "Folder2"}}},
                    {"_source": {"entityType": "FOLDER", "commonAttributes": {"name": "Folder3"}}}
                ]
            }
        }

        result_type, data, clarif = _analyze_result(
            result=result,
            current_step=1,
            total_steps=2,
            step_description="Find folder"
        )

        assert result_type == "needs_clarification"
        assert clarif is not None
        assert clarif["type"] == "multiple_choice"
        assert len(clarif["options"]) == 3

    def test_analyze_multiple_results_final_step(self):
        """Test multiple results in final step is success."""
        result = {
            "hits": {
                "total": {"value": 5},
                "hits": [{"_source": {"entityType": "DOCUMENT"}} for _ in range(5)]
            }
        }

        result_type, data, clarif = _analyze_result(
            result=result,
            current_step=2,
            total_steps=2,  # Final step
            step_description="Find documents"
        )

        assert result_type == "success"
        assert isinstance(data, list)
        assert len(data) == 5
        assert clarif is None

    def test_analyze_empty_result_final_step(self):
        """Test empty result in final step is acceptable."""
        result = {"hits": {"total": {"value": 0}, "hits": []}}

        result_type, data, clarif = _analyze_result(
            result=result,
            current_step=1,
            total_steps=1,  # Final step
            step_description="Find documents"
        )

        assert result_type == "empty_result"
        assert data == []
        assert clarif is None


class TestClarification:
    """Test cases for clarification creation."""

    def test_create_clarification_folders(self):
        """Test clarification for folder selection."""
        hits = [
            {
                "_source": {
                    "entityType": "FOLDER",
                    "commonAttributes": {"name": "Tax"},
                    "organizationAttributes": {"folderPath": "root/Personal/Tax"}
                }
            },
            {
                "_source": {
                    "entityType": "FOLDER",
                    "commonAttributes": {"name": "Tax"},
                    "organizationAttributes": {"folderPath": "root/Business/Tax"}
                }
            }
        ]

        clarif = _create_clarification(hits, "Find folder named Tax")

        assert clarif["type"] == "multiple_choice"
        assert "2" in clarif["question"] or "2 folders" in clarif["question"].lower()
        assert len(clarif["options"]) == 2
        assert clarif["options"][0]["number"] == 1
        assert clarif["options"][1]["number"] == 2
        assert "value" in clarif["options"][0]


class TestHelperFunctions:
    """Test cases for helper functions."""

    def test_get_result_count(self):
        """Test extracting result count."""
        result = {"hits": {"total": {"value": 42}}}
        assert _get_result_count(result) == 42

        empty_result = {"hits": {"total": {"value": 0}}}
        assert _get_result_count(empty_result) == 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
