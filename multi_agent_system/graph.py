"""
LangGraph workflow for the multi-agent tool builder system.

This module defines the graph structure, nodes, edges, and routing logic
for the complete workflow from requirements through publishing.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from multi_agent_system.state import ToolBuilderState
from multi_agent_system.agents.agent_1_requirements import (
    agent_1_discovery,
    agent_1_generate,
    agent_1_review,
    agent_1_save
)


# ===== Routing Functions =====


def route_after_discovery(state: ToolBuilderState) -> Literal["generate", "review"]:
    """
    Route after Agent 1 discovery phase.

    Routes to:
    - "generate": If discovery is complete and ready to create artifacts
    - "review": If artifacts already exist (iteration case)

    Note: Discovery phase uses interrupt() to pause for user input.
    When user resumes, the same node runs again (LangGraph behavior).
    """
    current_phase = state.get("current_phase", "discovery")

    if current_phase == "generation":
        return "generate"
    elif state.get("prd_content") and not state.get("prd_approved"):
        # Already have artifacts, go directly to review
        return "review"
    else:
        # Should not reach here - discovery should have interrupted
        # But if it does, go to generation (fail-safe)
        return "generate"


def route_after_generation(state: ToolBuilderState) -> Literal["review"]:
    """
    Route after Agent 1 artifact generation.

    Always routes to review phase.
    """
    return "review"


def route_after_review(state: ToolBuilderState) -> Literal["save", "discovery", "generate", "review"]:
    """
    Route after Agent 1 review phase.

    Routes to:
    - "save": If user approved the artifacts
    - "discovery": If user requested changes requiring more Q&A
    - "generate": If user requested changes to artifacts only
    - "review": If waiting for user input (shouldn't happen, handled by interrupt)
    """
    if state.get("prd_approved"):
        return "save"

    current_phase = state.get("current_phase", "review")

    if current_phase == "discovery":
        return "discovery"
    elif current_phase == "generation":
        return "generate"
    else:
        return "review"


def route_after_save(state: ToolBuilderState) -> Literal["end", "agent_2"]:
    """
    Route after Agent 1 save phase.

    Routes to:
    - "agent_2": If ready to proceed to implementation (future)
    - "end": For Phase 1 MVP, just end here
    """
    # For Phase 1 MVP, end here
    # In future phases, route to agent_2_implement
    return "end"


# ===== Graph Construction =====


def create_tool_builder_graph() -> StateGraph:
    """
    Create the complete LangGraph workflow for tool building.

    Phase 1 (MVP): Only Agent 1 nodes
    Future phases: Will add Agent 2, 3, 4 nodes
    """

    # Initialize workflow with state schema
    workflow = StateGraph(ToolBuilderState)

    # ===== Agent 1 Nodes =====
    workflow.add_node("agent_1_discovery", agent_1_discovery)
    workflow.add_node("agent_1_generate", agent_1_generate)
    workflow.add_node("agent_1_review", agent_1_review)
    workflow.add_node("agent_1_save", agent_1_save)

    # ===== Set Entry Point =====
    workflow.set_entry_point("agent_1_discovery")

    # ===== Agent 1 Edges =====

    # After discovery - conditional routing
    workflow.add_conditional_edges(
        "agent_1_discovery",
        route_after_discovery,
        {
            "generate": "agent_1_generate",
            "review": "agent_1_review"
        }
    )

    # After generation - always go to review
    workflow.add_conditional_edges(
        "agent_1_generate",
        route_after_generation,
        {
            "review": "agent_1_review"
        }
    )

    # After review - conditional based on approval
    workflow.add_conditional_edges(
        "agent_1_review",
        route_after_review,
        {
            "save": "agent_1_save",
            "discovery": "agent_1_discovery",
            "generate": "agent_1_generate",
            "review": "agent_1_review"  # Loop back (shouldn't happen)
        }
    )

    # After save - end workflow (Phase 1)
    workflow.add_conditional_edges(
        "agent_1_save",
        route_after_save,
        {
            "end": END,
            "agent_2": END  # Placeholder for future Agent 2
        }
    )

    return workflow


def compile_graph(workflow: StateGraph, checkpointer=None):
    """
    Compile the graph with optional checkpointer for persistence.

    Args:
        workflow: The StateGraph to compile
        checkpointer: Optional checkpointer (e.g., MemorySaver) for state persistence

    Returns:
        Compiled graph ready for execution
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    # Compile with checkpointing and interrupts before review nodes
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["agent_1_review"]  # Human approval gate
    )

    return app


def create_app():
    """
    Convenience function to create and compile the complete app.

    Returns:
        Compiled LangGraph app ready for use
    """
    workflow = create_tool_builder_graph()
    return compile_graph(workflow)
