"""
Debug test to see what's happening with the state.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Disable LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from multi_agent_system.state import create_initial_state
from multi_agent_system.graph import create_app
from langgraph.types import Command


def main():
    print("="*60)
    print("Debug Test")
    print("="*60)

    app = create_app()
    initial_state = create_initial_state("Create a tool to parse CSV files")

    config = {"configurable": {"thread_id": "debug_001"}}

    print("\nInitial state conversation:")
    print(f"  Messages: {len(initial_state['conversation_history'])}")
    for msg in initial_state['conversation_history']:
        print(f"  - {msg['role']}: {msg['content'][:80]}...")

    print("\n[Step 1] Running first iteration...")

    event_count = 0
    for event in app.stream(initial_state, config, stream_mode="values"):
        event_count += 1
        print(f"\nEvent {event_count}:")
        print(f"  Current agent: {event.get('current_agent')}")
        print(f"  Current phase: {event.get('current_phase')}")
        print(f"  Conversation messages: {len(event.get('conversation_history', []))}")

        conversation = event.get('conversation_history', [])
        if conversation:
            last_msg = conversation[-1]
            print(f"  Last message from: {last_msg['role']}")
            print(f"  Content: {last_msg['content'][:150]}...")

        # Stop after a few events to see what's happening
        if event_count >= 3:
            print("\n(Stopping after 3 events)")
            break

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
