# PRD: Multi-Agent Tool Development System

**Version:** 1.0  
**Date:** October 27, 2025  
**Status:** Design Approved - Ready for Implementation

---

## 1. Executive Summary

A multi-agent system that automates the end-to-end process of creating Python tools/functions - from requirements gathering through implementation, testing, and publishing to pip. The system uses specialized agents working sequentially with built-in feedback loops and human approval gates.

---

## 2. System Architecture

### 2.1 High-Level Overview

```
User Input → Agent 1 (Requirements) → [Approval] → Agent 2 (Implementation) 
→ [Approval] → Agent 3 (Testing) → [Approval] → Agent 4 (Publishing) → Complete
     ↑              ↓ (escalation if ambiguous)         ↓                  ↓
     └──────────────┴─────────────────────────────────┴──────────────────┘
```

**Core Design Principles:**
- Sequential handoff between agents with clear boundaries
- Human-in-the-loop approval gates after each agent
- Bidirectional communication (escalation back to Agent 1)
- TDD-style approach (PRD acts as specification/contract)
- Persistent state management across agent transitions

### 2.2 Technology Stack

**Primary Framework:** LangGraph (for orchestration and state management)

**Supporting Technologies:**
- LangChain (dependency of LangGraph)
- OpenAI API or Anthropic Claude API (LLM backend - flexible)
- Python 3.10+
- pytest (for test execution)
- Standard Python packaging tools (setuptools, wheel, twine)

**Key LangGraph Features Used:**
- Graph-based state machine for workflow
- Conditional routing for approval/escalation
- Shared state across agents
- Human-in-the-loop checkpoints
- State persistence for resume capability

---

## 3. Agent Specifications

### 3.1 Agent 1: Requirements Architect

**Role:** Own the complete requirements lifecycle from discovery through all iterations

**Responsibilities:**
1. Interactive requirements gathering (conversational)
2. PRD markdown generation
3. OpenAI JSON schema generation
4. User review and iterative refinement
5. Handle escalations from downstream agents

**Workflow Phases:**

#### Phase 1: Interactive Discovery (Chat Experience)
- Ask questions one at a time (based on existing `CreateTools.md` prompt)
- Gather: function name, description, parameters, outputs, error cases, constraints
- Clarify ambiguities in real-time
- Build internal understanding of user needs

**Required Information to Gather:**
- Function name (Python-valid identifier)
- Description (clear, concise, AI-consumable)
- Input parameters:
  - Name, type, required/optional status, description, default values
- Success output structure (exact format and data types)
- Error conditions:
  - Each potential error scenario
  - Error code and message format for each
- Constraints & behaviors:
  - Size limits, security restrictions, validation rules
  - File type handling, encoding assumptions
  - Performance considerations

#### Phase 2: Artifact Generation
Once information is complete:
- Generate PRD markdown following standard format (see existing `PRDs/get_file_data.md`)
- Generate OpenAI function JSON schema (see existing `tool_registry.json` format)
- Present both documents to user in readable format

**PRD Structure:**
```markdown
# Tool: {function_name}

**Description:** ...

**Function Name:** ...

**Input Parameters:**
- parameter_name (type, Required/Optional): Description

**Success Output:**
{JSON example}

**Error Outputs:**
- ERROR_CODE: {JSON example with description}

**Constraints & Behaviors:**
- Bullet list of constraints
```

**JSON Schema Format:**
```json
{
  "function_name": {
    "type": "function",
    "name": "function_name",
    "description": "...",
    "parameters": {
      "type": "object",
      "properties": { ... },
      "required": [...],
      "additionalProperties": false
    }
  }
}
```

#### Phase 3: User Review & Iteration
User options:
- **Approve** → Proceed to Phase 4
- **Request modifications** → Agent 1 updates documents, re-presents
- **Ask questions** → Agent 1 clarifies, may update documents
- **Make direct edits** → Agent 1 incorporates feedback

**Loop as many times as needed until explicit approval**

#### Phase 4: Handoff Preparation
Once approved:
- Save PRD to `PRDs/{function_name}.md`
- Update `tool_registry.json` with new JSON schema entry
- Update shared state for Agent 2

