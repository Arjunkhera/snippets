"""
Quick test to verify the interrupt mechanism works correctly in discovery phase.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_agent_system.state import create_initial_state
from multi_agent_system.graph import create_app
from langgraph.types import Command


def test_discovery_interrupts():
    """Test that discovery phase properly interrupts for user input."""
    print("="*60)
    print("Testing Discovery Phase Interrupt Mechanism")
    print("="*60)

    app = create_app()
    initial_state = create_initial_state(
        "I want to create a tool that validates JSON schemas"
    )

    config = {"configurable": {"thread_id": "interrupt_test_001"}}

    print("\n[Step 1] Starting workflow - should ask first question and pause")

    # This should execute discovery, agent asks a question, and PAUSE
    events = list(app.stream(initial_state, config, stream_mode="values"))

    if len(events) > 0:
        last_state = events[-1]
        conversation = last_state.get("conversation_history", [])

        print(f"\n✓ Workflow paused after {len(events)} event(s)")
        print(f"✓ Conversation has {len(conversation)} message(s)")

        if conversation:
            last_msg = conversation[-1]
            print(f"\n✓ Last message role: {last_msg['role']}")
            print(f"✓ Last message preview: {last_msg['content'][:150]}...")

            if last_msg['role'] == 'assistant':
                print("\n✅ SUCCESS: Agent asked a question and paused!")
                print("   (Waiting for user input - this is correct behavior)")
            else:
                print("\n⚠️  WARNING: Expected assistant message, got:", last_msg['role'])

        # Check that we can resume
        print("\n[Step 2] Testing resume with user input")
        user_response = "validate_json_schema"

        resume_events = list(app.stream(
            Command(resume=user_response),
            config,
            stream_mode="values"
        ))

        if len(resume_events) > 0:
            resumed_state = resume_events[-1]
            new_conversation = resumed_state.get("conversation_history", [])

            print(f"\n✓ Workflow resumed")
            print(f"✓ Conversation now has {len(new_conversation)} message(s)")

            # Check if user response was added
            user_messages = [m for m in new_conversation if m['role'] == 'user']
            if len(user_messages) >= 2:  # Initial + our response
                print(f"✓ User response was added to conversation")
                print(f"\n✅ SUCCESS: Interrupt and resume working correctly!")
                return True

    print("\n⚠️  Test incomplete - see output above")
    return False


def main():
    """Run interrupt test."""
    print("\nThis test verifies that the discovery phase properly pauses")
    print("and waits for user input instead of auto-answering.\n")

    try:
        success = test_discovery_interrupts()

        print("\n" + "="*60)
        if success:
            print("✅ Interrupt mechanism validated!")
            print("   The agent will now wait for user input properly.")
        else:
            print("⚠️  Check the output above for details")
        print("="*60)

        return 0 if success else 1

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
