"""
Integration tests for Agent 1 (Requirements Architect).

Tests the complete workflow from requirements gathering to PRD approval.
Uses mocked Anthropic API calls to avoid external dependencies.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tool_builder_system import (
    create_initial_state,
    Agent1,
    ToolBuilderWorkflow,
    StatePersistence
)


class TestAgent1Integration:
    """Integration tests for Agent 1."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mocked Anthropic client."""
        with patch('tool_builder_system.agents.agent_1.Anthropic') as mock:
            # Create mock client instance
            mock_client = MagicMock()
            mock.return_value = mock_client

            # Setup mock responses
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Hello! What tool would you like to create?"

            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response

            yield mock_client

    @pytest.fixture
    def agent_1(self, mock_anthropic_client):
        """Create Agent 1 instance with mocked client."""
        agent = Agent1(api_key="test-key")
        agent.client = mock_anthropic_client
        return agent

    @pytest.fixture
    def test_state(self):
        """Create initial test state."""
        return create_initial_state("I want to create a tool that validates JSON files")

    def test_agent_1_initialization(self):
        """Test Agent 1 initializes correctly."""
        with patch('tool_builder_system.agents.agent_1.Anthropic'):
            agent = Agent1(api_key="test-key")
            assert agent.model == "claude-sonnet-4-20250514"
            assert agent.system_prompt is not None
            assert len(agent.system_prompt) > 0

    def test_discovery_phase(self, agent_1, test_state, mock_anthropic_client):
        """Test discovery phase adds conversation and calls API."""
        # Setup mock response
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Great! What should we name this JSON validation function?"
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response

        # Run discovery
        updated_state = agent_1.discovery(test_state)

        # Verify API was called
        assert mock_anthropic_client.messages.create.called

        # Verify conversation history updated
        assert len(updated_state["conversation_history"]) == 2
        assert updated_state["conversation_history"][-1]["role"] == "assistant"
        assert "JSON validation" in updated_state["conversation_history"][-1]["content"]

        # Verify phase updated
        assert updated_state["current_phase"] == "discovery"

    def test_generate_artifacts_phase(self, agent_1, test_state, mock_anthropic_client):
        """Test artifact generation creates PRD and JSON schema."""
        # Setup mock response with PRD and JSON
        prd_content = """# Tool: validate_json_file

**Description:**

Validates JSON files by checking syntax and structure.

**Function Name:**

`validate_json_file`

**Input Parameters:**

* **`file_path`** (`str`, Required): Path to JSON file

**Success Output:**

```json
{
  "valid": true,
  "message": "JSON is valid"
}
```

**Error Outputs:**

* **Invalid JSON:**
    ```json
    {
      "error_code": "INVALID_JSON",
      "error_message": "JSON syntax is invalid"
    }
    ```

**Constraints & Behaviors:**

* Maximum file size: 10MB
"""

        json_schema = {
            "validate_json_file": {
                "type": "function",
                "name": "validate_json_file",
                "description": "Validates JSON files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to JSON file"
                        }
                    },
                    "required": ["file_path"],
                    "additionalProperties": False
                }
            }
        }

        response_text = f"""
I've created the PRD and JSON schema:

## PRD: validate_json_file

{prd_content}

## JSON Schema

```json
{json.dumps(json_schema, indent=2)}
```
"""

        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = response_text
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response

        # Run generation
        updated_state = agent_1.generate_artifacts(test_state)

        # Verify artifacts extracted
        assert updated_state["prd_content"] is not None
        assert "validate_json_file" in updated_state["prd_content"]

        assert updated_state["json_schema"] is not None
        assert "validate_json_file" in updated_state["json_schema"]

        assert updated_state["current_phase"] == "review"

    def test_review_approval(self, agent_1, test_state):
        """Test review phase detects approval."""
        # Add some artifacts to state
        test_state["prd_content"] = "# Tool: test_function\n..."
        test_state["json_schema"] = {"test_function": {"type": "function"}}

        # Test approval
        updated_state = agent_1.review(test_state, "Looks good, proceed!")

        assert updated_state["prd_approved"] is True
        assert updated_state["current_phase"] == "approved"

    def test_review_iteration(self, agent_1, test_state, mock_anthropic_client):
        """Test review phase handles iteration requests."""
        # Setup state with artifacts
        test_state["prd_content"] = "# Tool: test_function\n..."
        test_state["json_schema"] = {"test_function": {"type": "function"}}

        # Setup mock response
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "I'll update the max file size to 20MB..."
        mock_response.content = [mock_content]
        mock_anthropic_client.messages.create.return_value = mock_response

        # Request change
        updated_state = agent_1.review(test_state, "Change max file size to 20MB")

        assert updated_state["prd_approved"] is False
        assert updated_state["current_phase"] == "review"
        assert mock_anthropic_client.messages.create.called

    def test_state_persistence(self, tmp_path):
        """Test state can be saved and loaded."""
        persistence = StatePersistence(base_path=str(tmp_path))

        # Create and save state
        state = create_initial_state("Test tool")
        state["function_name"] = "test_function"
        state["prd_content"] = "Test PRD content"

        saved_path = persistence.save_state(state, "test_session")

        # Verify file exists
        assert Path(saved_path).exists()

        # Load state
        loaded_state = persistence.load_state("test_session")

        assert loaded_state is not None
        assert loaded_state["function_name"] == "test_function"
        assert loaded_state["prd_content"] == "Test PRD content"

    def test_artifact_extraction_prd(self, agent_1, test_state):
        """Test PRD extraction from response text."""
        response_text = """
# Tool: my_function

**Description:**
Does something cool

**Function Name:**
`my_function`
"""

        prd, schema = agent_1._extract_artifacts(response_text, test_state)

        assert prd is not None
        assert "my_function" in prd
        assert "Description:" in prd

    def test_artifact_extraction_json_schema(self, agent_1, test_state):
        """Test JSON schema extraction from response text."""
        schema_dict = {
            "my_function": {
                "type": "function",
                "name": "my_function",
                "description": "Test",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

        response_text = f"""
Here's the JSON schema:

```json
{json.dumps(schema_dict, indent=2)}
```
"""

        prd, schema = agent_1._extract_artifacts(response_text, test_state)

        assert schema is not None
        assert "my_function" in schema
        assert schema["my_function"]["type"] == "function"


class TestWorkflowIntegration:
    """Integration tests for the complete workflow."""

    @pytest.fixture
    def mock_agent_1(self):
        """Create a mocked Agent 1."""
        with patch('tool_builder_system.agents.agent_1.Anthropic'):
            agent = Agent1(api_key="test-key")

            # Mock the methods
            agent.discovery = Mock(side_effect=lambda state: {
                **state,
                "current_phase": "discovery",
                "conversation_history": state.get("conversation_history", []) + [
                    {"role": "assistant", "content": "What's the function name?"}
                ]
            })

            agent.generate_artifacts = Mock(side_effect=lambda state: {
                **state,
                "current_phase": "review",
                "prd_content": "# Tool: test\nTest PRD",
                "json_schema": {"test": {"type": "function"}},
                "conversation_history": state.get("conversation_history", []) + [
                    {"role": "assistant", "content": "Here are the artifacts"}
                ]
            })

            agent.review = Mock(side_effect=lambda state, feedback: {
                **state,
                "prd_approved": "approve" in feedback.lower(),
                "current_phase": "approved" if "approve" in feedback.lower() else "review"
            })

            return agent

    def test_workflow_graph_creation(self, mock_agent_1):
        """Test workflow graph can be created and compiled."""
        workflow = ToolBuilderWorkflow(mock_agent_1)
        app = workflow.compile()

        assert app is not None

    def test_workflow_nodes_exist(self, mock_agent_1):
        """Test all expected nodes exist in workflow."""
        workflow = ToolBuilderWorkflow(mock_agent_1)

        # Check nodes were added
        assert "agent_1_discovery" in workflow.graph.nodes
        assert "agent_1_generate" in workflow.graph.nodes
        assert "agent_1_review" in workflow.graph.nodes
        assert "complete_phase_1" in workflow.graph.nodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
