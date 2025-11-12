# Testing Documentation

This document describes the test suite for the Multi-Agent Tool Builder System.

## Test Files

### 1. `test_basic.py` - Basic Validation Tests ✅

Tests the fundamental structure without requiring external dependencies.

**What it tests:**
- File structure completeness
- Module imports
- State creation and initialization
- Agent instantiation
- Graph structure

**Run:**
```bash
python multi_agent_system/test_basic.py
```

**Expected output:**
```
5/5 tests passed
🎉 All tests passed! System structure is valid.
```

### 2. `test_workflow.py` - Workflow Phase Tests ✅

Tests individual Agent 1 phases in isolation.

**What it tests:**
- Phase 1: Discovery (conversation handling)
- Phase 2: Artifact Generation (PRD + JSON schema)
- Phase 4: Save Artifacts (file creation, registry update)
- File persistence
- State transitions

**Run:**
```bash
python multi_agent_system/test_workflow.py
```

**Expected output:**
```
✅ Agent 1 workflow test completed successfully!
```

**Side effects:**
- Creates `PRDs/validate_email.md`
- Updates `tool_registry.json`

### 3. `test_graph.py` - LangGraph Compilation Tests ✅

Tests the LangGraph workflow compilation and execution structure.

**What it tests:**
- Graph compilation with checkpointing
- Graph invocation with state
- Event streaming
- Node execution flow

**Run:**
```bash
python multi_agent_system/test_graph.py
```

**Expected output:**
```
2/2 tests passed
🎉 All graph tests passed!
```

### 4. `test_integration.py` - Full Integration Test ✅

Tests the complete system with actual OpenAI API calls.

**What it tests:**
- End-to-end workflow with real LLM
- Discovery phase with actual question generation
- State management through multiple turns
- Resume functionality with user input

**Requirements:**
- `OPENAI_API_KEY` environment variable set
- Active internet connection
- OpenAI API credits

**Run:**
```bash
python multi_agent_system/test_integration.py
```

**Expected output:**
```
✅ Integration test completed successfully!
System is fully functional and ready to use!
```

**Note:** This test makes actual API calls and will consume credits.

## Running All Tests

To run the complete test suite:

```bash
# Basic structure tests (no API required)
python multi_agent_system/test_basic.py

# Workflow tests (no API required, creates test files)
python multi_agent_system/test_workflow.py

# Graph compilation tests (no API required)
python multi_agent_system/test_graph.py

# Integration tests (requires API key)
python multi_agent_system/test_integration.py
```

## Test Results Summary

| Test Suite | Status | API Required | Creates Files |
|------------|--------|--------------|---------------|
| `test_basic.py` | ✅ PASS | No | No |
| `test_workflow.py` | ✅ PASS | No | Yes |
| `test_graph.py` | ✅ PASS | No | No |
| `test_integration.py` | ✅ PASS | Yes | No |

## Known Issues

### LangSmith Warnings

You may see warnings like:
```
Failed to POST https://api.smith.langchain.com/runs/multipart
```

**This is expected and harmless.** LangChain tries to send telemetry to LangSmith for debugging, but since we don't have LangSmith configured, it fails. This doesn't affect functionality.

To disable these warnings, set:
```bash
export LANGCHAIN_TRACING_V2=false
```

## Test Coverage

### Covered ✅

- [x] State schema and initialization
- [x] Agent 1 instantiation
- [x] Discovery phase execution
- [x] Artifact generation (simulated)
- [x] Save phase (file creation)
- [x] Graph compilation
- [x] Graph execution flow
- [x] Checkpoint and state persistence
- [x] Event streaming
- [x] LLM integration (basic)

### Not Yet Covered ⏳

- [ ] Phase 3: Review with actual interrupt/resume cycle
- [ ] Complete multi-turn discovery conversation
- [ ] Iterative refinement loop (user requests changes)
- [ ] Escalation handling from downstream agents
- [ ] Error recovery and edge cases
- [ ] Concurrent session handling
- [ ] State corruption recovery

## Future Testing

### Unit Tests (To Be Added)

```bash
pytest multi_agent_system/tests/
```

Future test structure:
```
tests/
├── unit/
│   ├── test_state.py
│   ├── test_agent_1.py
│   └── test_graph.py
├── integration/
│   └── test_full_workflow.py
└── fixtures/
    └── mock_responses.py
```

### Test with Mock LLM

For CI/CD without API costs:

```python
# Future: Mock LLM for testing
from unittest.mock import Mock

mock_llm = Mock()
mock_llm.invoke.return_value.content = "Mocked response"
agent = RequirementsArchitect(llm=mock_llm)
```

## Debugging Tests

If tests fail:

1. **Check environment:**
   ```bash
   conda activate testing
   python --version  # Should be 3.10+
   ```

2. **Verify dependencies:**
   ```bash
   pip list | grep -E "(langgraph|langchain|openai)"
   ```

3. **Check API key (for integration tests):**
   ```bash
   echo $OPENAI_API_KEY
   ```

4. **Clean test artifacts:**
   ```bash
   rm -f PRDs/validate_email.md
   # Edit tool_registry.json to remove test entries
   ```

5. **Enable debug mode:**
   ```bash
   export LANGCHAIN_VERBOSE=true
   python multi_agent_system/test_integration.py
   ```

## Contributing Tests

When adding new features:

1. Add unit tests for new functions
2. Update workflow tests for new phases
3. Update integration tests for new agents
4. Document any new test files here

---

**All tests passing as of:** 2025-10-28
**Environment:** conda `testing` with Python 3.10.12
**LangGraph version:** 0.0.20+