#### Phase 5: Reactivation (Escalation Handling)
If Agent 2, 3, or 4 discovers:
- Ambiguity in requirements
- Missing error case
- Unclear constraint
- Contradiction in specification

**Agent 1 reactivates:**
- Discusses clarification with user
- Updates PRD + JSON schema
- Versions the changes
- Hands back to requesting agent

**Inputs:**
- User conversation (natural language)
- Escalation questions from downstream agents

**Outputs:**
- `PRDs/{function_name}.md` (versioned)
- Entry in `tool_registry.json`
- Updated shared state

**Success Criteria:**
- User explicitly approves PRD and JSON schema
- All required information captured completely
- No ambiguities or contradictions
- PRD follows standard structure

---

### 3.2 Agent 2: Implementation Specialist

**Role:** Convert specifications into working Python code

**Responsibilities:**
1. Read and understand PRD completely
2. Determine proper module placement in codebase
3. Implement function matching PRD exactly
4. Add appropriate logging, documentation, error handling
5. Self-validate implementation against PRD
6. Escalate to Agent 1 if ambiguities discovered

**Workflow:**

#### Step 1: Input Consumption
- Read `PRDs/{function_name}.md` thoroughly
- Understand existing codebase structure (e.g., `ai_tools/file_system/`, `ai_tools/network/`)
- Identify dependencies needed

#### Step 2: Implementation Planning
- Determine module placement (follow existing patterns)
- Identify required imports (standard library + external)
- Plan error handling strategy
- Consider edge cases mentioned in PRD

#### Step 3: Code Generation
**Code must include:**
- Complete function implementation
- Type hints for all parameters and return type
- Comprehensive docstring:
  - Function description
  - Args section (each parameter documented)
  - Returns section (both success and error formats)
  - Possible error codes listed
- Inline comments for complex logic
- Logging statements (following existing patterns, see user rules)
- All error cases from PRD implemented exactly as specified

**File location:** `ai_tools/{module_category}/{function_name}.py`

**Code quality standards:**
- Clean, readable, Pythonic code
- Proper error handling (no bare exceptions)
- Input validation
- Security considerations (e.g., path traversal prevention)
- Performance considerations (e.g., file size limits)

#### Step 4: Documentation
- Update `ai_tools/__init__.py` if needed for exports
- Add inline comments where logic is non-obvious

#### Step 5: Self-Validation
Before presenting to user:
- Verify all PRD requirements addressed
- Check all error cases implemented
- Confirm output formats match PRD exactly
- Validate type hints are complete

#### Step 6: Ambiguity Check
**If any requirement is unclear, ambiguous, or incomplete:**
- STOP implementation
- Escalate to Agent 1 with specific questions
- Wait for clarified PRD
- Resume implementation

#### Step 7: User Approval
- Present implemented code
- Explain design decisions
- Wait for explicit approval

**Inputs:**
- `PRDs/{function_name}.md`
- Existing codebase structure
- Shared state from Agent 1

**Outputs:**
- `ai_tools/{module}/{function_name}.py` (implementation)
- Updated shared state

**Success Criteria:**
- Code matches PRD specification exactly
- All error cases handled per PRD
- Type hints complete
- Docstring comprehensive
- User approves implementation

**Escalation Triggers:**
- Ambiguous requirement in PRD
- Missing error case definition
- Unclear constraint or validation rule
- Contradictory specifications

---

### 3.3 Agent 3: Test Engineer

**Role:** Write comprehensive test suite

**Responsibilities:**
1. Read PRD and understand all success/error paths
2. Read implementation code
3. Write pytest tests covering all scenarios
4. Execute tests and verify they pass
5. Report coverage and results
6. Escalate to Agent 1 if test case requirements unclear

**Workflow:**

#### Step 1: Test Planning
- Read `PRDs/{function_name}.md` - especially error cases section
- Read implemented code from Agent 2
- Identify all code paths
- List test cases needed:
  - All success scenarios (including edge cases like empty inputs, max size)
  - Each error condition from PRD
  - Boundary conditions
  - Integration points (if applicable)

#### Step 2: Test File Creation
**File location:** `tests/{module_path}/test_{function_name}.py`

**Test structure:**
- Use pytest framework
- Create fixtures for common setups (temp files, mocking)
- Group tests logically (success cases, error cases by type)
- Use parametrize for multiple similar cases
- Mock external dependencies (filesystem, network, etc.)

