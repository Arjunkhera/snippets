# Nodes

This directory contains the LangGraph node implementations for the search agent.

## Node Implementation Status

### Phase 2: Query Planner
- [ ] `planner.py` - Query planning and gap analysis node

### Phase 3: Query Executor
- [ ] `executor.py` - Multi-step query execution loop node

### Phase 4: Classifier & Formatter
- [ ] `classifier.py` - Intent classification node
- [ ] `formatter.py` - Response formatting node

## Node Function Signature

All nodes follow this pattern:

```python
from search_agent.core.state import SearchAgentState

def node_name(state: SearchAgentState) -> SearchAgentState:
    """
    Brief description of what this node does.

    Args:
        state: Current agent state

    Returns:
        Updated state with new fields populated

    Raises:
        Exception: When something goes wrong
    """
    # 1. Extract inputs from state
    user_query = state["user_query"]

    # 2. Perform node logic
    result = do_something(user_query)

    # 3. Update and return state
    return {
        **state,
        "new_field": result,
        "last_updated": datetime.now().isoformat()
    }
```

## Testing Nodes

Each node should have corresponding tests in `tests/test_<node_name>.py`:

```python
def test_node_name():
    # Create initial state
    state = create_initial_state("test query", "conv-123")

    # Call node
    updated_state = node_name(state)

    # Assert expectations
    assert updated_state["new_field"] is not None
```

## Node Routing

Nodes are connected via conditional edges in the LangGraph workflow.
See `graph.py` (to be created in Phase 4) for routing logic.
