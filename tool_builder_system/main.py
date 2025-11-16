"""
Main entry point for the Tool Builder System.

Phase 1: Interactive CLI for Agent 1 (Requirements Architect)
"""

import os
import sys
from pathlib import Path
from langgraph.checkpoint.memory import MemorySaver

from tool_builder_system import (
    create_initial_state,
    Agent1,
    ToolBuilderWorkflow,
    StatePersistence
)


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 80 + "\n")


def print_assistant_message(message: str):
    """Print an assistant message with formatting."""
    print(f"\n🤖 Agent 1 (Requirements Architect):\n")
    print(message)
    print_separator()


def print_system_message(message: str):
    """Print a system message with formatting."""
    print(f"\n📋 System:\n")
    print(message)
    print_separator()


def run_interactive_session():
    """
    Run an interactive CLI session with the tool builder system.

    Phase 1: Agent 1 requirements gathering and PRD generation.
    """
    print_system_message("""
Multi-Agent Tool Builder System - Phase 1
==========================================

This system will help you create Python tools through an interactive process:

Phase 1 (Current): Requirements Architect
- Interactive requirements gathering
- PRD and JSON schema generation
- User review and approval

Phase 2 (Coming): Implementation Specialist
- Code generation based on PRD
- Implementation review

Let's start by understanding what tool you want to create!
""")

    # Get initial user input
    print("👤 You:")
    user_input = input("What tool would you like to create? ").strip()

    if not user_input:
        print("No input provided. Exiting.")
        return

    # Initialize components
    print_system_message("Initializing Agent 1...")

    agent_1 = Agent1()
    workflow = ToolBuilderWorkflow(agent_1)

    # Use memory checkpointer for this session
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    # Create initial state
    state = create_initial_state(user_input)

    # Thread configuration
    thread_id = "tool_builder_session_1"
    config = {"configurable": {"thread_id": thread_id}}

    # Initialize state persistence
    persistence = StatePersistence(
        base_path=str(Path(__file__).parent / ".agent_state")
    )

    print_system_message("Starting conversation with Agent 1...")

    try:
        # Main conversation loop
        iteration = 0
        max_iterations = 50  # Prevent infinite loops

        while iteration < max_iterations:
            iteration += 1

            # Run workflow until interrupt or completion
            events = list(app.stream(state, config, stream_mode="values"))

            if not events:
                print_system_message("Workflow completed!")
                break

            # Get latest state
            latest_state = events[-1]

            # Save state
            if latest_state.get("function_name"):
                persistence.save_state(latest_state, thread_id)

            # Get last assistant message
            conversation = latest_state.get("conversation_history", [])
            if conversation and conversation[-1]["role"] == "assistant":
                last_message = conversation[-1]["content"]
                print_assistant_message(last_message)

                # Check if we're in review phase (approval gate)
                current_phase = latest_state.get("current_phase", "")

                if current_phase == "review":
                    # User needs to approve or provide feedback
                    print("\n👤 You (type your response, 'approve' to proceed, or 'quit' to exit):")
                    user_feedback = input().strip()

                    if user_feedback.lower() in ["quit", "exit", "q"]:
                        print_system_message("Exiting session. State has been saved.")
                        break

                    # Update state with user feedback
                    latest_state = agent_1.review(latest_state, user_feedback)
                    state = latest_state

                    # Save updated state
                    if latest_state.get("function_name"):
                        persistence.save_state(latest_state, thread_id)

                    # Check if approved
                    if latest_state.get("prd_approved"):
                        print_system_message("""
🎉 PRD Approved!

Phase 1 is complete. The requirements have been documented and approved.

Summary:
- Function Name: {function_name}
- PRD Content: {prd_status}
- JSON Schema: {schema_status}

State saved to: .agent_state/{thread_id}.json

Next Steps (Phase 2):
- Agent 2 will implement the code based on the PRD
- You will review the implementation
- Agent 3 will write tests
- Agent 4 will publish to pip

[Phase 2 implementation coming soon]
""".format(
                            function_name=latest_state.get("function_name", "N/A"),
                            prd_status="✓ Generated" if latest_state.get("prd_content") else "✗ Missing",
                            schema_status="✓ Generated" if latest_state.get("json_schema") else "✗ Missing",
                            thread_id=thread_id
                        ))
                        break

                elif current_phase == "discovery":
                    # Agent is asking questions, get user response
                    print("\n👤 You:")
                    user_response = input().strip()

                    if user_response.lower() in ["quit", "exit", "q"]:
                        print_system_message("Exiting session. State has been saved.")
                        break

                    # Add user response to conversation
                    latest_state["conversation_history"].append({
                        "role": "user",
                        "content": user_response
                    })

                    state = latest_state

                elif current_phase == "completed":
                    # Phase 1 completed
                    break

            else:
                # No assistant message, might be end
                if latest_state.get("current_phase") == "completed":
                    break

        if iteration >= max_iterations:
            print_system_message("Maximum iterations reached. Please restart the session.")

    except KeyboardInterrupt:
        print_system_message("\n\nSession interrupted. State has been saved.")
        if state.get("function_name"):
            persistence.save_state(state, thread_id)

    except Exception as e:
        print_system_message(f"\n\nError occurred: {str(e)}")
        print("Saving state before exit...")
        if state.get("function_name"):
            persistence.save_state(state, thread_id)
        raise


def main():
    """Main entry point."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Please set it before running: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)

    run_interactive_session()


if __name__ == "__main__":
    main()