**Follow existing patterns (see `tests/file_system/test_get_file_data.py`)**

#### Step 3: Test Implementation
Each test should:
- Have descriptive name: `test_{function}_success_{scenario}` or `test_{function}_error_{error_code}`
- Test one specific thing
- Use appropriate assertions
- Mock external dependencies
- Clean up resources (if needed)

**Coverage requirements:**
- Every success case in PRD
- Every error code in PRD
- Edge cases mentioned in constraints
- Boundary conditions (min/max values, empty inputs, etc.)

#### Step 4: Test Execution
- Run pytest locally
- Verify all tests pass
- Check for any warnings or issues
- Measure coverage (aim for 100% of implemented code)

#### Step 5: User Approval
- Present test suite
- Show test results
- Report coverage metrics
- Wait for approval

**Inputs:**
- `PRDs/{function_name}.md`
- `ai_tools/{module}/{function_name}.py` (implementation)
- Existing test patterns

**Outputs:**
- `tests/{module}/test_{function_name}.py`
- Test execution results
- Updated shared state

**Success Criteria:**
- All tests pass
- All PRD scenarios covered
- Tests follow existing patterns
- User approves test suite

**Escalation Triggers:**
- Unclear what to test for a given error case
- PRD doesn't specify expected behavior for edge case
- Implementation behavior doesn't match PRD (may need Agent 2 fix or Agent 1 clarification)

---

### 3.4 Agent 4: Release Manager

**Role:** Package and publish to pip repository

**Responsibilities:**
1. Pre-flight validation checks
2. Version management
3. Build distribution packages
4. Publish to pip repository
5. Documentation updates (CHANGELOG, README)
6. Git tagging

**Workflow:**

#### Step 1: Pre-flight Checks
- Verify all tests pass (run pytest again)
- Check `pyproject.toml` or `setup.py` for current version
- Validate package structure integrity
- Check for uncommitted changes (if applicable)

#### Step 2: Version Management
- Determine version increment (user input or auto-detect):
  - Major: Breaking changes
  - Minor: New features (typical for new tools)
  - Patch: Bug fixes
- Update version in `pyproject.toml` or `setup.py`

#### Step 3: Build Distribution
Follow existing `build_instructions/publishing_steps.md`:
```bash
python -m build
# Generates dist/ files: .whl and .tar.gz
```

#### Step 4: Publishing
**Options:**
- Test PyPI first (recommended for new tools)
- Production PyPI directly

```bash
python -m twine upload dist/*
```

#### Step 5: Documentation Updates
- Update `CHANGELOG.md` with new tool entry
- Update `README.md` if needed (list new tool)
- Commit documentation changes

#### Step 6: Git Operations (if enabled)
- Tag release: `git tag v{version}`
- Push tag: `git push origin v{version}`

#### Step 7: Final Report
- Confirm publication success
- Provide pip install command
- Share PyPI package URL

**Inputs:**
- All tests passing
- `ai_tools/{module}/{function_name}.py`
- `tests/{module}/test_{function_name}.py`
- Existing package configuration

**Outputs:**
- Updated `pyproject.toml` or `setup.py` (version bump)
- Distribution files in `dist/`
- Published package on PyPI
- Updated CHANGELOG.md
- Git tag (optional)

**Success Criteria:**
- Package successfully published
- Installation works: `pip install akhera_ai_tools`
- New tool is importable

---

## 4. State Management

### 4.1 Shared State Schema

LangGraph maintains shared state throughout workflow:

```python
class ToolBuilderState(TypedDict):
    # User input and conversation
    user_input: str
    conversation_history: list[dict]  # Full chat history
    
    # Requirements (Agent 1)
    function_name: str
    prd_content: str
    json_schema: dict
    prd_version: str
    prd_approved: bool
    
    # Implementation (Agent 2)
    module_path: str  # e.g., "ai_tools/file_system"
    implementation_code: str
    implementation_approved: bool
    
    # Testing (Agent 3)
    test_code: str
    test_results: dict
    tests_passed: bool
    tests_approved: bool
    
    # Publishing (Agent 4)
    version_number: str
    publish_target: str  # "test_pypi" or "pypi"
    package_url: str
    
    # Workflow control
    current_agent: str  # "agent_1", "agent_2", "agent_3", "agent_4"
    current_phase: str  # Specific phase within agent
    escalation_active: bool
    escalation_question: str | None
    escalation_from_agent: str | None
    
    # Metadata
    created_at: str
    last_updated: str
    errors: list[str]
```

