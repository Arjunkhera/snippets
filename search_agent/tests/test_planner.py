"""
Unit tests for the query planner node.

Tests cover:
- Single-step query planning
- Multi-step query planning
- Plan validation
- LLM error handling
- Gap analysis accuracy
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

from search_agent.core.state import SearchAgentState
from search_agent.core.models import QueryPlan, Step
from search_agent.nodes.planner import query_planner_node, validate_plan_dependencies
from search_agent.utils.validation import validate_query_plan


class TestQueryPlannerNode:
    """Test cases for the query_planner_node function."""

    def test_single_step_query_planning(self):
        """Test that single-step queries are correctly planned."""
        # Mock LLM response for single-step query
        mock_response = {
            "plan_type": "single_step",
            "reasoning": "Query only requires filtering documents by type. The field 'commonAttributes.documentType' exists directly on DOCUMENT entities.",
            "total_steps": 1,
            "steps": [
                {
                    "step": 1,
                    "description": "Find all documents where document type is W2"
                }
            ]
        }

        # Create initial state
        state: SearchAgentState = {
            "user_query": "Find all W2 documents",
            "intent": "search",
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        # Mock the LLM service
        with patch('search_agent.nodes.planner.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            # Execute planner node
            result = query_planner_node(state)

            # Assertions
            assert "error" not in result
            assert result["query_plan"]["plan_type"] == "single_step"
            assert result["total_steps"] == 1
            assert result["current_step"] == 1
            assert len(result["query_plan"]["steps"]) == 1

    def test_multi_step_query_planning(self):
        """Test that multi-step queries are correctly planned."""
        # Mock LLM response for multi-step query
        mock_response = {
            "plan_type": "multi_step",
            "reasoning": "User references folder by name 'Tax Documents' but documents only store parent folder ID. Need to resolve folder name to ID first.",
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

        # Create initial state
        state: SearchAgentState = {
            "user_query": "List documents in Tax Documents folder",
            "intent": "search",
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        # Mock the LLM service
        with patch('search_agent.nodes.planner.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            # Execute planner node
            result = query_planner_node(state)

            # Assertions
            assert "error" not in result
            assert result["query_plan"]["plan_type"] == "multi_step"
            assert result["total_steps"] == 2
            assert result["current_step"] == 1
            assert len(result["query_plan"]["steps"]) == 2
            assert result["query_plan"]["steps"][1]["depends_on_step"] == 1

    def test_llm_invalid_json_with_retry(self):
        """Test that planner retries when LLM returns invalid JSON."""
        # First call returns invalid JSON, second call returns valid plan
        invalid_response_text = "This is not JSON at all"
        valid_response = {
            "plan_type": "single_step",
            "reasoning": "Valid plan after retry with proper error handling",
            "total_steps": 1,
            "steps": [
                {
                    "step": 1,
                    "description": "Find all documents where document type is W2"
                }
            ]
        }

        state: SearchAgentState = {
            "user_query": "Find all W2 documents",
            "intent": "search",
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        with patch('search_agent.nodes.planner.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            # First call raises JSONDecodeError, second call succeeds
            mock_llm.call_with_json_response.side_effect = [
                json.JSONDecodeError("Invalid JSON", invalid_response_text, 0),
                valid_response
            ]
            mock_get_llm.return_value = mock_llm

            # Execute planner node
            result = query_planner_node(state)

            # Should succeed after retry
            assert "error" not in result
            assert result["query_plan"]["plan_type"] == "single_step"
            # Should have called LLM twice (initial + 1 retry)
            assert mock_llm.call_with_json_response.call_count == 2

    def test_llm_validation_error_with_retry(self):
        """Test that planner retries when LLM returns invalid plan structure."""
        # First call returns invalid plan, second call returns valid plan
        invalid_response = {
            "plan_type": "single_step",
            "reasoning": "Too short",  # Less than 20 chars - will fail validation
            "total_steps": 1,
            "steps": []  # Empty steps - will fail validation
        }

        valid_response = {
            "plan_type": "single_step",
            "reasoning": "This is a valid reasoning with sufficient length for validation",
            "total_steps": 1,
            "steps": [
                {
                    "step": 1,
                    "description": "Find all documents where document type is W2"
                }
            ]
        }

        state: SearchAgentState = {
            "user_query": "Find all W2 documents",
            "intent": "search",
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        with patch('search_agent.nodes.planner.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.side_effect = [
                invalid_response,
                valid_response
            ]
            mock_get_llm.return_value = mock_llm

            # Execute planner node
            result = query_planner_node(state)

            # Should succeed after retry
            assert "error" not in result
            assert result["query_plan"]["plan_type"] == "single_step"

    def test_llm_max_retries_exceeded(self):
        """Test that planner fails gracefully after max retries."""
        state: SearchAgentState = {
            "user_query": "Find all W2 documents",
            "intent": "search",
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        with patch('search_agent.nodes.planner.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            # Always return invalid JSON
            mock_llm.call_with_json_response.side_effect = json.JSONDecodeError(
                "Invalid JSON", "bad response", 0
            )
            mock_get_llm.return_value = mock_llm

            # Execute planner node
            result = query_planner_node(state)

            # Should have error after max retries
            assert "error" in result
            assert "Failed to parse plan from LLM response" in result["error"]
            # Should have tried 3 times
            assert mock_llm.call_with_json_response.call_count == 3

    def test_prompt_building_failure(self):
        """Test error handling when prompt building fails."""
        state: SearchAgentState = {
            "user_query": "Find all W2 documents",
            "intent": "search",
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        # Mock the prompt builder to raise an exception
        with patch('search_agent.nodes.planner.build_planner_prompt') as mock_build:
            mock_build.side_effect = FileNotFoundError("ES mapping file not found")

            # Execute planner node
            result = query_planner_node(state)

            # Should have error
            assert "error" in result
            assert "Failed to build planner prompt" in result["error"]


class TestPlanValidation:
    """Test cases for plan validation functions."""

    def test_validate_valid_single_step_plan(self):
        """Test validation of a valid single-step plan."""
        plan = QueryPlan(
            plan_type="single_step",
            reasoning="This is a valid reasoning for single step execution",
            total_steps=1,
            steps=[
                Step(step=1, description="Find all documents where type is W2")
            ]
        )

        errors = validate_query_plan(plan)
        assert len(errors) == 0

    def test_validate_valid_multi_step_plan(self):
        """Test validation of a valid multi-step plan."""
        plan = QueryPlan(
            plan_type="multi_step",
            reasoning="Need to resolve folder name to ID before querying documents",
            total_steps=2,
            steps=[
                Step(step=1, description="Find the folder named Tax Documents"),
                Step(step=2, description="Find documents in that folder", depends_on_step=1)
            ]
        )

        errors = validate_query_plan(plan)
        assert len(errors) == 0

    def test_validate_plan_step_count_mismatch(self):
        """Test that validation catches total_steps mismatch."""
        plan = QueryPlan(
            plan_type="single_step",
            reasoning="Valid reasoning for testing purposes only",
            total_steps=2,  # Says 2 but only has 1 step
            steps=[
                Step(step=1, description="Find all documents where type is W2")
            ]
        )

        errors = validate_query_plan(plan)
        assert len(errors) > 0
        assert any("total_steps" in error and "does not match" in error for error in errors)

    def test_validate_plan_type_mismatch(self):
        """Test that validation catches plan_type mismatch with step count."""
        plan = QueryPlan(
            plan_type="single_step",  # Says single but has 2 steps
            reasoning="Valid reasoning for testing purposes only",
            total_steps=2,
            steps=[
                Step(step=1, description="Find the folder named Tax Documents"),
                Step(step=2, description="Find documents in that folder", depends_on_step=1)
            ]
        )

        errors = validate_query_plan(plan)
        assert len(errors) > 0
        assert any("single_step" in error and "must be 1" in error for error in errors)

    def test_validate_plan_invalid_dependency(self):
        """Test that validation catches invalid step dependencies."""
        # Pydantic validation catches depends_on_step >= step during model creation
        # So we test that this raises a ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Step(step=2, description="Find documents in that folder", depends_on_step=5)  # Invalid!

        # Verify the error is about the dependency
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("depends_on_step" in str(error) for error in errors)

    def test_validate_plan_short_description(self):
        """Test that validation catches short descriptions."""
        # Pydantic validation catches short descriptions during model creation
        # So we test that this raises a ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Step(step=1, description="Find docs")  # Too short!

        # Verify the error is about the description length
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("description" in str(error) for error in errors)

    def test_validate_plan_short_reasoning(self):
        """Test that validation catches short reasoning."""
        # This should fail Pydantic validation before reaching our validator
        with pytest.raises(ValidationError):
            plan = QueryPlan(
                plan_type="single_step",
                reasoning="Short",  # Less than 20 chars
                total_steps=1,
                steps=[
                    Step(step=1, description="Find all documents where type is W2")
                ]
            )

    def test_validate_plan_dependencies_helper(self):
        """Test the validate_plan_dependencies helper function."""
        plan = QueryPlan(
            plan_type="multi_step",
            reasoning="Valid reasoning for testing purposes only",
            total_steps=2,
            steps=[
                Step(step=1, description="Find the folder named Tax Documents"),
                Step(step=2, description="Find documents in that folder", depends_on_step=1)
            ]
        )

        errors = validate_plan_dependencies(plan)
        assert len(errors) == 0


class TestGapAnalysis:
    """Test cases for gap analysis accuracy."""

    def test_gap_analysis_folder_name_to_documents(self):
        """Test that planner correctly identifies folder name resolution as multi-step."""
        mock_response = {
            "plan_type": "multi_step",
            "reasoning": "Documents store parent folder ID, not name. Must resolve folder name to ID first.",
            "total_steps": 2,
            "steps": [
                {
                    "step": 1,
                    "description": "Find folder named Business to get its ID"
                },
                {
                    "step": 2,
                    "description": "Find documents where parent folder ID matches the ID from step 1",
                    "depends_on_step": 1
                }
            ]
        }

        state: SearchAgentState = {
            "user_query": "Show documents in Business folder",
            "intent": "search",
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        with patch('search_agent.nodes.planner.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = query_planner_node(state)

            assert result["query_plan"]["plan_type"] == "multi_step"
            assert result["total_steps"] == 2

    def test_gap_analysis_direct_document_type_single_step(self):
        """Test that planner correctly identifies direct queries as single-step."""
        mock_response = {
            "plan_type": "single_step",
            "reasoning": "Document type field exists directly on documents, no resolution needed",
            "total_steps": 1,
            "steps": [
                {
                    "step": 1,
                    "description": "Find all documents where document type is invoice"
                }
            ]
        }

        state: SearchAgentState = {
            "user_query": "Find all invoice documents",
            "intent": "search",
            "conversation_id": "test-123",
            "conversation_history": [],
        }

        with patch('search_agent.nodes.planner.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = query_planner_node(state)

            assert result["query_plan"]["plan_type"] == "single_step"
            assert result["total_steps"] == 1


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
