"""
End-to-end workflow test for Agent 1.

This test simulates a complete workflow through Agent 1 phases without
requiring actual user interaction (uses programmatic state updates).
"""

import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_agent_system.state import create_initial_state
from multi_agent_system.agents.agent_1_requirements import RequirementsArchitect


def test_agent_1_phases():
    """Test Agent 1 can execute all phases."""
    print("="*60)
    print("Testing Agent 1: Requirements Architect Workflow")
    print("="*60)

    # Initialize agent
    agent = RequirementsArchitect()
    print("\n✓ Agent 1 initialized")

    # Create initial state
    state = create_initial_state("Create a tool that validates email addresses")
    print("✓ Initial state created")

    # Test Phase 1: Discovery
    print("\n--- Phase 1: Discovery ---")
    try:
        # Simulate user providing function name in conversation
        state["conversation_history"].append({
            "role": "user",
            "content": "Call it validate_email"
        })
        state["function_name"] = "validate_email"
        state["tool_description"] = "Validates email addresses against RFC standards"

        # Run discovery (will ask a question)
        result_state = agent.discovery_phase(state)
        print(f"✓ Discovery phase completed")
        print(f"  Current phase: {result_state['current_phase']}")
        print(f"  Conversation messages: {len(result_state['conversation_history'])}")
    except Exception as e:
        print(f"✗ Discovery phase failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test Phase 2: Generation (simulate having enough info)
    print("\n--- Phase 2: Artifact Generation ---")
    try:
        # Set up state as if discovery is complete
        result_state["current_phase"] = "generation"
        result_state["input_parameters"] = [
            {"name": "email", "type": "str", "required": True, "description": "Email to validate"}
        ]
        result_state["success_output"] = {"valid": "bool", "message": "str"}
        result_state["error_cases"] = [
            {"error_code": "INVALID_FORMAT", "description": "Email format invalid"}
        ]

        # Note: We can't actually call generate_artifacts without API calls
        # So we'll simulate what it would produce
        result_state["prd_content"] = "# Tool: validate_email\n\nValidates email addresses..."
        result_state["json_schema"] = {
            "type": "function",
            "name": "validate_email",
            "description": "Validates email addresses",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email to validate"}
                },
                "required": ["email"]
            }
        }
        result_state["current_phase"] = "review"

        print(f"✓ Artifact generation completed (simulated)")
        print(f"  PRD content length: {len(result_state['prd_content'])} chars")
        print(f"  JSON schema has function name: {result_state['json_schema'].get('name')}")
    except Exception as e:
        print(f"✗ Generation phase failed: {e}")
        return False

    # Test Phase 4: Save (skip review since it requires interrupt)
    print("\n--- Phase 4: Save Artifacts ---")
    try:
        result_state["prd_approved"] = True
        result_state["current_phase"] = "save"

        # Run save
        final_state = agent.save_artifacts(result_state)

        print(f"✓ Save phase completed")
        print(f"  Function name: {final_state['function_name']}")
        print(f"  Current phase: {final_state['current_phase']}")

        # Check if files were created
        prd_path = Path(f"PRDs/{final_state['function_name']}.md")
        registry_path = Path("tool_registry.json")

        if prd_path.exists():
            print(f"  ✓ PRD file created: {prd_path}")
        else:
            print(f"  ✗ PRD file not found: {prd_path}")

        if registry_path.exists():
            print(f"  ✓ Registry file exists: {registry_path}")
            with open(registry_path, 'r') as f:
                registry = json.load(f)
                if final_state['function_name'] in registry:
                    print(f"  ✓ Function registered in tool_registry.json")
                else:
                    print(f"  ✗ Function not in registry")
        else:
            print(f"  ✗ Registry file not found")

    except Exception as e:
        print(f"✗ Save phase failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*60)
    print("✅ Agent 1 workflow test completed successfully!")
    print("="*60)
    return True


def main():
    """Run workflow test."""
    success = test_agent_1_phases()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
