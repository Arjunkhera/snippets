"""
End-to-End Integration Example for Search Agent LangGraph Workflow.

This example demonstrates the complete workflow from user query to final response:
1. Query Classification
2. Query Planning
3. Query Execution (with loop for multi-step)
4. Response Formatting

Run this file to see the search agent in action with various query types.
"""

import json
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


def run_query(graph, user_query: str, thread_id: str):
    """
    Run a query through the complete workflow.

    Args:
        graph: Compiled LangGraph
        user_query: User's natural language query
        thread_id: Unique thread ID for checkpointing

    Returns:
        Final state after execution
    """
    print("\n" + "=" * 80)
    print(f"Query: {user_query}")
    print("=" * 80)

    # Create initial state
    initial_state: SearchAgentState = {
        "user_query": user_query,
        "conversation_id": thread_id,
        "conversation_history": []
    }

    # Execute graph
    try:
        result = graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": thread_id}}
        )

        # Display results
        print("\n--- CLASSIFICATION ---")
        print(f"Intent: {result.get('intent', 'N/A')}")
        print(f"Confidence: {result.get('classification_confidence', 'N/A')}")
        print(f"Reasoning: {result.get('classification_reasoning', 'N/A')}")

        if result.get("intent") == "search":
            print("\n--- PLANNING ---")
            query_plan = result.get("query_plan", {})
            print(f"Plan Type: {query_plan.get('plan_type', 'N/A')}")
            print(f"Total Steps: {query_plan.get('total_steps', 'N/A')}")
            print(f"Reasoning: {query_plan.get('reasoning', 'N/A')}")

            if query_plan.get("steps"):
                print("\nSteps:")
                for step in query_plan["steps"]:
                    deps = f" (depends on step {step.get('depends_on_step')})" if step.get('depends_on_step') else ""
                    print(f"  {step['step']}. {step['description']}{deps}")

            print("\n--- EXECUTION ---")
            step_results = result.get("step_results", {})
            print(f"Steps Executed: {len(step_results)}")

            for step_num, step_data in step_results.items():
                print(f"\nStep {step_num}:")
                print(f"  Execution Time: {step_data.get('execution_time_ms', 0)}ms")
                print(f"  Result Count: {step_data.get('result_count', 0)}")

        print("\n--- RESPONSE ---")
        if "response_message" in result:
            print(result["response_message"])
        else:
            print("No response message (workflow may have terminated early)")

        if "error" in result:
            print(f"\n❌ Error: {result['error']}")

        if "metadata" in result:
            print(f"\n--- METADATA ---")
            print(json.dumps(result["metadata"], indent=2))

        return result

    except Exception as e:
        logger.exception("Error executing graph")
        print(f"\n❌ Execution failed: {e}")
        return None


def main():
    """
    Main function to demonstrate complete workflow with various queries.
    """
    print("\n" + "█" * 80)
    print("Search Agent - Complete Workflow Demonstration")
    print("█" * 80)

    # Create graph
    print("\n📊 Creating LangGraph workflow...")
    graph = create_search_agent_graph()
    print("✓ Graph created successfully!\n")

    # Example 1: Single-step search query
    print("\n" + "▼" * 80)
    print("EXAMPLE 1: Single-Step Search Query")
    print("▼" * 80)
    run_query(
        graph,
        user_query="Find all documents where document type is W2",
        thread_id="example-1"
    )

    # Example 2: Multi-step query (folder name resolution)
    print("\n" + "▼" * 80)
    print("EXAMPLE 2: Multi-Step Query (Folder Name Resolution)")
    print("▼" * 80)
    run_query(
        graph,
        user_query="List documents in Tax Documents folder",
        thread_id="example-2"
    )

    # Example 3: Multi-step query (document name to folder search)
    print("\n" + "▼" * 80)
    print("EXAMPLE 3: Multi-Step Query (Document Location)")
    print("▼" * 80)
    run_query(
        graph,
        user_query="Which folder contains invoice.pdf?",
        thread_id="example-3"
    )

    # Example 4: Move operation (not implemented)
    print("\n" + "▼" * 80)
    print("EXAMPLE 4: Move Operation (Not Yet Implemented)")
    print("▼" * 80)
    run_query(
        graph,
        user_query="Move report.pdf to Archive folder",
        thread_id="example-4"
    )

    # Example 5: Help query
    print("\n" + "▼" * 80)
    print("EXAMPLE 5: Help Query")
    print("▼" * 80)
    run_query(
        graph,
        user_query="How does this search system work?",
        thread_id="example-5"
    )

    # Example 6: Complex multi-step query
    print("\n" + "▼" * 80)
    print("EXAMPLE 6: Complex Multi-Step Query (Owner-Based Search)")
    print("▼" * 80)
    run_query(
        graph,
        user_query="Find all documents owned by John Smith in the Business folder",
        thread_id="example-6"
    )

    print("\n" + "█" * 80)
    print("Demonstration Complete!")
    print("█" * 80)
    print("\nKey Observations:")
    print("  - Classification correctly identifies search vs. other intents")
    print("  - Planner performs gap analysis for multi-step requirements")
    print("  - Executor loops through steps, passing results between them")
    print("  - Formatter presents user-friendly output")
    print("\nNext Steps:")
    print("  - Phase 5: Add error handling and HITL clarifications")
    print("  - Integration: Connect to real Elasticsearch service")
    print("  - Testing: End-to-end tests with mock ES data")
    print("█" * 80 + "\n")


if __name__ == "__main__":
    main()
