"""
Main CLI interface for the multi-agent tool builder system.

This provides an interactive command-line interface for users to create tools
through the multi-agent workflow.
"""

import sys
import os
from typing import Optional
import json
from datetime import datetime

from langgraph.types import Command

from multi_agent_system.state import create_initial_state, ToolBuilderState
from multi_agent_system.graph import create_app


class ToolBuilderCLI:
    """Interactive CLI for the tool builder system."""

    def __init__(self):
        self.app = create_app()
        self.thread_id: Optional[str] = None
        self.state: Optional[ToolBuilderState] = None

    def start_session(self, user_input: str):
        """
        Start a new tool building session.

        Args:
            user_input: The user's initial request/description
        """
        # Generate unique thread ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.thread_id = f"tool_builder_{timestamp}"

        # Create initial state
        initial_state = create_initial_state(user_input)

        print(f"\n{'='*60}")
        print(f"🚀 Starting Tool Builder Session")
        print(f"{'='*60}")
        print(f"Thread ID: {self.thread_id}")
        print(f"Initial Request: {user_input}")
        print(f"{'='*60}\n")

        # Run the graph
        config = {"configurable": {"thread_id": self.thread_id}}

        try:
            # Stream events from the graph
            for event in self.app.stream(initial_state, config, stream_mode="values"):
                self._handle_event(event)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    def resume_session(self, user_input: str):
        """
        Resume an existing session with user input.

        Args:
            user_input: The user's response/feedback
        """
        if not self.thread_id:
            print("❌ No active session. Use start_session() first.")
            return

        print(f"\n{'='*60}")
        print(f"📝 Resuming Session: {self.thread_id}")
        print(f"{'='*60}\n")

        config = {"configurable": {"thread_id": self.thread_id}}

        try:
            # Resume with user input
            for event in self.app.stream(
                Command(resume=user_input),
                config,
                stream_mode="values"
            ):
                self._handle_event(event)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    def _handle_event(self, event: dict):
        """
        Handle events from the graph stream.

        Args:
            event: Event dictionary from LangGraph
        """
        # Extract state from event
        if isinstance(event, dict):
            current_agent = event.get("current_agent", "unknown")
            current_phase = event.get("current_phase", "unknown")

            # Print status
            print(f"\n🤖 Agent: {current_agent} | Phase: {current_phase}")

            # Print latest message if available
            conversation = event.get("conversation_history", [])
            if conversation:
                latest = conversation[-1]
                if latest["role"] == "assistant":
                    print(f"\n{latest['content']}\n")

            # Store state for reference
            self.state = event

    def save_session_state(self, filepath: Optional[str] = None):
        """
        Save the current session state to a file.

        Args:
            filepath: Optional custom filepath. Defaults to .agent_state/{thread_id}.json
        """
        if not self.state or not self.thread_id:
            print("❌ No active session to save.")
            return

        if filepath is None:
            state_dir = os.path.join(os.getcwd(), ".agent_state")
            os.makedirs(state_dir, exist_ok=True)
            filepath = os.path.join(state_dir, f"{self.thread_id}.json")

        with open(filepath, 'w') as f:
            json.dump(self.state, f, indent=2)

        print(f"💾 Session state saved to: {filepath}")


def interactive_mode():
    """
    Run the CLI in interactive mode.

    Guides the user through creating a tool step by step.
    """
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║     🛠️  Multi-Agent Tool Builder System 🛠️               ║
║                                                            ║
║     Automated tool creation from requirements to           ║
║     implementation using specialized AI agents             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)

    cli = ToolBuilderCLI()

    # Get initial user input
    print("Let's create a new tool! What would you like to build?")
    print("(Describe the tool's purpose or goal)\n")
    user_input = input("Your request: ").strip()

    if not user_input:
        print("❌ No input provided. Exiting.")
        return

    # Start session
    cli.start_session(user_input)

    # Interactive loop for continued conversation
    while True:
        print("\n" + "="*60)
        user_response = input("\nYour response (or 'quit' to exit, 'save' to save state): ").strip()

        if user_response.lower() == 'quit':
            print("\n👋 Exiting. Session state preserved.")
            cli.save_session_state()
            break
        elif user_response.lower() == 'save':
            cli.save_session_state()
            continue
        elif not user_response:
            continue

        # Resume with user input
        cli.resume_session(user_response)

        # Check if workflow completed
        if cli.state and cli.state.get("current_phase") == "complete":
            print("\n✅ Tool building complete!")
            print(f"   PRD saved: PRDs/{cli.state.get('function_name')}.md")
            print(f"   Registry updated: tool_registry.json")
            cli.save_session_state()
            break


def main():
    """Main entry point for CLI."""
    if len(sys.argv) > 1:
        # Command line mode with argument
        user_input = " ".join(sys.argv[1:])
        cli = ToolBuilderCLI()
        cli.start_session(user_input)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
