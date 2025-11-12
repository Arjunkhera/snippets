# Multi-Agent Tool Builder System

A LangGraph-based multi-agent system that automates the end-to-end process of creating Python tools/functions - from requirements gathering through implementation, testing, and publishing to pip.

## 🎯 Overview

This system uses specialized AI agents working sequentially with built-in feedback loops and human approval gates to create high-quality, production-ready Python tools.

### Current Status: Phase 1 (MVP) - Agent 1 Complete ✅

**Phase 1** implements Agent 1 (Requirements Architect) with:
- ✅ Interactive requirements gathering (conversational Q&A)
- ✅ PRD markdown generation
- ✅ OpenAI JSON schema generation
- ✅ User review and iterative refinement
- ✅ Human-in-the-loop approval gates
- ✅ State persistence and checkpointing

## 🏗️ Architecture

```
User Input → Agent 1 (Requirements) → [Approval] → Agent 2 (Implementation)*
→ [Approval] → Agent 3 (Testing)* → [Approval] → Agent 4 (Publishing)* → Complete
     ↑              ↓ (escalation if ambiguous)         ↓                  ↓
     └──────────────┴─────────────────────────────────┴──────────────────┘

* Coming in future phases
```

### Technology Stack

- **LangGraph**: Workflow orchestration and state management
- **LangChain**: LLM integration framework
- **OpenAI API**: LLM backend (GPT-4)
- **Python 3.10+**: Core language
- **pytest**: Testing framework (for future Agent 3)

## 📦 Installation

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**

```bash
cp multi_agent_system/.env.example multi_agent_system/.env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

## 🚀 Usage

### Interactive Mode (Recommended)

Run the CLI in interactive mode for a guided experience:

```bash
python -m multi_agent_system.main
```

This will:
1. Ask you to describe the tool you want to create
2. Guide you through requirements gathering via Q&A
3. Generate PRD and JSON schema for your review
4. Allow iteration until you approve
5. Save artifacts to `PRDs/` and update `tool_registry.json`

### Command Line Mode

Provide your initial request as a command-line argument:

```bash
python -m multi_agent_system.main "I want to create a tool that validates JSON files"
```

### Example Session

```
🛠️  Multi-Agent Tool Builder System 🛠️

Let's create a new tool! What would you like to build?
Your request: I want to create a function that reads CSV files and converts them to JSON

🤖 Agent: agent_1 | Phase: discovery

What would you like to name this function? Please provide a Python-valid identifier.

Your response: csv_to_json

🤖 Agent: agent_1 | Phase: discovery

Great! Can you describe what this function should do? Please be specific about its purpose.

Your response: Reads a CSV file from disk and converts it to JSON format, returning the data as a JSON string

[... conversation continues ...]

🤖 Agent: agent_1 | Phase: review

I've generated the following artifacts for your review:

## PRD (Markdown Tool Definition)
[... PRD content ...]

## JSON Schema (OpenAI Function)
[... JSON schema ...]

Please review and let me know:
- Approve: Say "approve", "looks good", "proceed", or "LGTM"
- Request changes: Provide specific feedback
- Ask questions: Any clarifications needed

Your response: looks good

✅ Artifacts saved successfully!
- PRD: PRDs/csv_to_json.md
- Registry updated: tool_registry.json
```

## 📁 Project Structure

```
multi_agent_system/
├── __init__.py              # Package initialization
├── state.py                 # State schema and management
├── graph.py                 # LangGraph workflow definition
├── main.py                  # CLI interface
├── .env.example             # Environment variables template
├── README.md                # This file
└── agents/
    ├── __init__.py
    └── agent_1_requirements.py  # Agent 1: Requirements Architect

Generated files:
├── PRDs/
│   └── {function_name}.md   # Generated PRDs
├── tool_registry.json        # Updated with new tool schemas
└── .agent_state/
    └── {thread_id}.json     # Session state snapshots
