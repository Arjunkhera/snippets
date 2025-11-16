# Quick Start Guide - Phase 1

This guide helps you get started with the Phase 1 foundation.

## Installation

```bash
# Navigate to search_agent directory
cd search_agent

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Verify Installation

```bash
# Test configuration
python -m config.settings

# Run Phase 1 tests
pytest tests/test_state.py -v

# Run examples
python examples/example_basic.py
```

## Project Structure Overview

```
search_agent/
├── config/           # Configuration management
│   └── settings.py   # Pydantic settings with env vars
├── core/             # State and models
│   ├── state.py      # LangGraph state schema
│   └── models.py     # Pydantic models
├── services/         # External integrations
│   ├── elasticsearch_service.py  # Mock ES for Phase 1
│   └── llm_service.py           # Anthropic Claude API
├── utils/            # Helper functions
│   └── validation.py
├── nodes/            # Node implementations (Phases 2-4)
├── prompts/          # Prompt templates (Phases 2-4)
├── examples/         # Usage examples
└── tests/            # Unit tests
```

## Next Steps

1. **Phase 2**: Implement Query Planner Node
   - Read `PHASE_HANDOFF.md` Section "Phase 2"
   - Review PRD Section 6.2 and 8
   - Start with `prompts/planner_prompt.py`

2. **Understanding the Architecture**:
   - Read `ARCHITECTURE.md` for design patterns
   - Review `core/state.py` for state schema
   - Explore `examples/example_basic.py` for usage patterns

3. **Testing Your Changes**:
   - Write unit tests in `tests/`
   - Use mock ES service for testing
   - Follow existing test patterns

## Key Files to Review

- **README.md**: Project overview and phase tracking
- **ARCHITECTURE.md**: Detailed technical documentation
- **PHASE_HANDOFF.md**: Phase completion status and next steps
- **core/models.py**: Pydantic models with validation
- **services/elasticsearch_service.py**: Mock ES implementation

## Getting Help

- Check `ARCHITECTURE.md` for design patterns
- Review existing Phase 1 code for examples
- Refer to PRD (`../PRDs/langgraph.md`) for specifications
- Test incrementally as you build
