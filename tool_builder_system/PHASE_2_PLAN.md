# Phase 2 Implementation Plan

## Overview

Phase 2 adds **Agent 2 (Implementation Specialist)** to the workflow. Agent 2 receives the approved PRD from Agent 1 and implements the Python code according to specifications.

## Current Status

✅ **Phase 1 Complete:**
- Agent 1 requirements gathering
- PRD and JSON schema generation
- User approval loop
- State management
- CLI interface

🔄 **Phase 2 Scope:**
- Agent 2 implementation
- Code generation from PRD
- Escalation mechanism
- Agent 2 approval gate
- Integration with Phase 1 workflow

## Implementation Tasks

### 1. Create Agent 2 System Prompt

**File:** `prompts/agent_2_system_prompt.md`

**Based on:** `Prompts/ImplementTool.md` (existing prompt in parent directory)

**Key Additions:**
- Self-validation checklist against PRD
- Escalation protocol (when/how to escalate to Agent 1)
- Code quality standards
- Documentation requirements

**Content:**
```markdown
# Agent 2: Implementation Specialist - System Prompt

You are an AI assistant acting as an **Implementation Specialist**...

## Your Role

You are the second agent in a 4-agent workflow:
- Agent 1: Requirements (completed - you receive PRD from them)
- **Agent 2 (YOU)**: Implementation (code writing)
- Agent 3: Testing
- Agent 4: Publishing

## Responsibilities

1. Read and understand PRD completely
2. Determine proper module placement in codebase
3. Implement function matching PRD exactly
4. Add logging, documentation, error handling
5. Self-validate against PRD
6. Escalate to Agent 1 if ambiguities discovered

[... detailed instructions based on ImplementTool.md ...]
```

### 2. Implement Agent 2 Class

**File:** `agents/agent_2.py`

```python
class Agent2:
    """Implementation Specialist Agent."""

    def __init__(self, api_key: Optional[str] = None):
        # Initialize Anthropic client
        # Load system prompt

    def implement(self, state: dict) -> dict:
        """
        Generate Python code implementation from PRD.

        Steps:
        1. Read PRD from state
        2. Analyze requirements
        3. Generate code with:
           - Type hints
           - Docstrings
           - Error handling
           - Logging
        4. Self-validate against PRD
        5. Check for ambiguities -> escalate if found

        Returns:
            Updated state with implementation_code
        """

    def validate_implementation(self, state: dict) -> dict:
        """
        Self-validate implementation against PRD.

        Checks:
        - All parameters from PRD implemented
        - All error cases handled
        - Type hints complete
        - Docstring comprehensive

        Returns:
            Updated state with validation results
        """

    def check_for_escalation(self, state: dict) -> dict:
        """
        Check if any requirements are ambiguous.

        If ambiguous:
        - Set escalation_active = True
        - Set escalation_question with specific question
        - Set escalation_from_agent = "agent_2"

        Returns:
            Updated state
        """
```

### 3. Update Workflow Graph

**File:** `graph.py`

**Changes:**

```python
# Add Agent 2 nodes
workflow.add_node("agent_2_implement", self._agent_2_implement_node)
workflow.add_node("agent_2_validate", self._agent_2_validate_node)
workflow.add_node("agent_2_review", self._agent_2_review_node)

# Update edges
# Phase 1 completion -> Agent 2 implementation
workflow.add_edge("complete_phase_1", "agent_2_implement")

# Agent 2 implementation -> validation
workflow.add_edge("agent_2_implement", "agent_2_validate")

# Validation -> review (with conditional routing)
workflow.add_conditional_edges(
    "agent_2_validate",
    self._route_after_agent_2_validation,
    {
        "escalate": "agent_1_discovery",  # Back to Agent 1
        "review": "agent_2_review",       # User approval
        "retry": "agent_2_implement"      # Retry implementation
    }
)

# Review -> conditional routing
workflow.add_conditional_edges(
    "agent_2_review",
    self._route_after_agent_2_review,
    {
        "approved": "complete_phase_2",
        "iterate": "agent_2_implement",
        "escalate": "agent_1_discovery"
    }
)
```