```

## 🔄 Workflow Phases

### Agent 1: Requirements Architect (Current)

**Phase 1 - Interactive Discovery:**
- Asks questions one at a time to gather complete requirements
- Collects: function name, description, parameters, outputs, error cases, constraints
- Builds understanding through conversational Q&A

**Phase 2 - Artifact Generation:**
- Generates PRD markdown (following standard format)
- Generates OpenAI function JSON schema
- Presents both for user review

**Phase 3 - User Review & Iteration:**
- Human-in-the-loop approval gate (uses LangGraph `interrupt()`)
- User can approve, request changes, or ask questions
- Loops back to discovery/generation as needed

**Phase 4 - Handoff Preparation:**
- Saves PRD to `PRDs/{function_name}.md`
- Updates `tool_registry.json` with JSON schema
- Prepares state for Agent 2 (future)

**Phase 5 - Escalation Handling:**
- Handles clarification questions from downstream agents (future)
- Updates PRD and versions changes

### Agent 2: Implementation Specialist (Coming Soon)

Will convert specifications into working Python code following TDD principles.

### Agent 3: Test Engineer (Coming Soon)

Will write comprehensive pytest test suites covering all PRD requirements.

### Agent 4: Release Manager (Coming Soon)

Will package and publish tools to PyPI.

## 🧠 Key Features

### Human-in-the-Loop Approval Gates

Uses LangGraph's `interrupt()` mechanism to pause execution and wait for human approval at critical checkpoints:

```python
# In agent_1_requirements.py
user_feedback = interrupt(presentation)  # Pauses here until user responds
```

### State Persistence

All workflow state is persisted using LangGraph's checkpointing:
- Resume interrupted sessions
- Audit trail for debugging
- Thread-based isolation

### Conditional Routing

Smart routing based on state and user input:
- Approved → Proceed to next agent
- Changes requested → Loop back to appropriate phase
- Escalation needed → Return to Agent 1

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_key

# Optional
MODEL_NAME=gpt-4              # Default: gpt-4
MODEL_TEMPERATURE=0.7         # Default: 0.7
WORKSPACE_PATH=/path/to/repo  # Default: current directory
```

### Model Configuration

By default, Agent 1 uses GPT-4. You can customize in `agent_1_requirements.py`:

```python
agent = RequirementsArchitect(
    model_name="gpt-4-turbo-preview",
    temperature=0.5
)
```

## 📖 API Usage

You can also use the system programmatically:

```python
from multi_agent_system import ToolBuilderCLI

# Create CLI instance
cli = ToolBuilderCLI()

# Start a new session
cli.start_session("Create a tool that parses XML files")

# Resume with user input
cli.resume_session("name it parse_xml")

# Save session state
cli.save_session_state()
```

## 🧪 Testing

Currently implementing Phase 1 (Agent 1 only). To test:

```bash
python -m multi_agent_system.main
```

Follow the interactive prompts to create a sample tool.

## 🗺️ Roadmap

- [x] **Phase 1**: Agent 1 (Requirements Architect) - MVP ✅
- [ ] **Phase 2**: Agent 2 (Implementation Specialist)
- [ ] **Phase 3**: Agent 3 (Test Engineer)
- [ ] **Phase 4**: Agent 4 (Release Manager)
- [ ] **Phase 5**: Polish, optimization, and CLI enhancements

## 📚 References

- [PRD: Full System Design](../PRDs/multi_agent_tool_builder.md)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Existing CreateTools Prompt](../Prompts/CreateTools.md)
- [Example PRD](../PRDs/get_file_data.md)

## 🤝 Contributing

This is part of the `akhera_ai_tools` project. See main repository for contribution guidelines.

## 📝 License

[Your License Here]

## 🐛 Troubleshooting

### "Module not found" errors

Make sure you're running from the repository root:

```bash
cd /path/to/snippets
python -m multi_agent_system.main
```

### OpenAI API errors

- Verify your API key is set in `.env`
- Check your OpenAI account has credits
- Try a different model if rate-limited

### State persistence issues

Session states are saved to `.agent_state/{thread_id}.json`. If corrupted:

```bash
rm -rf .agent_state/
```

Start a fresh session.

## 💡 Tips

1. **Be specific**: The more detailed your initial description, the fewer questions Agent 1 needs to ask
2. **Review carefully**: The PRD becomes the contract for implementation - ensure it's complete
3. **Save often**: Use the 'save' command during long sessions
4. **Iterate freely**: Don't hesitate to request changes - that's what the system is designed for

---

**Built with ❤️ using LangGraph**
