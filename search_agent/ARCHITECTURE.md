# Search Agent Architecture

This document provides a detailed overview of the search agent's architecture, design patterns, and implementation approach.

## Table of Contents

1. [System Overview](#system-overview)
2. [State Machine Design](#state-machine-design)
3. [State Schema](#state-schema)
4. [Node Specifications](#node-specifications)
5. [Data Flow](#data-flow)
6. [Service Layer](#service-layer)
7. [Design Patterns](#design-patterns)
8. [Error Handling Strategy](#error-handling-strategy)

---

## System Overview

The search agent is a LangGraph-based state machine that orchestrates natural language search queries against an Elasticsearch backend. It intelligently handles both simple and complex queries through a planning-execution pattern.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Search/List Agent                         │
│                                                              │
│  User Query → Classifier → Planner → Executor → Formatter   │
│                                            ↑         ↓       │
│                                            └─────────┘       │
│                                            (Loop Back)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │  Elasticsearch   │
                    │     Service      │
                    └──────────────────┘
```

### Core Principles

1. **Planning-Execution Separation**: Plan what to do before executing
2. **High-Level Planning**: Plans describe intent, not implementation
3. **Full Result Passing**: Pass complete ES documents between steps
4. **Loop-Based Execution**: Single executor node loops for multi-step queries
5. **State-Driven Flow**: All data flows through immutable state

---

## State Machine Design

### Node Graph

```
        START
          ↓
    ┌─────────────┐
    │ Classifier  │
    └──────┬──────┘
           │
      ┌────┴────┐
      │         │
   search     other
      │         │
      │         └──→ [Future: Other Agents]
      ↓
 ┌─────────────┐
 │   Planner   │
 └──────┬──────┘
        │
        ↓
 ┌─────────────┐
 │  Executor   │◄──┐
 └──────┬──────┘   │
        │          │
    ┌───┴───┐      │
    │ More  │ Yes ─┘
    │Steps? │
    └───┬───┘
        │ No
        ↓
 ┌─────────────┐
 │  Formatter  │
 └──────┬──────┘
        │
        ↓
       END
```

### Routing Logic

**After Classifier:**
```python
if state["intent"] == "search":
    return "planner"
else:
    return "formatter"  # Or route to other agents
```

**After Planner:**
```python
# Always proceed to executor
return "executor"
```

**After Executor (Loop Decision):**
```python
if state.get("pending_clarification"):
    return "executor"  # Resume after interrupt
elif state.get("error"):
    return "formatter"
elif state["current_step"] < state["total_steps"]:
    return "executor"  # Loop back for next step
else:
    return "formatter"  # All steps complete
```

---

## State Schema

The state is a `TypedDict` that persists across all nodes. See [core/state.py](./core/state.py) for complete implementation.

### State Structure

```python
class SearchAgentState(TypedDict):
    # ===== INPUT =====
    user_query: str                        # Original user query
    conversation_id: str                   # Unique conversation ID
    conversation_history: List[Dict]       # Chat history

    # ===== CLASSIFICATION =====
    intent: str                            # "search" | "move" | "delete" | etc.
    classification_confidence: str         # "high" | "medium" | "low"
    classification_reasoning: str          # Why this classification

    # ===== PLANNING =====
    query_plan: Optional[QueryPlan]        # Complete execution plan
    total_steps: int                       # Number of steps in plan
    current_step: int                      # Current step being executed

    # ===== EXECUTION =====
    step_results: Dict[int, StepResult]    # Results from each step
    final_results: Optional[Any]           # Final results for user

    # ===== ERROR HANDLING =====
    error: Optional[str]                   # Fatal error message
    retry_count: int                       # Current retry attempt

    # ===== HUMAN-IN-THE-LOOP =====
    pending_clarification: Optional[Dict]  # Active clarification request
    user_clarification_response: Optional[str]

    # ===== OUTPUT =====
    response_message: str                  # Final formatted response
    metadata: Dict[str, Any]               # Execution metadata
```

### Key Design Choices

**1. Immutable State Updates**
Each node returns a new state dict rather than mutating:
```python
def node(state: SearchAgentState) -> SearchAgentState:
    return {**state, "new_field": value}
```

**2. Full Document Storage**
Store complete Elasticsearch documents in `step_results`:
```python
step_results[1] = {
    "_source": {...},  # Complete ES document
    "metadata": {
        "query": {...},
        "execution_time_ms": 150,
        "result_count": 1
    }
}
```

**Why?** LLM can extract any field it needs; no hardcoded extraction logic required.

**3. Typed Models**
Use Pydantic models for validation (see [core/models.py](./core/models.py)):
```python
class QueryPlan(BaseModel):
    plan_type: Literal["single_step", "multi_step"]
    reasoning: str
    total_steps: int
    steps: List[Step]
```

---

## Node Specifications

### Node 1: Query Classifier (Phase 4)

**Purpose**: Determine user intent (search, move, delete, etc.)

**Inputs**:
- `user_query`
- `conversation_history`

**Outputs**:
- `intent`
- `classification_confidence`
- `classification_reasoning`

**LLM**: Claude Sonnet 4.5 with structured output

**Processing Time**: ~1-2s

---

### Node 2: Query Planner (Phase 2)

**Purpose**: Analyze query and create execution plan

**Inputs**:
- `user_query`
- `intent`
- ES mapping (from static resources)

**Outputs**:
- `query_plan`
- `total_steps`
- `current_step` (initialized to 1)

**LLM**: Claude Sonnet 4.5 with extensive prompt

**Key Logic**:
```python
# Gap Analysis
if user_references_folder_by_name and documents_need_folder_id:
    plan_type = "multi_step"
    steps = [
        {"step": 1, "description": "Find folder by name"},
        {"step": 2, "description": "Find documents in that folder"}
    ]
else:
    plan_type = "single_step"
```

**Processing Time**: ~2-3s

---

### Node 3: Query Executor (Phase 3)

**Purpose**: Execute plan step-by-step

**Inputs**:
- `query_plan`
- `current_step`
- `step_results` (from previous steps)

**Outputs**:
- `step_results` (updated)
- `current_step` (incremented)
- `final_results` (when done)
- `pending_clarification` (if needed)
- `error` (if fatal)

**LLM**: Claude Sonnet 4.5 for query generation

**Operations Per Step**:
1. Generate ES query (using existing tool)
2. Validate query
3. Execute against ES service
4. Analyze result
5. Handle errors/ambiguities
6. Store full result
7. Loop decision

**Processing Time**: ~3-5s per step

---

### Node 4: Response Formatter (Phase 4)

**Purpose**: Format results for user-friendly output

**Inputs**:
- `final_results`
- `query_plan`
- `error` (if any)

**Outputs**:
- `response_message`
- `metadata`

**LLM**: Optional (for enhanced formatting)

**Processing Time**: <1s

---

## Data Flow

### Example: Multi-Step Query

**User Query**: "List documents in Tax Documents folder"

**Flow**:

1. **Classifier**:
   ```python
   state["intent"] = "search"
   state["classification_confidence"] = "high"
   ```

2. **Planner**:
   ```python
   state["query_plan"] = {
       "plan_type": "multi_step",
       "total_steps": 2,
       "steps": [
           {"step": 1, "description": "Find folder named 'Tax Documents'"},
           {"step": 2, "description": "Find documents in that folder"}
       ]
   }
   state["current_step"] = 1
   ```

3. **Executor - Step 1**:
   ```python
   # Generate query for "Find folder named 'Tax Documents'"
   query = {
       "bool": {
           "must": [
               {"term": {"entityType.keyword": "FOLDER"}},
               {"term": {"commonAttributes.name.keyword": "Tax Documents"}}
           ]
       }
   }

   # Execute → Get folder with ID "abc-123"
   state["step_results"][1] = {
       "_source": {
           "systemAttributes": {"id": "abc-123"},
           "commonAttributes": {"name": "Tax Documents"},
           ...
       }
   }

   state["current_step"] = 2  # Increment
   # Return to executor (loop back)
   ```

4. **Executor - Step 2**:
   ```python
   # Generate query using result from step 1
   # LLM extracts folder ID: "abc-123"
   query = {
       "bool": {
           "must": [
               {"term": {"entityType.keyword": "DOCUMENT"}},
               {"term": {"systemAttributes.parentId.keyword": "abc-123"}}
           ]
       }
   }

   # Execute → Get 5 documents
   state["final_results"] = [doc1, doc2, doc3, doc4, doc5]
   # All steps complete → proceed to formatter
   ```

5. **Formatter**:
   ```python
   state["response_message"] = """
   Found 5 documents in 'Tax Documents' folder:

   1. W2_2024.pdf
   2. Receipt_Jan.pdf
   3. Invoice_2024.pdf
   4. Tax_Summary.xlsx
   5. Deductions.pdf
   """
   ```

---

## Service Layer

### Elasticsearch Service

Located in `services/elasticsearch_service.py`.

**Interface**:
```python
class ElasticsearchService:
    def search(self, query: Dict[str, Any], size: int = 100) -> Dict[str, Any]:
        """Execute Elasticsearch query and return results."""

    def validate_query(self, query: Dict[str, Any]) -> List[str]:
        """Validate query syntax and field existence."""
```

**Phase 1**: Mock implementation returns sample data
**Phase 3+**: Can be replaced with real ES client

---

### LLM Service

Located in `services/llm_service.py`.

**Interface**:
```python
class LLMService:
    def call_with_retry(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
        temperature: float = 0.0
    ) -> str:
        """Call Anthropic API with retry logic."""
```

**Features**:
- Exponential backoff retry
- Error categorization
- JSON response parsing
- Timeout handling

---

## Design Patterns

### 1. Planning-Execution Separation

**Pattern**: Separate "what to do" (planner) from "how to do it" (executor)

**Benefits**:
- Easier debugging (inspect plan before execution)
- Clear separation of concerns
- Can retry execution without re-planning
- User transparency (show plan to user)

**Implementation**:
```python
# Planner outputs high-level intent
plan = {
    "steps": [
        {"description": "Find folder named 'Tax Documents'"}
    ]
}

# Executor translates to ES query
executor.generate_query(plan.steps[0])  # → ES DSL
```

---

### 2. Full Result Passing

**Pattern**: Pass complete ES documents between steps, let LLM extract needed fields

**Benefits**:
- No hardcoded field extraction logic
- Flexible for any query pattern
- Self-correcting (LLM can try different fields)
- Easier debugging (see full context)

**Implementation**:
```python
# Step 1 stores full document
step_results[1] = {"_source": {...}}  # Complete ES document

# Step 2 LLM extracts what it needs
prompt = f"""
Previous step returned:
{json.dumps(step_results[1])}

Extract the folder ID and use it in your query.
"""
```

---

### 3. Loop Node Architecture

**Pattern**: Single executor node loops back to itself for multi-step execution

**Benefits**:
- Simpler than multiple specialized nodes (POC appropriate)
- All execution logic in one place
- Easier to maintain and iterate
- Can refactor later if needed

**Implementation**:
```python
def route_after_executor(state):
    if state["current_step"] < state["total_steps"]:
        return "executor"  # Loop back
    else:
        return "formatter"  # Done
```

---

### 4. State-Driven Flow

**Pattern**: All data flows through immutable state; nodes are pure functions

**Benefits**:
- Easier testing (pure functions)
- Built-in checkpointing (LangGraph)
- Replay-ability for debugging
- Multi-turn conversation support

**Implementation**:
```python
def node(state: SearchAgentState) -> SearchAgentState:
    # Pure function: input state → output state
    result = process(state["user_query"])
    return {**state, "result": result}  # Immutable update
```

---

## Error Handling Strategy

### Error Categories

1. **Validation Errors** (before execution)
   - Invalid ES syntax
   - Non-existent fields
   - **Recovery**: Regenerate query with feedback (max 3 attempts)

2. **Execution Errors** (API failures)
   - Network timeout
   - 500 server error
   - **Recovery**: Retry with exponential backoff (max 2 attempts)

3. **Critical Errors** (cannot proceed)
   - Step 1 returns 0 results in multi-step
   - Max retries exceeded
   - **Recovery**: None, set error and proceed to formatter

4. **Ambiguity** (multiple valid results)
   - Step 1 returns 3 folders with same name
   - **Recovery**: Ask user to clarify (interrupt)

### Retry Logic

```python
MAX_RETRIES = 3
BACKOFF_DELAYS = [2, 4, 8]  # seconds

for attempt in range(MAX_RETRIES):
    try:
        result = execute()
        return result
    except RetryableError as e:
        if attempt < MAX_RETRIES - 1:
            time.sleep(BACKOFF_DELAYS[attempt])
            continue
        else:
            raise FatalError(f"Failed after {MAX_RETRIES} attempts")
```

### Human-in-the-Loop

**Trigger**: Multiple results when expecting single (e.g., step 1 folder lookup)

**Flow**:
```python
# 1. Executor detects ambiguity
if result_count > 1 and current_step < total_steps:
    state["pending_clarification"] = {
        "type": "multiple_choice",
        "question": "I found 3 folders. Which one?",
        "options": [...]
    }
    # LangGraph interrupts execution

# 2. User responds with selection
user_response = "2"  # Selected option 2

# 3. Graph resumes
selected = state["pending_clarification"]["options"][1]
state["step_results"][current_step] = selected
state["pending_clarification"] = None
# Continue to next step
```

---

## Performance Considerations

### Expected Latencies (POC Phase)

- **Classifier**: ~1-2s
- **Planner**: ~2-3s
- **Executor per step**: ~3-5s
- **Formatter**: <1s

**Total for single-step**: ~7-11s
**Total for two-step**: ~12-19s

### Optimization Opportunities (Post-POC)

1. **Caching**: Cache folder name → ID mappings
2. **Parallel Execution**: Where dependencies allow
3. **Faster Models**: Use Haiku for classification
4. **Query Optimization**: Combine filters efficiently
5. **Result Pagination**: Stream large result sets

---

## Security Considerations

1. **Input Validation**: Validate all user inputs
2. **Query Sanitization**: Prevent ES injection
3. **API Key Management**: Never log API keys
4. **PCI Data**: Respect `isPci` flags
5. **Authorization**: Enforce access controls (future)

---

## Extensibility

### Adding New Agents

The classifier can route to different agent types:

```python
def route_after_classify(state):
    if state["intent"] == "search":
        return "planner"
    elif state["intent"] == "move":
        return "move_agent"  # Future
    elif state["intent"] == "delete":
        return "delete_agent"  # Future
```

### Adding New Node Types

Can refactor executor into specialized nodes:

```
Executor (current)
    ↓
Query Generator → Validator → Executor → Analyzer
```

---

## Testing Strategy

### Unit Tests (Each Phase)
- Test individual node functions
- Test state transformations
- Test validation logic
- Test error handling

### Integration Tests (Phase 6)
- Full graph execution
- Single-step queries
- Multi-step queries
- Error scenarios
- Interrupt/resume flows

### Performance Tests (Phase 6)
- Latency benchmarks
- Token usage tracking
- Memory profiling

---

## References

- [Product Requirements Document](../PRDs/langgraph.md)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [State Schema](./core/state.py)
- [Phase Handoff Guide](./PHASE_HANDOFF.md)