### 4.2 State Persistence

**File-based persistence:**
- `.agent_state/{function_name}.json` - Current state snapshot
- Enables resume if interrupted
- Audit trail for debugging

**Files created during workflow:**
- `PRDs/{function_name}.md`
- `tool_registry.json` (updated)
- `ai_tools/{module}/{function_name}.py`
- `tests/{module}/test_{function_name}.py`

---

## 5. Workflow Implementation (LangGraph)

### 5.1 Graph Structure

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

workflow = StateGraph(ToolBuilderState)

# Agent 1 nodes
workflow.add_node("agent_1_discovery", agent_1_discovery)
workflow.add_node("agent_1_generate", agent_1_generate_artifacts)
workflow.add_node("agent_1_review", agent_1_user_review)
workflow.add_node("agent_1_save", agent_1_save_artifacts)

# Agent 2 nodes
workflow.add_node("agent_2_implement", agent_2_implement)
workflow.add_node("agent_2_review", agent_2_user_review)

# Agent 3 nodes
workflow.add_node("agent_3_test", agent_3_write_tests)
workflow.add_node("agent_3_execute", agent_3_execute_tests)
workflow.add_node("agent_3_review", agent_3_user_review)

# Agent 4 nodes
workflow.add_node("agent_4_publish", agent_4_publish)
workflow.add_node("agent_4_finalize", agent_4_finalize)

# Set entry point
workflow.set_entry_point("agent_1_discovery")
```

### 5.2 Conditional Routing Examples

```python
# After Agent 1 review
def route_agent_1_review(state: ToolBuilderState) -> str:
    if state["prd_approved"]:
        return "save"
    elif state["escalation_active"]:
        return "discovery"  # Re-gather requirements
    else:
        return "generate"  # Regenerate docs

workflow.add_conditional_edges(
    "agent_1_review",
    route_agent_1_review,
    {
        "save": "agent_1_save",
        "discovery": "agent_1_discovery",
        "generate": "agent_1_generate"
    }
)

# After Agent 2 implementation
def route_agent_2(state: ToolBuilderState) -> str:
    if state["escalation_active"]:
        return "agent_1_discovery"  # Escalate back
    elif state["implementation_approved"]:
        return "agent_3_test"
    else:
        return "agent_2_implement"  # Re-implement

workflow.add_conditional_edges(
    "agent_2_review",
    route_agent_2,
    {
        "agent_1_discovery": "agent_1_discovery",
        "agent_3_test": "agent_3_test",
        "agent_2_implement": "agent_2_implement"
    }
)
```

### 5.3 Human-in-the-Loop Implementation

```python
from langgraph.checkpoint import MemorySaver

# Compile with checkpointing
memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["agent_1_review", "agent_2_review", "agent_3_review"])

# Usage
thread_id = "tool_builder_session_123"
inputs = {"user_input": "I want to create a tool that validates JSON files"}

# Run until first interrupt (agent_1_review)
for event in app.stream(inputs, config={"configurable": {"thread_id": thread_id}}):
    print(event)

# User reviews, provides feedback
user_feedback = {"prd_approved": True}

# Resume from checkpoint
for event in app.stream(user_feedback, config={"configurable": {"thread_id": thread_id}}):
    print(event)
```

---

## 6. Agent Prompts & System Instructions

### 6.1 Agent 1 System Prompt

**Base on existing:** `Prompts/CreateTools.md`

**Key additions:**
- Handle escalations from downstream agents
- Maintain conversation context across interruptions
- Version PRD when updating after escalation
- Validate completeness before generating artifacts

### 6.2 Agent 2 System Prompt

**Base on existing:** `Prompts/ImplementTool.md`

**Key additions:**
- Self-validation checklist against PRD
- Escalation protocol (when and how to escalate)
- Logging standards (from user rules)
- Code documentation requirements (from user rules)

### 6.3 Agent 3 System Prompt

**New prompt needed:**
```
You are a Test Engineer specializing in Python pytest tests.