**Routing Functions:**

```python
def _route_after_agent_2_validation(
    self, state: ToolBuilderState
) -> Literal["escalate", "review", "retry"]:
    """Route after Agent 2 validation."""
    if state.get("escalation_active"):
        return "escalate"
    elif state.get("implementation_code"):
        return "review"
    else:
        return "retry"

def _route_after_agent_2_review(
    self, state: ToolBuilderState
) -> Literal["approved", "iterate", "escalate"]:
    """Route after Agent 2 user review."""
    if state.get("implementation_approved"):
        return "approved"
    elif state.get("escalation_active"):
        return "escalate"
    else:
        return "iterate"
```

### 4. Update State Schema

**File:** `state.py`

**No changes needed** - Phase 2 fields already defined:
- `module_path`
- `implementation_code`
- `implementation_approved`

### 5. Update Main CLI

**File:** `main.py`

**Changes:**

```python
# After Phase 1 completion, continue to Phase 2
if latest_state.get("prd_approved"):
    print_system_message("Phase 1 complete! Starting Phase 2...")

    # Continue workflow to Agent 2
    # (workflow will automatically continue to agent_2_implement node)

# Add handling for Agent 2 review phase
elif current_phase == "agent_2_review":
    # User needs to approve implementation
    print("\n👤 You (review the code, 'approve' to proceed):")
    user_feedback = input().strip()

    if user_feedback.lower() in ["quit", "exit", "q"]:
        break

    # Update state with user feedback
    latest_state = agent_2.review(latest_state, user_feedback)
```

### 6. Implement Escalation Back to Agent 1

**Update Agent 1:** Add method to handle escalation

```python
# In agent_1.py

def handle_escalation(self, state: dict, escalation_question: str) -> dict:
    """
    Handle escalation from Agent 2/3/4.

    Steps:
    1. Present escalation question to user
    2. Discuss and clarify
    3. Update PRD and JSON schema
    4. Increment version (e.g., 1.0 -> 1.1)
    5. Clear escalation flag
    6. Return to requesting agent

    Returns:
        Updated state with clarified requirements
    """
```

**Update Workflow:** Add escalation routing

```python
# When escalation_active is True, route back to Agent 1
# Agent 1 handles clarification
# Then routes back to requesting agent
```

### 7. Add File Saving for Implementation

**New File:** `file_operations.py`

```python
class FileOperations:
    """Handle file operations for saving PRD, code, tests."""

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)

    def save_prd(self, function_name: str, prd_content: str) -> str:
        """Save PRD to PRDs/{function_name}.md"""
        prd_path = self.workspace_path / "PRDs" / f"{function_name}.md"
        prd_path.parent.mkdir(exist_ok=True, parents=True)

        with open(prd_path, 'w') as f:
            f.write(prd_content)

        return str(prd_path)

    def save_implementation(
        self,
        function_name: str,
        module_path: str,
        code: str
    ) -> str:
        """Save implementation to ai_tools/{module}/{function_name}.py"""
        impl_path = self.workspace_path / module_path / f"{function_name}.py"
        impl_path.parent.mkdir(exist_ok=True, parents=True)

        with open(impl_path, 'w') as f:
            f.write(code)

        return str(impl_path)

    def update_tool_registry(
        self,
        function_name: str,
        json_schema: dict
    ) -> str:
        """Update tool_registry.json with new schema"""
        registry_path = self.workspace_path / "tool_registry.json"

        # Read existing registry
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                registry = json.load(f)
        else:
            registry = {}

        # Add new schema
        registry.update(json_schema)

        # Write back
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        return str(registry_path)
```

### 8. Create Tests for Phase 2

**File:** `tests/test_agent_2_integration.py`

```python
class TestAgent2Integration:
    """Integration tests for Agent 2."""

    def test_agent_2_initialization(self):
        """Test Agent 2 initializes correctly."""

    def test_implementation_generation(self):
        """Test code generation from PRD."""

    def test_validation_against_prd(self):
        """Test self-validation catches missing requirements."""

    def test_escalation_detection(self):
        """Test ambiguity detection triggers escalation."""

    def test_implementation_approval(self):
        """Test user approval flow."""

    def test_implementation_iteration(self):
        """Test handling user feedback for changes."""

    def test_file_saving(self):
        """Test implementation is saved to correct path."""
```

