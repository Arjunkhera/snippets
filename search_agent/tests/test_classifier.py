"""
Unit tests for the query classifier node.

Tests cover:
- Intent classification (search, move, delete, create, other)
- Confidence levels
- Error handling and retries
- Validation
"""

import json
import pytest
from unittest.mock import Mock, patch

from search_agent.core.state import SearchAgentState
from search_agent.nodes.classifier import (
    query_classifier_node,
    _build_classifier_prompt,
    _validate_classification_response
)


class TestQueryClassifierNode:
    """Test cases for the query_classifier_node function."""

    def test_search_intent_classification(self):
        """Test classification of search/list queries."""
        state: SearchAgentState = {
            "user_query": "Find all W2 documents",
            "conversation_id": "test-123",
            "conversation_history": []
        }

        mock_response = {
            "intent": "search",
            "confidence": "high",
            "reasoning": "User wants to find documents using keywords 'find' and 'all'"
        }

        with patch('search_agent.nodes.classifier.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = query_classifier_node(state)

            assert result["intent"] == "search"
            assert result["classification_confidence"] == "high"
            assert len(result["classification_reasoning"]) > 10  # Has meaningful reasoning

    def test_move_intent_classification(self):
        """Test classification of move operations."""
        state: SearchAgentState = {
            "user_query": "Move invoice.pdf to Archive folder",
            "conversation_id": "test-123",
            "conversation_history": []
        }

        mock_response = {
            "intent": "move",
            "confidence": "high",
            "reasoning": "User wants to relocate a document to another folder"
        }

        with patch('search_agent.nodes.classifier.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = query_classifier_node(state)

            assert result["intent"] == "move"
            assert result["classification_confidence"] == "high"

    def test_delete_intent_classification(self):
        """Test classification of delete operations."""
        state: SearchAgentState = {
            "user_query": "Delete old tax documents from 2020",
            "conversation_id": "test-123",
            "conversation_history": []
        }

        mock_response = {
            "intent": "delete",
            "confidence": "high",
            "reasoning": "User wants to remove documents using keyword 'delete'"
        }

        with patch('search_agent.nodes.classifier.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = query_classifier_node(state)

            assert result["intent"] == "delete"

    def test_create_intent_classification(self):
        """Test classification of create operations."""
        state: SearchAgentState = {
            "user_query": "Create a new folder called Projects",
            "conversation_id": "test-123",
            "conversation_history": []
        }

        mock_response = {
            "intent": "create",
            "confidence": "high",
            "reasoning": "User wants to create a new folder"
        }

        with patch('search_agent.nodes.classifier.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = query_classifier_node(state)

            assert result["intent"] == "create"

    def test_other_intent_classification(self):
        """Test classification of help/unclear queries."""
        state: SearchAgentState = {
            "user_query": "How does this system work?",
            "conversation_id": "test-123",
            "conversation_history": []
        }

        mock_response = {
            "intent": "other",
            "confidence": "high",
            "reasoning": "User is asking about system capabilities, not requesting an action"
        }

        with patch('search_agent.nodes.classifier.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = query_classifier_node(state)

            assert result["intent"] == "other"

    def test_conversation_history_context(self):
        """Test that conversation history is included in prompt."""
        state: SearchAgentState = {
            "user_query": "Show me those",
            "conversation_id": "test-123",
            "conversation_history": [
                {"role": "user", "content": "Find W2 documents"},
                {"role": "assistant", "content": "Found 2 W2 documents"}
            ]
        }

        mock_response = {
            "intent": "search",
            "confidence": "medium",
            "reasoning": "Based on context, user is referring to W2 documents from previous query"
        }

        with patch('search_agent.nodes.classifier.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_with_json_response.return_value = mock_response
            mock_get_llm.return_value = mock_llm

            result = query_classifier_node(state)

            # Check that LLM was called with prompt containing history
            call_args = mock_llm.call_with_json_response.call_args
            prompt = call_args.kwargs['prompt']
            assert "W2 documents" in prompt

    def test_retry_on_invalid_json(self):
        """Test retry logic when LLM returns invalid JSON."""
        state: SearchAgentState = {
            "user_query": "Find documents",
            "conversation_id": "test-123",
            "conversation_history": []
        }

        with patch('search_agent.nodes.classifier.get_llm_service') as mock_get_llm:
            mock_llm = Mock()

            # First attempt: invalid JSON (missing field)
            # Second attempt: valid JSON
            mock_llm.call_with_json_response.side_effect = [
                {"intent": "search"},  # Missing confidence and reasoning
                {
                    "intent": "search",
                    "confidence": "high",
                    "reasoning": "Valid response"
                }
            ]
            mock_get_llm.return_value = mock_llm

            result = query_classifier_node(state)

            # Should have retried and succeeded
            assert result["intent"] == "search"
            assert mock_llm.call_with_json_response.call_count == 2

    def test_default_to_other_after_max_retries(self):
        """Test that classifier defaults to 'other' after max retries."""
        state: SearchAgentState = {
            "user_query": "Find documents",
            "conversation_id": "test-123",
            "conversation_history": []
        }

        with patch('search_agent.nodes.classifier.get_llm_service') as mock_get_llm:
            mock_llm = Mock()

            # Both attempts return invalid responses
            mock_llm.call_with_json_response.side_effect = [
                {"intent": "search"},  # Missing fields
                {"intent": "search"}   # Missing fields again
            ]
            mock_get_llm.return_value = mock_llm

            result = query_classifier_node(state)

            # Should default to "other" with low confidence
            assert result["intent"] == "other"
            assert result["classification_confidence"] == "low"
            assert mock_llm.call_with_json_response.call_count == 2


class TestClassifierPromptBuilder:
    """Test cases for prompt building."""

    def test_prompt_includes_user_query(self):
        """Test that prompt includes the user query."""
        prompt = _build_classifier_prompt(
            user_query="Find W2 documents",
            conversation_history=[]
        )

        assert "Find W2 documents" in prompt
        assert "USER QUERY:" in prompt

    def test_prompt_includes_intent_categories(self):
        """Test that prompt includes all intent categories."""
        prompt = _build_classifier_prompt(
            user_query="test",
            conversation_history=[]
        )

        assert '"search"' in prompt
        assert '"move"' in prompt
        assert '"delete"' in prompt
        assert '"create"' in prompt
        assert '"other"' in prompt

    def test_prompt_includes_conversation_history(self):
        """Test that conversation history is formatted in prompt."""
        history = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"}
        ]

        prompt = _build_classifier_prompt(
            user_query="test",
            conversation_history=history
        )

        assert "First message" in prompt
        assert "First response" in prompt

    def test_prompt_limits_history_to_last_5(self):
        """Test that only last 5 messages are included."""
        history = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]

        prompt = _build_classifier_prompt(
            user_query="test",
            conversation_history=history
        )

        # Should include messages 5-9, not 0-4
        assert "Message 9" in prompt
        assert "Message 5" in prompt
        assert "Message 0" not in prompt


class TestClassificationValidation:
    """Test cases for validation logic."""

    def test_valid_response(self):
        """Test validation of valid response."""
        valid_response = {
            "intent": "search",
            "confidence": "high",
            "reasoning": "This is a valid reasoning with enough characters"
        }

        # Should not raise
        _validate_classification_response(valid_response)

    def test_missing_field_raises_error(self):
        """Test that missing required fields raise error."""
        invalid_response = {
            "intent": "search",
            "confidence": "high"
            # Missing reasoning
        }

        with pytest.raises(ValueError, match="Missing required field"):
            _validate_classification_response(invalid_response)

    def test_invalid_intent_raises_error(self):
        """Test that invalid intent value raises error."""
        invalid_response = {
            "intent": "invalid_intent",
            "confidence": "high",
            "reasoning": "Valid reasoning"
        }

        with pytest.raises(ValueError, match="Invalid intent"):
            _validate_classification_response(invalid_response)

    def test_invalid_confidence_raises_error(self):
        """Test that invalid confidence value raises error."""
        invalid_response = {
            "intent": "search",
            "confidence": "very_high",
            "reasoning": "Valid reasoning"
        }

        with pytest.raises(ValueError, match="Invalid confidence"):
            _validate_classification_response(invalid_response)

    def test_short_reasoning_raises_error(self):
        """Test that too-short reasoning raises error."""
        invalid_response = {
            "intent": "search",
            "confidence": "high",
            "reasoning": "Short"
        }

        with pytest.raises(ValueError, match="Reasoning must be at least 10 characters"):
            _validate_classification_response(invalid_response)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