Your role:
1. Read the PRD and understand ALL success and error paths
2. Read the implementation code
3. Write comprehensive pytest tests covering:
   - All success scenarios
   - Every error code from PRD
   - Edge cases and boundaries
4. Follow existing test patterns in tests/ directory
5. Use fixtures and mocking appropriately
6. Execute tests and report results

Success criteria:
- All tests pass
- 100% coverage of PRD requirements
- Tests follow pytest best practices
```

### 6.4 Agent 4 System Prompt

**New prompt needed:**
```
You are a Release Manager specializing in Python package publishing.

Your role:
1. Validate all pre-flight checks
2. Manage version numbers
3. Build distribution packages
4. Publish to PyPI
5. Update documentation (CHANGELOG, README)
6. Tag releases

Follow existing build instructions in build_instructions/publishing_steps.md
```

---

## 7. User Interaction Model

### 7.1 Approval Gates

**Format:** Natural language + explicit confirmation

**Agent 1 presents:**
```
I've created the following PRD and JSON schema for your review:

[Shows PRD markdown]
[Shows JSON schema]

Please review and let me know:
- Approve: "Looks good, proceed" or "APPROVE"
- Request changes: "Change X to Y" or specific feedback
- Ask questions: Any clarifications needed
```

**User can:**
- Type natural approval: "looks good", "proceed", "yes"
- Request specific changes: "make the max file size 50MB"
- Ask questions: "what about error handling for X?"

**Agent interprets intent and routes accordingly**

### 7.2 Escalation User Experience

**When Agent 2 escalates:**
```
[Agent 2] I've encountered an ambiguity in the PRD:

Question: The PRD says "validate email" but doesn't specify which RFC standard 
to use. Should I implement RFC 5322 (strict) or a simpler regex pattern?

Context: I'm implementing the email_validator function, line 45.

Bringing in Agent 1 to clarify the requirements...