### 9. Update Documentation

**Files to Update:**
- `README.md` - Update status to Phase 2
- `CHANGELOG.md` - Document Phase 2 features

## Implementation Order

1. ✅ Create Agent 2 system prompt (`prompts/agent_2_system_prompt.md`)
2. ✅ Implement Agent 2 class (`agents/agent_2.py`)
3. ✅ Update workflow graph with Agent 2 nodes (`graph.py`)
4. ✅ Implement escalation handling in Agent 1 (`agents/agent_1.py`)
5. ✅ Create file operations utilities (`file_operations.py`)
6. ✅ Update main CLI to handle Agent 2 review (`main.py`)
7. ✅ Write integration tests (`tests/test_agent_2_integration.py`)
8. ✅ Test end-to-end Phase 1 + Phase 2 workflow
9. ✅ Update documentation

## Testing Strategy

### Unit Tests
- Agent 2 initialization
- Code generation
- Validation logic
- Escalation detection

### Integration Tests
- Full workflow: Agent 1 -> Agent 2
- Escalation: Agent 2 -> Agent 1 -> Agent 2
- File saving operations
- State persistence across phases

### Manual Testing
- Run CLI end-to-end
- Test various tool types
- Test escalation scenarios
- Verify file outputs

## Success Criteria

Phase 2 is complete when:

- ✅ Agent 2 can read PRD from state
- ✅ Agent 2 generates valid Python code
- ✅ Code matches PRD specifications exactly
- ✅ All error cases from PRD are handled
- ✅ Type hints and docstrings are complete
- ✅ Agent 2 can escalate to Agent 1 with questions
- ✅ Agent 1 can handle escalation and return to Agent 2
- ✅ User can approve/iterate on implementation
- ✅ Implementation is saved to correct file path
- ✅ PRD is saved to PRDs/ directory
- ✅ tool_registry.json is updated
- ✅ All tests pass
- ✅ End-to-end workflow works from user input to saved code

## Example Phase 2 Workflow

```
[User] "I want a JSON validator"
    ↓
[Agent 1] Gathers requirements, generates PRD
    ↓
[User] Approves PRD
    ↓
[Agent 2] Reads PRD, generates Python code
    ↓
[Agent 2] Self-validates against PRD
    ↓
[User] Reviews code implementation
    ↓
Option A: [User] Approves → Files saved → Phase 2 complete
Option B: [User] Requests changes → Agent 2 iterates
Option C: [Agent 2] Finds ambiguity → Escalates to Agent 1 → Clarifies → Returns
```

## Known Challenges

1. **Code Quality:** Ensuring generated code follows best practices
   - Solution: Detailed system prompt with examples
   - Include logging standards from user rules

2. **Module Path Detection:** Determining correct ai_tools subdirectory
   - Solution: Ask Agent 2 to analyze existing structure
   - Provide clear guidelines in prompt

3. **Escalation Triggers:** When to escalate vs. make assumptions
   - Solution: Conservative approach - escalate on any ambiguity
   - Provide escalation examples in prompt

4. **State Handoff:** Maintaining context between Agent 1 and 2
   - Solution: LangGraph handles this via shared state
   - Ensure all necessary fields populated

## Resources

- Existing implementation prompt: `Prompts/ImplementTool.md`
- Example implementation: `ai_tools/file_system/get_file_data.py`
- Example PRD: `PRDs/get_file_data.md`
- LangGraph conditional edges: [docs](https://langchain-ai.github.io/langgraph/how-tos/branching/)

## Next Steps After Phase 2

Once Phase 2 is complete and tested:
- **Phase 3:** Implement Agent 3 (Test Engineer)
- **Phase 4:** Implement Agent 4 (Release Manager)
- Polish error handling across all agents
- Add observability/logging
- Create web UI (optional)

---

**Target Completion:** TBD
**Dependencies:** Phase 1 complete ✅
**Blockers:** None
