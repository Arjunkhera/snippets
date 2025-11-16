"""
Human-in-the-Loop (HITL) Clarification Example.

This example demonstrates how the agent handles ambiguous queries that require
user clarification. It shows the interrupt/resume mechanism in LangGraph.

Scenario:
- User query: "List documents in Tax folder"
- Multiple "Tax" folders exist
- Agent pauses and asks user to select which one
- User responds with selection
- Agent resumes and completes the query
"""

import logging
from pathlib import Path

from search_agent.graph import create_search_agent_graph
from search_agent.core.state import SearchAgentState

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def simulate_hitl_flow():
    """
    Simulate a complete HITL flow with clarification.

    This demonstrates:
    1. Initial query execution
    2. Graph interrupts when clarification needed
    3. User provides selection
    4. Graph resumes from checkpoint
    5. Execution completes
    """
    print("\n" + "=" * 80)
    print("HITL Clarification Flow Demonstration")
    print("=" * 80)

    # Create graph with checkpointing
    graph = create_search_agent_graph()

    # Initial query (will trigger clarification in multi-step scenario)
    user_query = "List documents in Tax Documents folder"
    thread_id = "hitl-demo-123"

    print(f"\n📝 User Query: {user_query}")
    print(f"🔗 Thread ID: {thread_id}")

    # Step 1: Initial execution
    print("\n" + "-" * 80)
    print("STEP 1: Initial Execution")
    print("-" * 80)

    initial_state: SearchAgentState = {
        "user_query": user_query,
        "conversation_id": thread_id,
        "conversation_history": []
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Execute graph
        result = graph.invoke(initial_state, config=config)

        # Check if clarification is needed
        if "pending_clarification" in result:
            print("\n⚠️  CLARIFICATION NEEDED")
            print("=" * 80)

            clarification = result["pending_clarification"]
            print(f"\nQuestion: {clarification['question']}")
            print(f"Type: {clarification['type']}")
            print("\nOptions:")

            for option in clarification["options"]:
                print(f"  {option['number']}. {option['display']}")

            # Step 2: User provides clarification
            print("\n" + "-" * 80)
            print("STEP 2: User Provides Clarification")
            print("-" * 80)

            # Simulate user selection
            user_selection = 1  # User selects option 1
            print(f"\n👤 User selects: {user_selection}")

            # Create update state with user's selection
            selected_option = clarification["options"][user_selection - 1]

            # Resume execution with clarification response
            print("\n" + "-" * 80)
            print("STEP 3: Resume Execution")
            print("-" * 80)

            # Update state with selected result
            resume_state = {
                **result,
                "step_results": {
                    **result.get("step_results", {}),
                    result["current_step"]: {
                        "result": selected_option["value"],
                        "execution_time_ms": 0
                    }
                },
                "pending_clarification": None,  # Clear clarification
                "current_step": result["current_step"] + 1  # Move to next step
            }

            # Resume graph
            final_result = graph.invoke(resume_state, config=config)

            print("\n✓ Execution resumed and completed!")

            if "response_message" in final_result:
                print("\n" + "=" * 80)
                print("FINAL RESPONSE")
                print("=" * 80)
                print(final_result["response_message"])

        else:
            # No clarification needed
            print("\n✓ Query completed without clarification")

            if "response_message" in result:
                print("\n" + "=" * 80)
                print("RESPONSE")
                print("=" * 80)
                print(result["response_message"])

    except Exception as e:
        logger.exception("Error in HITL flow")
        print(f"\n❌ Error: {e}")


def demonstrate_interrupt_mechanism():
    """
    Demonstrate the interrupt mechanism at a lower level.

    This shows how LangGraph checkpointing works with interrupts.
    """
    print("\n" + "=" * 80)
    print("LangGraph Interrupt Mechanism")
    print("=" * 80)

    print("""
The HITL interrupt mechanism works as follows:

1. **Graph Execution**: Node executes and updates state
   └─> state["pending_clarification"] = {...}

2. **Routing Check**: After node execution, routing function checks state
   └─> if state.get("pending_clarification"): return "executor"

3. **LangGraph Interrupt**: When state has pending_clarification
   └─> Graph automatically pauses (INTERRUPT)
   └─> State is saved to checkpointer
   └─> Returns current state to caller

4. **External System**: Presents clarification to user
   └─> User provides response (e.g., selects option 2)

5. **Resume Execution**: Application updates state with user's choice
   └─> state["pending_clarification"] = None
   └─> state["step_results"][current_step] = selected_value
   └─> graph.invoke(updated_state, config=same_thread_id)

6. **Graph Continues**: Execution resumes from checkpoint
   └─> Proceeds to next step with selected value
   └─> Completes execution

Key Points:
- Checkpointing preserves all state across interrupt
- Thread ID maintains conversation context
- Any node can trigger interrupt by setting pending_clarification
- External system controls when to resume
""")


def show_checkpoint_structure():
    """
    Show what gets saved in checkpoints.
    """
    print("\n" + "=" * 80)
    print("Checkpoint Structure")
    print("=" * 80)

    print("""
LangGraph checkpoints save complete state at each node:

Checkpoint {
    "thread_id": "hitl-demo-123",
    "checkpoint_id": "abc-123-xyz",
    "node": "executor",
    "state": {
        "user_query": "List documents in Tax folder",
        "intent": "search",
        "query_plan": {...},
        "current_step": 1,
        "total_steps": 2,
        "step_results": {
            1: {
                "result": {...},  # Step 1 result
                "execution_time_ms": 150
            }
        },
        "pending_clarification": {
            "type": "multiple_choice",
            "question": "I found 3 folders...",
            "options": [...]
        }
    }
}

Resume Process:
1. Load checkpoint by thread_id
2. User provides clarification response
3. Update state with user's selection
4. Clear pending_clarification
5. Invoke graph with updated state
6. Graph continues from where it left off
""")


def main():
    """
    Run all HITL demonstrations.
    """
    print("\n" + "█" * 80)
    print("Human-in-the-Loop (HITL) Clarification - Complete Guide")
    print("█" * 80)

    # 1. Demonstrate the interrupt mechanism
    demonstrate_interrupt_mechanism()

    # 2. Show checkpoint structure
    show_checkpoint_structure()

    # 3. Simulate actual HITL flow
    print("\n" + "█" * 80)
    print("Live HITL Flow Simulation")
    print("█" * 80)

    simulate_hitl_flow()

    print("\n" + "█" * 80)
    print("HITL Demonstration Complete")
    print("█" * 80)

    print("""
Summary:
- HITL enables agent to ask clarifying questions
- LangGraph interrupts provide pause/resume capability
- Checkpointing preserves state across interrupts
- Thread IDs maintain conversation context
- External system controls presentation and response collection

Use Cases:
- Multiple matching entities (folders, documents)
- Ambiguous references
- Confirmation requests
- Parameter validation

Next Steps:
- Integrate with UI for user interaction
- Add timeout handling for pending clarifications
- Implement clarification history tracking
- Support multi-turn clarification dialogs
""")


if __name__ == "__main__":
    main()