[Agent 1] I see the issue. Let's clarify this with you...
```

---

## 8. Error Handling & Edge Cases

### 8.1 System-Level Errors

**LLM API failures:**
- Retry with exponential backoff (3 attempts)
- If persistent, save state and notify user
- Provide resume capability

**State corruption:**
- Validate state schema at each transition
- Keep backup of last known good state
- Provide rollback capability

**File system errors:**
- Wrap all file I/O in try-catch
- Provide clear error messages
- Don't leave partial files

### 8.2 Agent-Level Errors

**Agent 1:**
- User provides insufficient information → Keep asking questions
- User contradicts themselves → Point out contradiction, clarify
- Cannot generate valid JSON schema → Ask for simpler parameters

**Agent 2:**
- Cannot implement feature → Escalate with specific blocker
- PRD impossible to implement → Escalate to Agent 1
- Code doesn't match PRD → Iterate until it does

**Agent 3:**
- Tests fail → Report to user, may need Agent 2 fix
- Cannot test certain scenario → Escalate to Agent 1 for clarification
- Missing test coverage → Identify gaps, write additional tests

**Agent 4:**
- Publishing fails → Report error, provide manual steps
- Version conflict → Ask user for resolution
- Tests fail during final check → Block publishing, return to Agent 3

---

## 9. Implementation Phases

### Phase 1: Core Agent 1 (MVP)
- Implement Agent 1 discovery, generation, review loop
- File I/O for PRD and JSON schema
- Basic LangGraph structure
- Manual handoff (don't continue to Agent 2 yet)

**Success criteria:**
- Agent 1 can gather requirements
- Generate valid PRD and JSON schema
- User can approve
- Files are saved correctly

### Phase 2: Add Agent 2
- Implement Agent 2 code generation
- Escalation back to Agent 1
- User approval gate

**Success criteria:**
- Agent 2 receives PRD and generates code
- Code matches PRD
- Escalation works
- User can approve implementation

### Phase 3: Add Agent 3
- Implement test generation
- Test execution
- Report results

**Success criteria:**
- Tests cover all PRD requirements
- Tests pass
- User can approve test suite

### Phase 4: Add Agent 4
- Implement publishing workflow
- Version management
- Documentation updates

**Success criteria:**
- Package publishes successfully
- New tool is usable via pip install

### Phase 5: Polish & Optimization
- Improve prompts based on real usage
- Add better error handling
- Optimize state management
- Add logging and observability
- Create CLI interface

---

## 10. Success Metrics

**System-level:**
- End-to-end workflow completion rate
- Time from user input to published package
- Number of escalations per tool (target: < 2)
- User approval success rate per agent

**Quality metrics:**
- PRD completeness (no ambiguities)
- Implementation matches PRD (validated by tests)
- Test coverage (target: 100% of PRD requirements)
- Published package works without issues

**User satisfaction:**
- Number of iterations required per agent
- User feedback on PRD clarity
- User feedback on code quality
- Successful tool usage after publishing

---

## 11. Future Enhancements

**Post-MVP features:**
- Web UI for easier interaction (beyond CLI/chat)
- Multi-tool projects (create related tools together)
- Tool refactoring/updates (not just creation)
- Integration with CI/CD pipelines
- Automatic documentation generation for docs site
- Support for other languages (TypeScript, Java, etc.)
- Template library (common tool patterns)
- Analytics dashboard (tool usage, success rates)

---

## 12. Dependencies & Requirements

### 12.1 Python Packages
```
langgraph>=0.0.20
langchain>=0.1.0
langchain-openai>=0.0.5  # or langchain-anthropic
openai>=1.0.0  # or anthropic
pytest>=7.0.0
python-dotenv>=1.0.0
```

### 12.2 Environment Variables
```
OPENAI_API_KEY=...  # or ANTHROPIC_API_KEY
WORKSPACE_PATH=/path/to/snippets/
PYPI_TOKEN=...  # for Agent 4
```

### 12.3 File Structure
```
snippets/
├── PRDs/
│   ├── {function_name}.md
│   └── multi_agent_tool_builder.md (this document)
├── Prompts/
│   ├── CreateTools.md (Agent 1 base prompt)
│   ├── ImplementTool.md (Agent 2 base prompt)
│   ├── TestTool.md (Agent 3 prompt - to create)
│   └── PublishTool.md (Agent 4 prompt - to create)
├── ai_tools/
│   ├── __init__.py
│   └── {module}/
│       └── {function_name}.py
├── tests/
│   └── {module}/
│       └── test_{function_name}.py
├── .agent_state/
│   └── {function_name}.json (state persistence)
├── tool_registry.json
├── pyproject.toml
└── README.md
```

---

## 13. Acceptance Criteria

**System is considered complete when:**

✅ User can start a conversation with natural language input  
✅ Agent 1 gathers requirements through Q&A  
✅ Agent 1 generates PRD and JSON schema  
✅ User can review, iterate, and approve  
✅ Agent 2 receives PRD and implements matching code  
✅ Agent 2 can escalate back to Agent 1 with questions  
✅ User can approve implementation  
✅ Agent 3 writes comprehensive tests  
✅ Tests execute and pass  
✅ User can approve tests  
✅ Agent 4 publishes package to PyPI  
✅ Published tool is installable and works correctly  
✅ State persists across interruptions  
✅ All approval gates function properly  
✅ Escalation mechanism works bidirectionally  

---

## 14. Open Questions & Decisions Needed

1. **Model Selection:** OpenAI GPT-4 vs Anthropic Claude vs both (user choice)?
2. **Publishing Target:** Always Test PyPI first, or user choice each time?
3. **Version Auto-increment:** Automatic (minor bump) or always ask user?
4. **Git Integration:** Should agents auto-commit, or leave to user?
5. **PRD Versioning:** Track full history or just latest + changelog?
6. **State Persistence:** JSON files or database (SQLite)?
7. **CLI vs API:** Build CLI first, or expose as API/library?
8. **Multi-tenancy:** Support multiple users/sessions simultaneously?

---

## 15. References

- Existing prompts: `Prompts/CreateTools.md`, `Prompts/ImplementTool.md`
- Example PRD: `PRDs/get_file_data.md`
- Example implementation: `ai_tools/file_system/get_file_data.py`
- Example tests: `tests/file_system/test_get_file_data.py`
- Tool registry: `tool_registry.json`
- LangGraph documentation: https://langchain-ai.github.io/langgraph/
- Publishing guide: `build_instructions/publishing_steps.md`

---

**End of PRD**

