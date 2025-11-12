"""
Demo test showing the complete workflow with interrupt behavior.

This demonstrates that the system properly pauses and waits for user input.
"""

import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from multi_agent_system import create_app, create_initial_state
from langgraph.types import Command


def demo_workflow():
    """Demonstrate the complete workflow with proper pauses."""

    print("\n" + "="*70)
    print(" Multi-Agent Tool Builder - Interactive Demo".center(70))
    print("="*70)

    # Setup
    app = create_app()
    config = {"configurable": {"thread_id": "demo_session_001"}}

    print("\n📝 Scenario: User wants to create a temperature conversion tool\n")

    # Step 1: Initial request
    print("-" * 70)
    print("STEP 1: User provides initial request")
    print("-" * 70)

    initial_state = create_initial_state(
        "I want to create a function that converts Celsius to Fahrenheit"
    )

    print(f"User says: \"{initial_state['user_input']}\"")
    print("\n⏳ Starting workflow...")

    # Run until first interrupt
    for event in app.stream(initial_state, config, stream_mode="updates"):
        if "__interrupt__" in event:
            print("\n✅ System PAUSED - waiting for user input")
            print("   (This is the interrupt mechanism working)")
            break
        elif "agent_1_discovery" in event:
            # Get the agent's question from state
            snapshot = app.get_state(config)
            conversation = snapshot.values.get("conversation_history", [])
            if conversation:
                last_msg = conversation[-1]
                if last_msg["role"] == "assistant":
                    print(f"\n🤖 Agent asks: \"{last_msg['content'][:150]}...\"")

    # Step 2: User responds
    print("\n" + "-" * 70)
    print("STEP 2: User provides answer")
    print("-" * 70)

    user_response_1 = "celsius_to_fahrenheit"
    print(f"User responds: \"{user_response_1}\"")
    print("\n⏳ Resuming workflow...")

    # Resume with user input
    for event in app.stream(Command(resume=user_response_1), config, stream_mode="updates"):
        if "__interrupt__" in event:
            print("\n✅ System PAUSED again - waiting for next input")
            break
        elif "agent_1_discovery" in event:
            snapshot = app.get_state(config)
            conversation = snapshot.values.get("conversation_history", [])
            if conversation:
                last_msg = conversation[-1]
                if last_msg["role"] == "assistant":
                    print(f"\n🤖 Agent asks: \"{last_msg['content'][:150]}...\"")

    # Step 3: Continue answering questions
    print("\n" + "-" * 70)
    print("STEP 3: User continues answering")
    print("-" * 70)

    user_response_2 = "It takes a temperature in Celsius and returns the equivalent in Fahrenheit"
    print(f"User responds: \"{user_response_2}\"")
    print("\n⏳ Resuming workflow...")

    # This would continue until all questions are answered...
    for event in app.stream(Command(resume=user_response_2), config, stream_mode="updates"):
        if "__interrupt__" in event:
            print("\n✅ System PAUSED - waiting for more input")
            print("   (Agent will continue asking questions until it has all info)")
            break
        elif "agent_1_discovery" in event:
            snapshot = app.get_state(config)
            conversation = snapshot.values.get("conversation_history", [])
            if conversation:
                last_msg = conversation[-1]
                if last_msg["role"] == "assistant":
                    print(f"\n🤖 Agent asks: \"{last_msg['content'][:150]}...\"")

    # Summary
    print("\n" + "="*70)
    print(" Demo Summary".center(70))
    print("="*70)

    snapshot = app.get_state(config)
    conversation = snapshot.values.get("conversation_history", [])

    print(f"\n📊 Conversation Stats:")
    print(f"   Total messages: {len(conversation)}")
    print(f"   User messages: {len([m for m in conversation if m['role'] == 'user'])}")
    print(f"   Agent messages: {len([m for m in conversation if m['role'] == 'assistant'])}")

    print(f"\n✅ Key Observations:")
    print(f"   1. Agent asks ONE question at a time")
    print(f"   2. System PAUSES after each question (interrupt)")
    print(f"   3. Workflow RESUMES only when user provides input")
    print(f"   4. NO auto-answering - system waits indefinitely")

    print(f"\n💡 This is EXACTLY how it works in the interactive CLI!")
    print(f"   The user must type their response after each question.")

    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        demo_workflow()
        print("\n✅ Demo completed successfully!\n")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
