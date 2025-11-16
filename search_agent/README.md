# Elasticsearch Search/List Agent

An AI-powered multi-step query agent built with LangGraph for intelligent document and folder search in an Elasticsearch-based document management system.

## Overview

This agent translates natural language queries into Elasticsearch DSL queries, intelligently handling both simple single-step searches and complex multi-step queries that require sequential information resolution (e.g., resolving folder names to IDs before querying documents).

## Key Features

- **Natural Language Query Processing**: Convert user queries into Elasticsearch DSL
- **Multi-Step Query Planning**: Automatically detect when queries need multiple sequential steps
- **Intelligent Resolution**: Handle name-to-ID resolution for folders and documents
- **Human-in-the-Loop**: Request clarification for ambiguous queries
- **Robust Error Handling**: Retry logic and graceful error recovery

## Architecture

The agent follows a 4-node LangGraph state machine:

```
User Query → [Classifier] → [Planner] → [Executor Loop] → [Formatter] → Response
```

1. **Query Classifier**: Determines if query is search/list vs. other operations
2. **Query Planner**: Analyzes query and creates single-step or multi-step execution plan
3. **Query Executor**: Executes plan step-by-step, looping for multi-step queries
4. **Response Formatter**: Formats results for user-friendly output

## Project Status

### ✅ Phase 1: Foundation & State Management (COMPLETE)
- Project structure setup
- State schema definition
- Mock Elasticsearch service interface
- Configuration management
- Basic utilities

### ✅ Phase 2: Query Planner Node (COMPLETE)
- Query planner implementation
- Planner prompt engineering
- Plan validation logic
- Unit tests
- Example queries

### ✅ Phase 3: Query Executor Node (COMPLETE)
- Executor loop node implementation
- Integration with ES query generator
- Step-by-step execution
- Result passing between steps
- Clarification handling (HITL)
- Error handling and retries

### ✅ Phase 4: Classifier & Formatter Nodes (COMPLETE)
- Query classifier node with intent detection
- Response formatter node with user-friendly output
- Complete LangGraph workflow assembly
- Unit tests for all new nodes
- End-to-end integration example

### 🔄 Phase 5: Error Handling & HITL (NEXT)
- Comprehensive error handling
- Retry logic
- Human-in-the-loop clarifications
- Checkpointing

### 📋 Phase 6: Integration & Testing
- End-to-end integration tests
- Example queries from PRD
- Performance testing
- Documentation

## Documentation

- [Architecture Overview](./ARCHITECTURE.md) - System design and components
- [Phase Handoff Guide](./PHASE_HANDOFF.md) - Phase completion status and next steps
- [PRD Reference](../PRDs/langgraph.md) - Complete Product Requirements Document

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export ANTHROPIC_API_KEY="your-api-key-here"
export ELASTICSEARCH_URL="http://localhost:9200"  # Optional for Phase 1
```

### Basic Usage (After Phase 3+)

```python
from search_agent.core.state import SearchAgentState, create_initial_state
from search_agent.graph import create_search_agent_graph

# Create agent
agent = create_search_agent_graph()

# Execute query
initial_state = create_initial_state(
    user_query="List documents in Tax Documents folder",
    conversation_id="conv-123"
)

result = agent.invoke(initial_state)
print(result["response_message"])
```

## Dependencies

- **langgraph** >= 0.0.20 - State machine orchestration
- **langchain** >= 0.1.0 - LLM interaction layer
- **anthropic** >= 0.18.0 - Claude API
- **pydantic** >= 2.0.0 - Data validation
- **python-dotenv** >= 1.0.0 - Environment configuration

See [requirements.txt](./requirements.txt) for complete list.

## Project Structure

```
search_agent/
├── README.md                    # This file
├── ARCHITECTURE.md              # Detailed architecture documentation
├── PHASE_HANDOFF.md            # Phase completion & handoff guide
├── requirements.txt             # Python dependencies
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration management
├── core/
│   ├── __init__.py
│   ├── state.py                 # LangGraph state schema
│   └── models.py                # Pydantic models for type safety
├── services/
│   ├── __init__.py
│   ├── elasticsearch_service.py # Elasticsearch service interface
│   └── llm_service.py          # LLM interaction wrapper
├── nodes/
│   ├── __init__.py
│   ├── classifier.py            # Phase 4
│   ├── planner.py               # Phase 2
│   ├── executor.py              # Phase 3
│   └── formatter.py             # Phase 4
├── prompts/
│   ├── __init__.py
│   ├── classifier_prompt.py     # Phase 4
│   ├── planner_prompt.py        # Phase 2
│   └── executor_prompt.py       # Phase 3
├── utils/
│   ├── __init__.py
│   └── validation.py            # Validation utilities
├── examples/
│   └── example_queries.py       # Usage examples
└── tests/
    ├── __init__.py
    ├── test_state.py            # Phase 1
    ├── test_planner.py          # Phase 2
    ├── test_executor.py         # Phase 3
    └── test_integration.py      # Phase 6
```

## Configuration

Configuration is managed through environment variables and the `config/settings.py` module:

```python
from search_agent.config import settings

print(settings.ANTHROPIC_API_KEY)
print(settings.ELASTICSEARCH_URL)
print(settings.MAX_RETRIES)
```

See [config/settings.py](./config/settings.py) for all configuration options.

## Design Decisions

### Why LangGraph?
- Built-in state management and checkpointing
- Native support for human-in-the-loop interrupts
- Multi-turn conversation context
- Integration with other agents (future: move, delete, create operations)

### Why Separate Planner & Executor?
- **Clarity**: Clean separation of concerns (planning vs. execution)
- **Debuggability**: Inspect plans before execution
- **Reusability**: Same executor handles any plan structure
- **Transparency**: Users can see what the system intends to do

### Why Loop Node Instead of Multiple Executor Nodes?
- Simpler for POC phase
- All execution logic in one place
- Easier to iterate and debug
- Can refactor into specialized nodes later if needed

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_state.py -v

# Run with coverage
pytest --cov=search_agent tests/
```

## Contributing

When implementing subsequent phases, please:

1. Read the [PHASE_HANDOFF.md](./PHASE_HANDOFF.md) guide
2. Follow the established code structure and patterns
3. Update documentation as you go
4. Write tests for new functionality
5. Update the phase status in this README

## License

See [LICENSE](../LICENSE) file in repository root.

## References

- [Product Requirements Document](../PRDs/langgraph.md) - Complete specification
- [Existing ES Query Tool](../ai_tools/elasticsearch/) - Elasticsearch query generator
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Anthropic API Documentation](https://docs.anthropic.com/)
