"""
LangGraph workflow assembly for the Search/List Agent.

This module creates the complete StateGraph with all nodes and routing logic.

Graph Structure:
    START -> Classifier -> Planner -> Executor (loop) -> Formatter -> END

Routing:
- Classifier: routes to planner if "search", else to other handlers or end
- Planner: always routes to executor
- Executor: loops back to itself for multi-step, clarifications, retries;
           routes to formatter when complete or on fatal error
- Formatter: always routes to END
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from search_agent.core.state import SearchAgentState
from search_agent.nodes import (
    query_classifier_node,
    query_planner_node,
    query_executor_node,
    response_formatter_node,
)
from search_agent.config import settings

# Set up logging
logger = logging.getLogger(__name__)


def route_after_classifier(state: SearchAgentState) -> Literal["planner", "end"]:
    """
    Route after classification based on intent.

    Args:
        state: Current state with intent

    Returns:
        Next node name: "planner" for search queries, "end" for others

    Note:
        Future: Will route to "move_handler", "delete_handler", "create_handler"
        when those agents are implemented.
    """
    intent = state.get("intent", "other")

    logger.info(f"Routing after classification: intent={intent}")

    if intent == "search":
        return "planner"
    elif intent == "move":
        # Future: return "move_handler"
        logger.warning("Move operations not yet implemented")
        return "end"
    elif intent == "delete":
        # Future: return "delete_handler"
        logger.warning("Delete operations not yet implemented")
        return "end"
    elif intent == "create":
        # Future: return "create_handler"
        logger.warning("Create operations not yet implemented")
        return "end"
    else:  # "other"
        return "end"


def route_after_planner(state: SearchAgentState) -> Literal["executor"]:
    """
    Route after planning.

    Args:
        state: Current state with query_plan

    Returns:
        Always returns "executor"

    Note:
        Planner always proceeds to executor. Executor handles both
        single-step and multi-step plans.
    """
    logger.info("Routing to executor")
    return "executor"


def route_after_executor(
    state: SearchAgentState
) -> Literal["executor", "formatter"]:
    """
    Route after executor - handles loop logic.

    The executor is a loop node that can:
    - Loop back to itself for next step
    - Loop back for retry on errors
    - Interrupt for clarification (handled by LangGraph)
    - Proceed to formatter when complete

    Args:
        state: Current state

    Returns:
        "executor" to loop back, "formatter" to proceed
    """
    # Check for pending clarification (HITL interrupt)
    if state.get("pending_clarification"):
        logger.info("Pending clarification - will interrupt")
        # Note: LangGraph will automatically interrupt here
        # When resumed after user response, will come back to executor
        return "executor"

    # Check for fatal error
    if state.get("error"):
        logger.warning(f"Error in executor: {state['error']}")
        return "formatter"

    # Check if more steps remain
    current_step = state.get("current_step", 0)
    total_steps = state.get("total_steps", 0)

    if current_step < total_steps:
        logger.info(f"More steps remaining ({current_step}/{total_steps}) - looping back")
        return "executor"

    # All steps complete
    logger.info("All steps complete - proceeding to formatter")
    return "formatter"


def route_after_formatter(state: SearchAgentState) -> Literal["__end__"]:
    """
    Route after formatting.

    Args:
        state: Current state with response_message

    Returns:
        Always returns END
    """
    logger.info("Workflow complete")
    return END


def create_search_agent_graph(checkpointer=None) -> StateGraph:
    """
    Create and compile the complete search agent LangGraph workflow.

    The graph consists of:
    1. Query Classifier - determines user intent
    2. Query Planner - creates execution plan
    3. Query Executor - executes plan step-by-step (loop node)
    4. Response Formatter - formats results for user

    Args:
        checkpointer: Optional checkpointer for state persistence
                     Default: MemorySaver() for POC
                     Production: Use PostgresSaver or RedisSaver

    Returns:
        Compiled StateGraph ready for execution

    Example:
        >>> graph = create_search_agent_graph()
        >>> result = graph.invoke({
        ...     "user_query": "Find W2 documents",
        ...     "conversation_id": "conv-123",
        ...     "conversation_history": []
        ... })
        >>> print(result["response_message"])
    """
    logger.info("Creating search agent graph")

    # Create graph with state schema
    workflow = StateGraph(SearchAgentState)

    # Add nodes
    workflow.add_node("classifier", query_classifier_node)
    workflow.add_node("planner", query_planner_node)
    workflow.add_node("executor", query_executor_node)
    workflow.add_node("formatter", response_formatter_node)

    # Set entry point
    workflow.set_entry_point("classifier")

    # Add edges with routing logic
    workflow.add_conditional_edges(
        "classifier",
        route_after_classifier,
        {
            "planner": "planner",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "executor": "executor"
        }
    )

    workflow.add_conditional_edges(
        "executor",
        route_after_executor,
        {
            "executor": "executor",  # Loop back for next step
            "formatter": "formatter"
        }
    )

    workflow.add_conditional_edges(
        "formatter",
        route_after_formatter,
        {
            "__end__": END
        }
    )

    # Use provided checkpointer or default to MemorySaver
    if checkpointer is None:
        checkpointer = MemorySaver()
        logger.info("Using MemorySaver for checkpointing (POC mode)")

    # Compile the graph
    compiled_graph = workflow.compile(checkpointer=checkpointer)

    logger.info("Search agent graph compiled successfully")

    return compiled_graph


def create_search_agent_graph_from_config() -> StateGraph:
    """
    Create search agent graph with checkpointer from configuration settings.

    Uses settings to determine checkpoint backend:
    - settings.CHECKPOINTER_TYPE: "memory", "postgres", or "redis"
    - settings.POSTGRES_CONNECTION_STRING: PostgreSQL connection (if postgres)
    - settings.REDIS_URL: Redis URL (if redis)

    Returns:
        Compiled StateGraph with configured checkpointer

    Example:
        >>> # Set environment variables or .env file:
        >>> # CHECKPOINTER_TYPE=postgres
        >>> # POSTGRES_CONNECTION_STRING=postgresql://localhost/db
        >>> graph = create_search_agent_graph_from_config()
    """
    from search_agent.utils.checkpointing import get_checkpointer

    # Build checkpointer config from settings
    checkpointer_config = {"backend": settings.CHECKPOINTER_TYPE}

    if settings.CHECKPOINTER_TYPE == "postgres":
        if settings.POSTGRES_CONNECTION_STRING:
            checkpointer_config["connection_string"] = settings.POSTGRES_CONNECTION_STRING
        else:
            logger.warning(
                "CHECKPOINTER_TYPE is 'postgres' but POSTGRES_CONNECTION_STRING is not set. "
                "Falling back to MemorySaver."
            )
            checkpointer_config["backend"] = "memory"

    elif settings.CHECKPOINTER_TYPE == "redis":
        if settings.REDIS_URL:
            checkpointer_config["redis_url"] = settings.REDIS_URL
        else:
            logger.warning(
                "CHECKPOINTER_TYPE is 'redis' but REDIS_URL is not set. "
                "Falling back to MemorySaver."
            )
            checkpointer_config["backend"] = "memory"

    # Create checkpointer
    try:
        checkpointer = get_checkpointer(**checkpointer_config)
        logger.info(f"Using {checkpointer_config['backend']} checkpointer from config")
    except Exception as e:
        logger.error(f"Failed to create checkpointer: {e}. Falling back to MemorySaver.")
        checkpointer = MemorySaver()

    return create_search_agent_graph(checkpointer=checkpointer)


def visualize_graph(graph: StateGraph, output_path: str = "search_agent_graph.png"):
    """
    Visualize the graph structure and save to file.

    Requires graphviz to be installed:
        pip install pygraphviz

    Args:
        graph: Compiled StateGraph
        output_path: Path to save visualization

    Returns:
        None
    """
    try:
        from IPython.display import Image, display

        # Get Mermaid diagram
        mermaid_diagram = graph.get_graph().draw_mermaid()
        print("Graph structure (Mermaid):")
        print(mermaid_diagram)

        # Try to render as PNG if pygraphviz is available
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            with open(output_path, "wb") as f:
                f.write(png_data)
            logger.info(f"Graph visualization saved to {output_path}")
        except Exception as e:
            logger.warning(f"Could not save PNG (install pygraphviz): {e}")

    except ImportError:
        logger.warning("IPython not available, skipping visualization")


if __name__ == "__main__":
    # Test graph creation
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 70)
    print("Creating Search Agent LangGraph")
    print("=" * 70)

    # Create graph
    graph = create_search_agent_graph()

    print("\n✓ Graph compiled successfully!")

    # Print graph structure
    print("\nGraph Structure:")
    print("-" * 70)

    try:
        mermaid = graph.get_graph().draw_mermaid()
        print(mermaid)
    except Exception as e:
        print(f"Could not generate Mermaid diagram: {e}")

    print("\n" + "=" * 70)
    print("Nodes:")
    print("  1. classifier - Query Classifier")
    print("  2. planner - Query Planner")
    print("  3. executor - Query Executor (loop node)")
    print("  4. formatter - Response Formatter")
    print("\nRouting:")
    print("  classifier -> planner (if intent='search')")
    print("  classifier -> END (if intent='other')")
    print("  planner -> executor (always)")
    print("  executor -> executor (loop for multi-step)")
    print("  executor -> formatter (when complete)")
    print("  formatter -> END (always)")
    print("=" * 70)

    # Test with sample query
    print("\n" + "=" * 70)
    print("Testing with sample query")
    print("=" * 70)

    test_input: SearchAgentState = {
        "user_query": "Find all W2 documents",
        "conversation_id": "test-graph",
        "conversation_history": []
    }

    print(f"\nInput: {test_input['user_query']}")
    print("\nExecuting graph...")

    try:
        result = graph.invoke(test_input, config={"configurable": {"thread_id": "test-1"}})

        print("\n✓ Execution complete!")
        print(f"\nIntent: {result.get('intent', 'N/A')}")
        print(f"Plan Type: {result.get('query_plan', {}).get('plan_type', 'N/A')}")
        print(f"Total Steps: {result.get('total_steps', 'N/A')}")

        if "response_message" in result:
            print(f"\nResponse:\n{result['response_message']}")

        if "error" in result:
            print(f"\n❌ Error: {result['error']}")

    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        logger.exception("Graph execution error")
