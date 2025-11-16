# Multi-Agent Tool Builder System

A LangGraph-based system for automating Python tool development from requirements gathering through implementation, testing, and publishing to pip.

## Current Status: Phase 1 (MVP)

**Implemented:**
- ✅ Agent 1: Requirements Architect
  - Interactive requirements gathering
  - PRD markdown generation
  - OpenAI JSON schema generation
  - User review and approval loop
  - State persistence

**Coming Next:**
- 🔄 Phase 2: Agent 2 (Implementation Specialist)
- 🔄 Phase 3: Agent 3 (Test Engineer)
- 🔄 Phase 4: Agent 4 (Release Manager)

## Overview

This system uses a multi-agent workflow orchestrated by LangGraph to automate the end-to-end process of creating Python tools/functions. Each agent specializes in a specific phase:

1. **Agent 1 - Requirements Architect** (Current Phase)
   - Gathers requirements through conversational Q&A
   - Generates Product Requirements Document (PRD)
   - Creates OpenAI-compatible JSON schema
   - Handles user approval and iterations

2. **Agent 2 - Implementation Specialist** (Phase 2)
   - Reads PRD and implements Python code
   - Handles error cases and edge conditions
   - Escalates ambiguities back to Agent 1

3. **Agent 3 - Test Engineer** (Phase 3)
   - Writes comprehensive pytest test suite
   - Covers all success and error cases from PRD
   - Executes tests and reports coverage

4. **Agent 4 - Release Manager** (Phase 4)
   - Manages versioning
   - Builds distribution packages
   - Publishes to PyPI
   - Updates documentation

## Architecture

### Technology Stack

- **Framework:** LangGraph (workflow orchestration)
- **LLM Provider:** Anthropic Claude (configurable)
- **Language:** Python 3.10+
- **Testing:** pytest
- **State Management:** JSON file-based persistence

### Directory Structure

```
tool_builder_system/
├── agents/
│   ├── __init__.py
│   └── agent_1.py              # Requirements Architect implementation
├── prompts/
│   └── agent_1_system_prompt.md # Agent 1 system instructions
├── tests/
│   └── test_agent_1_integration.py
├── .agent_state/                # State persistence (auto-created)
├── __init__.py
├── state.py                     # State schema definitions
├── state_persistence.py         # State save/load utilities
├── graph.py                     # LangGraph workflow definition
├── main.py                      # CLI entry point
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Anthropic API key

### Setup

1. **Install dependencies:**

```bash
cd tool_builder_system
pip install -r requirements.txt
```

2. **Set up environment variables:**

```bash
export ANTHROPIC_API_KEY='your-anthropic-api-key-here'
```

Or create a `.env` file:

```bash
ANTHROPIC_API_KEY=your-key-here
```

## Usage

### Phase 1: Interactive CLI

Run the interactive CLI to create a tool with Agent 1:

```bash
python -m tool_builder_system.main
```

**Example Session:**

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
Perfect! What input parameters should this function accept?

[... conversation continues ...]

🤖 Agent 1:
I've created the PRD and JSON schema for your review:

## PRD: validate_email

[PRD content shown]

## JSON Schema

[JSON schema shown]

Please review and let me know:
- Approve: "Looks good" or "Proceed"
- Request changes: Specify what needs updating

👤 You:
Looks good, proceed

🎉 PRD Approved!

Phase 1 is complete.
State saved to: .agent_state/tool_builder_session_1.json
```

### Programmatic Usage

```python
from tool_builder_system import (
    create_initial_state,
    Agent1,
    ToolBuilderWorkflow,
    StatePersistence
)
from langgraph.checkpoint.memory import MemorySaver

# Initialize components
agent_1 = Agent1()
workflow = ToolBuilderWorkflow(agent_1)

# Compile with checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Create initial state
state = create_initial_state("I want to create a JSON validator")

# Run workflow
config = {"configurable": {"thread_id": "session_1"}}
for event in app.stream(state, config):
    print(event)
```

## State Management

The system maintains a shared state throughout the workflow:

### State Schema

```python
class ToolBuilderState(TypedDict):
    # User interaction
    user_input: str
    conversation_history: list[dict]

    # Requirements (Agent 1)
    function_name: Optional[str]
    prd_content: Optional[str]
    json_schema: Optional[dict]
    prd_version: str
    prd_approved: bool

    # Workflow control
    current_agent: str
    current_phase: str
    escalation_active: bool

    # Metadata
    created_at: str
    last_updated: str
    errors: list[str]
```

### State Persistence

States are automatically saved to `.agent_state/{session_id}.json` and can be resumed:

