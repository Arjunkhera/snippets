"""
Example usage of the Query Planner.

Demonstrates:
- Single-step planning
- Multi-step planning
- Plan inspection before execution
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path to import search_agent
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from search_agent.core.state import SearchAgentState
from search_agent.nodes.planner import query_planner_node
from search_agent.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_plan(plan_dict: dict, query: str):
    """Pretty print a query plan."""
    print("\n" + "=" * 80)
    print(f"Query: {query}")
    print("=" * 80)
    print(f"\nPlan Type: {plan_dict['plan_type']}")
    print(f"Total Steps: {plan_dict['total_steps']}")
    print(f"\nReasoning:\n{plan_dict['reasoning']}")
    print(f"\nExecution Plan:")
    for step in plan_dict['steps']:
        depends = f" (depends on step {step['depends_on_step']})" if step.get('depends_on_step') else ""
        print(f"  Step {step['step']}: {step['description']}{depends}")
    print("=" * 80)


def example_single_step_planning():
    """Demonstrate single-step query planning."""
    print("\n" + "#" * 80)
    print("# Example 1: Single-Step Query Planning")
    print("#" * 80)

    # Example single-step queries
    single_step_queries = [
        "Find all W2 documents",
        "Show folders at root level",
        "List all documents created last week",
        "Find documents where tax year is 2024",
    ]

    for query in single_step_queries:
        state: SearchAgentState = {
            "user_query": query,
            "intent": "search",
            "conversation_id": "example-single",
            "conversation_history": [],
        }

        try:
            result = query_planner_node(state)

            if "error" in result:
                print(f"\n❌ Error for query '{query}':")
                print(f"   {result['error']}")
            else:
                print_plan(result["query_plan"], query)

        except Exception as e:
            print(f"\n❌ Exception for query '{query}': {e}")


def example_multi_step_planning():
    """Demonstrate multi-step query planning."""
    print("\n" + "#" * 80)
    print("# Example 2: Multi-Step Query Planning")
    print("#" * 80)

    # Example multi-step queries
    multi_step_queries = [
        "List documents in Tax Documents folder",
        "Show me subfolders under Business",
        "Which folder contains Invoice_2024.pdf?",
        "Show other documents in the same folder as Report.pdf",
        "Show W2 documents in Tax Documents folder",
    ]

    for query in multi_step_queries:
        state: SearchAgentState = {
            "user_query": query,
            "intent": "search",
            "conversation_id": "example-multi",
            "conversation_history": [],
        }

        try:
            result = query_planner_node(state)

            if "error" in result:
                print(f"\n❌ Error for query '{query}':")
                print(f"   {result['error']}")
            else:
                print_plan(result["query_plan"], query)

        except Exception as e:
            print(f"\n❌ Exception for query '{query}': {e}")


def example_plan_inspection():
    """Demonstrate plan inspection before execution."""
    print("\n" + "#" * 80)
    print("# Example 3: Plan Inspection Before Execution")
    print("#" * 80)

    query = "List documents in Tax Documents folder"

    print(f"\nQuery: {query}")
    print("\nStep 1: Generate Plan")
    print("-" * 80)

    state: SearchAgentState = {
        "user_query": query,
        "intent": "search",
        "conversation_id": "example-inspect",
        "conversation_history": [],
    }

    try:
        result = query_planner_node(state)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return

        plan = result["query_plan"]

        print(f"✓ Plan generated successfully")
        print(f"  Type: {plan['plan_type']}")
        print(f"  Steps: {plan['total_steps']}")

        print("\nStep 2: Inspect Plan Details")
        print("-" * 80)

        print("\nReasoning:")
        print(f"  {plan['reasoning']}")

        print("\nExecution Steps:")
        for step in plan['steps']:
            print(f"  [{step['step']}] {step['description']}")
            if step.get('depends_on_step'):
                print(f"      → Requires result from step {step['depends_on_step']}")

        print("\nStep 3: Analyze Plan")
        print("-" * 80)

        # Analyze the plan
        if plan['plan_type'] == 'single_step':
            print("  ℹ️  This query can be executed in a single step")
            print("  ℹ️  No intermediate results needed")
        else:
            print("  ℹ️  This query requires multiple steps")
            print(f"  ℹ️  Step 1 will execute first and provide data for subsequent steps")

            # Check dependencies
            dependent_steps = [s for s in plan['steps'] if s.get('depends_on_step')]
            if dependent_steps:
                print(f"  ℹ️  {len(dependent_steps)} step(s) depend on previous results")

        print("\nStep 4: Ready for Execution")
        print("-" * 80)
        print("  ✓ Plan validated")
        print("  ✓ Dependencies identified")
        print("  ✓ Ready to pass to executor node")

        print(f"\nState after planning:")
        print(f"  current_step: {result['current_step']}")
        print(f"  total_steps: {result['total_steps']}")

    except Exception as e:
        print(f"❌ Exception: {e}")


def example_comparative_analysis():
    """Compare single-step vs multi-step planning for similar queries."""
    print("\n" + "#" * 80)
    print("# Example 4: Comparative Analysis - Single vs Multi-Step")
    print("#" * 80)

    query_pairs = [
        (
            "Find all documents",
            "Find documents in Archive folder"
        ),
        (
            "List folders where parent ID is root",
            "List subfolders in Projects folder"
        ),
    ]

    for single_query, multi_query in query_pairs:
        print("\n" + "-" * 80)
        print("Comparing similar queries:")
        print(f"  A) {single_query}")
        print(f"  B) {multi_query}")
        print("-" * 80)

        for label, query in [("A", single_query), ("B", multi_query)]:
            state: SearchAgentState = {
                "user_query": query,
                "intent": "search",
                "conversation_id": f"example-compare-{label}",
                "conversation_history": [],
            }

            try:
                result = query_planner_node(state)

                if "error" not in result:
                    plan = result["query_plan"]
                    print(f"\n[{label}] {plan['plan_type']} ({plan['total_steps']} step{'s' if plan['total_steps'] > 1 else ''})")
                    print(f"    Reasoning: {plan['reasoning'][:100]}...")

            except Exception as e:
                print(f"\n[{label}] Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print(" Query Planner Examples")
    print("=" * 80)

    # Check if API key is set
    if not settings.ANTHROPIC_API_KEY:
        print("\n❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("   Set it before running these examples:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        return

    print(f"\n✓ Using model: {settings.LLM_MODEL}")
    print(f"✓ Max retries: {settings.MAX_RETRIES}")
    print(f"✓ Temperature: {settings.LLM_TEMPERATURE}")

    try:
        # Run examples
        example_single_step_planning()
        example_multi_step_planning()
        example_plan_inspection()
        example_comparative_analysis()

        print("\n" + "=" * 80)
        print(" Examples completed successfully!")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
