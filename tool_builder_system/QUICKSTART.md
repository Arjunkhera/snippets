# Quick Start Guide - Phase 1

## Installation

```bash
# Navigate to the tool builder system
cd /home/user/snippets/tool_builder_system

# Install required dependencies (if not already installed)
pip install langgraph langchain-anthropic anthropic pytest pytest-mock

# Set your Anthropic API key
export ANTHROPIC_API_KEY='your-anthropic-api-key-here'
```

## Run the Interactive CLI

```bash
python -m tool_builder_system.main
```

## Run Tests

```bash
# From the snippets directory
pytest tool_builder_system/tests/test_agent_1_integration.py -v
```

Expected output:
```
10 passed in 1.16s ✅
```

## Example Session

```
Multi-Agent Tool Builder System - Phase 1
==========================================

👤 You:
What tool would you like to create? I want to create a tool that validates email addresses

🤖 Agent 1 (Requirements Architect):
Great! Let's design an email validation tool. What should we name this function?

👤 You:
validate_email

🤖 Agent 1:
Perfect! Now, what input parameters should this function accept?

[... conversation continues ...]

🤖 Agent 1:
I've created the PRD and JSON schema for your review:

[PRD and JSON schema shown]

👤 You:
Looks good, proceed

🎉 PRD Approved!

Phase 1 is complete.
```

## What You Get

After approval, the state is saved to `.agent_state/tool_builder_session_1.json` with:
- Complete conversation history
- Generated PRD markdown
- OpenAI JSON schema
- All gathered requirements

## Next Steps

**Phase 2** (Coming Next):
- Agent 2 will implement the code based on the PRD
- You'll review the implementation
- Files will be saved to the proper locations

See `PHASE_2_PLAN.md` for implementation details.

## Troubleshooting

### API Key Error
```
Error: ANTHROPIC_API_KEY environment variable not set.
```
**Solution:** `export ANTHROPIC_API_KEY='your-key'`

### Import Errors
```
ModuleNotFoundError: No module named 'langgraph'
```
**Solution:** `pip install langgraph langchain-anthropic anthropic`

## Documentation

- `README.md` - Complete system documentation
- `PHASE_1_COMPLETE.md` - What was built in Phase 1
- `PHASE_2_PLAN.md` - What's coming in Phase 2