```python
persistence = StatePersistence()

# Save state
persistence.save_state(state, session_id="my_tool")

# Load state
loaded_state = persistence.load_state(session_id="my_tool")

# List all sessions
sessions = persistence.list_sessions()
```

## Testing

### Run Integration Tests

```bash
cd tool_builder_system
pytest tests/test_agent_1_integration.py -v
```

### Test Coverage

Phase 1 tests cover:
- ✅ Agent 1 initialization
- ✅ Discovery phase conversation
- ✅ Artifact generation (PRD + JSON schema)
- ✅ User approval detection
- ✅ Iteration handling
- ✅ State persistence
- ✅ Artifact extraction logic
- ✅ Workflow graph compilation

## Agent 1 Details

### Workflow Phases

1. **Discovery** - Interactive Q&A to gather:
   - Function name
   - Description
   - Input parameters (name, type, required/optional, description)
   - Success output structure
   - Error conditions and formats
   - Constraints and behaviors

2. **Generate** - Creates:
   - PRD markdown (human-readable specification)
   - OpenAI JSON schema (machine-readable API contract)

3. **Review** - User approval gate:
   - User can approve, request changes, or ask questions
   - Loops until explicit approval

4. **Complete** - Prepares for Phase 2 handoff

### Example PRD Format

```markdown
# Tool: validate_email

**Description:**
Validates email addresses using RFC 5322 standard...

**Function Name:**
`validate_email`

**Input Parameters:**
* **`email`** (`str`, Required): Email address to validate

**Success Output:**
```json
{
  "valid": true,
  "email": "user@example.com"
}
```

**Error Outputs:**
* **Invalid Format:**
    ```json
    {
      "error_code": "INVALID_FORMAT",
      "error_message": "Email format is invalid"
    }
    ```

**Constraints & Behaviors:**
* Uses RFC 5322 validation
* Maximum length: 254 characters
```

### Example JSON Schema

```json
{
  "validate_email": {
    "type": "function",
    "name": "validate_email",
    "description": "Validates email addresses...",
    "parameters": {
      "type": "object",
      "properties": {
        "email": {
          "type": "string",
          "description": "Email address to validate"
        }
      },
      "required": ["email"],
      "additionalProperties": false
    }
  }
}
```

## Development Roadmap

### Phase 1 ✅ (Current)
- [x] State management
- [x] Agent 1 implementation
- [x] LangGraph workflow
- [x] Interactive CLI
- [x] State persistence
- [x] Integration tests
- [x] Documentation

### Phase 2 🔄 (Next)
- [ ] Agent 2 implementation
- [ ] Code generation from PRD
- [ ] Escalation back to Agent 1
- [ ] Agent 2 approval gate
- [ ] Agent 2 tests
- [ ] Update workflow graph

### Phase 3 🔄 (Future)
- [ ] Agent 3 implementation
- [ ] Test generation
- [ ] Test execution
- [ ] Coverage reporting
- [ ] Agent 3 tests

### Phase 4 🔄 (Future)
- [ ] Agent 4 implementation
- [ ] Version management
- [ ] Package building
- [ ] PyPI publishing
- [ ] Documentation updates

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY` - Required for Claude API access
- `WORKSPACE_PATH` - Optional, defaults to current directory

### Model Selection

Default model: `claude-sonnet-4-20250514`

To use a different model:

```python
agent_1 = Agent1(model="claude-sonnet-3-5-20241022")
```

## Troubleshooting

### API Key Not Found

```
Error: ANTHROPIC_API_KEY environment variable not set.
```

**Solution:** Set the environment variable:
```bash
export ANTHROPIC_API_KEY='your-key'
```

### Import Errors

```
ModuleNotFoundError: No module named 'langgraph'
```

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### State Not Persisting

**Solution:** Ensure `.agent_state/` directory is writable:
```bash
mkdir -p tool_builder_system/.agent_state
chmod 755 tool_builder_system/.agent_state
```

## Contributing

This is Phase 1 (MVP). Contributions for Phase 2-4 are welcome!

### Next Steps for Contributors

1. **Implement Agent 2** (Implementation Specialist)
   - Read PRD from state
   - Generate Python code
   - Implement escalation to Agent 1
   - Add approval gate

2. **Implement Agent 3** (Test Engineer)
   - Generate pytest tests
   - Execute tests
   - Report coverage

3. **Implement Agent 4** (Release Manager)
   - Version management
   - Package building
   - PyPI publishing

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Full PRD](../PRDs/multi_agent_tool_builder.md)

## License

[Specify your license here]

## Contact

[Your contact information]

---

**Built with LangGraph + Claude Sonnet 4.5**
