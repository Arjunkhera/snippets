# Product Requirements Document (PRD)
# Elasticsearch Search/List Agent for Document Management Platform

**Version:** 1.0  
**Date:** November 16, 2025  
**Status:** POC Phase  
**Author:** AI Architecture Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals and Non-Goals](#3-goals-and-non-goals)
4. [Design Approach & Rationale](#4-design-approach--rationale)
5. [System Architecture (HLD)](#5-system-architecture-hld)
6. [Detailed Component Specifications](#6-detailed-component-specifications)
7. [State Management](#7-state-management)
8. [Multi-Step Query Patterns & Examples](#8-multi-step-query-patterns--examples)
9. [Prompt Engineering Guidelines](#9-prompt-engineering-guidelines)
10. [Error Handling & Recovery](#10-error-handling--recovery)
11. [Success Criteria](#11-success-criteria)
12. [Future Considerations](#12-future-considerations)

---

## 1. Executive Summary

### 1.1 Overview
This document specifies the design and implementation of an AI-powered search agent for a document management platform (similar to Google Drive). The agent uses LangGraph to orchestrate natural language queries into Elasticsearch DSL queries, handling both simple single-step searches and complex multi-step queries that require sequential information resolution.

### 1.2 Key Capabilities
- Natural language search query classification and execution
- Intelligent multi-step query planning for complex searches
- Automatic resolution of entity references (e.g., folder names to folder IDs)
- Human-in-the-loop clarification for ambiguous queries
- Robust error handling and retry mechanisms

### 1.3 Technology Stack
- **LangGraph**: State machine orchestration
- **LangChain**: LLM interaction layer
- **Elasticsearch**: Document/folder storage and search
- **LLM**: Claude/GPT-4 for query understanding and generation

---

## 2. Problem Statement

### 2.1 Core Challenge
The document management platform stores documents and folders in Elasticsearch with a complex schema (entities-v4 index). Users want to search using natural language queries, but there's a fundamental structural impediment:

**The Parent-Child ID Problem:**
- Users reference entities naturally: "Show documents in 'Tax Documents' folder"
- Elasticsearch stores parent-child relationships via UUIDs: `systemAttributes.parentId`
- Documents don't store parent folder names, only parent folder IDs
- Folders don't directly store their name in a queryable format for parent-child operations

**Example:**
```
User Query: "List all documents in the 'Tax Documents' folder"

What user provides: Folder name ("Tax Documents")
What ES needs: Folder ID ("4d3a2df1-1678-498c-99ee-b55960542d30")

Gap: Cannot query documents.parentId = "Tax Documents" (it's an ID field, not a name)
```

### 2.2 Secondary Challenges

1. **Complex Schema**: The entities-v4 index has 100+ fields across multiple nested structures
2. **Multiple Entity Types**: DOCUMENT and FOLDER entities with different attributes
3. **Ambiguous References**: Users may reference entities by name or ID without clear distinction
4. **Hierarchical Navigation**: Folder paths, parent-child relationships, sibling queries
5. **Relationship-Based Queries**: Finding entities with shared attributes (same owner, category, etc.)

### 2.3 Current State

An existing Elasticsearch query generator prompt exists that:
- ✅ Works "okayish" for single-step queries
- ✅ Understands the ES mapping
- ✅ Generates syntactically valid ES DSL
- ❌ Cannot handle multi-step resolution scenarios
- ❌ Doesn't know when to break queries into multiple steps
- ❌ Has no mechanism for using results from one query in another

---

## 3. Goals and Non-Goals

### 3.1 Goals (POC Phase)

**Primary Goals:**
1. Enable natural language search queries for documents and folders
2. Automatically detect when multi-step queries are needed
3. Successfully resolve folder name → folder ID → documents queries
4. Handle 80%+ of common user search patterns
5. Provide clear feedback when queries cannot be answered

**Secondary Goals:**
1. Support human-in-the-loop for ambiguous queries
2. Graceful error handling and recovery
3. Reuse existing ES query generation logic
4. Maintain conversation context for follow-up queries

### 3.2 Non-Goals (POC Phase)

1. ❌ Perfect accuracy (targeting 80%+ success rate)
2. ❌ Advanced query optimization
3. ❌ Real-time streaming results
4. ❌ Complex aggregations or analytics queries
5. ❌ Multi-user collaboration features
6. ❌ Fine-tuned domain-specific models
7. ❌ Sub-100ms response times

### 3.3 Success Metrics

- **Query Classification Accuracy**: >95% correct identification of search queries
- **Single-Step Query Success**: >90% successful execution
- **Multi-Step Query Success**: >80% successful execution
- **Ambiguity Detection**: <5% false positives (unnecessary clarifications)
- **User Satisfaction**: Subjective evaluation during POC testing

---

## 4. Design Approach & Rationale

### 4.1 Architecture Pattern: Agent-Based Sequential Planner

**Chosen Approach:**
A three-node LangGraph state machine with a planning-execution separation pattern.

**Why This Approach:**

#### 4.1.1 Planning-Execution Separation

**Decision:** Separate planning (what to do) from execution (how to do it)

**Rationale:**
- **Clarity**: Planner focuses on high-level strategy, executor focuses on implementation
- **Debuggability**: Can inspect the plan before executing costly operations
- **Reusability**: Same executor can handle any plan structure
- **Error Recovery**: Can retry execution without re-planning
- **Transparency**: User can see what the system intends to do

**Alternative Considered:** Monolithic node that plans and executes
- **Rejected because:** Harder to debug, mixing concerns, can't inspect plan before execution

#### 4.1.2 High-Level Planning vs. Prescriptive Planning

**Decision:** Planner outputs high-level natural language step descriptions, not detailed ES query structures

**Rationale:**
- **Flexibility**: Handles any multi-step pattern, not just pre-defined ones
- **Maintainability**: No hardcoded field mappings in planner
- **LLM Strengths**: LLMs excel at high-level reasoning, not schema memorization
- **Reuse**: Leverages existing ES query generation prompt
- **Extensibility**: Easy to add new query patterns without modifying planner

**Example:**
```json
// Good (high-level)
{
  "step": 1,
  "description": "Find the folder named 'Tax Documents'"
}

// Bad (too prescriptive)
{
  "step": 1,
  "entity_type": "FOLDER",
  "field": "commonAttributes.name.keyword",
  "operator": "term",
  "value": "Tax Documents"
}
```

#### 4.1.3 Full Result Passing vs. Selective Extraction

**Decision:** Pass complete ES document from step N to step N+1, let LLM extract what it needs

**Rationale:**
- **Simplicity**: No extraction logic to maintain
- **LLM Capability**: LLMs excel at JSON parsing and field extraction
- **Flexibility**: Works for any field that might be needed
- **Self-Correcting**: LLM can try different fields if first attempt fails
- **Future-Proof**: Handles new patterns without code changes

**Alternative Considered:** Hardcoded extraction rules (if folder query, extract ID; if category query, extract category)
- **Rejected because:** Brittle, incomplete coverage, maintenance burden

#### 4.1.4 Loop Node vs. Multiple Specialized Nodes

**Decision:** Single executor node that loops for multi-step execution

**Rationale:**
- **POC Appropriate**: Simpler to build and test
- **Maintainable**: All execution logic in one place
- **Sufficient**: Handles the major use cases we need
- **Evolvable**: Can extract into specialized nodes later if needed

**Alternative Considered:** Separate nodes for query generation, validation, execution, result analysis
- **Rejected because:** Over-engineering for POC, harder to iterate, more boilerplate

#### 4.1.5 LangGraph vs. Simple Python Loop

**Decision:** Use LangGraph despite its complexity

**Rationale:**
- **Already Available**: Starter service uses LangGraph
- **State Management**: Built-in checkpointing and persistence
- **Human-in-the-Loop**: Native interrupt support for clarifications
- **Multi-Turn**: Conversation context across sessions
- **Future Integration**: Needs to work with other agents (move, delete, etc.)

---

## 5. System Architecture (HLD)

### 5.1 Overall System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Search/List Agent                         │
│                                                              │
│  ┌──────────────┐                                           │
│  │   START      │ User sends natural language query         │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │  Node 1: Query Classifier                        │      │
│  │  ─────────────────────────                       │      │
│  │  Purpose: Determine if this is a search/list     │      │
│  │           operation or something else             │      │
│  │                                                    │      │
│  │  Input:  user_query                               │      │
│  │  Output: intent ("search" | "move" | "delete")    │      │
│  │  LLM:    Yes (classification)                     │      │
│  └──────┬───────────────────────────────────────────┘      │
│         │                                                    │
│    ┌────┴─────┐                                             │
│    ▼          ▼                                             │
│  search    other intent                                     │
│    │          │                                             │
│    │          ▼                                             │
│    │    ┌──────────────┐                                   │
│    │    │ Route to     │                                   │
│    │    │ Other Agent  │                                   │
│    │    └──────────────┘                                   │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────────────────────────────────────────┐     │
│  │  Node 2: Query Planner                           │     │
│  │  ──────────────────                              │     │
│  │  Purpose: Determine if query needs 1 or N steps  │     │
│  │           and create high-level plan              │     │
│  │                                                    │     │
│  │  Input:  user_query, ES mapping, examples         │     │
│  │  Output: query_plan {                             │     │
│  │            plan_type: "single_step" | "multi_step"│     │
│  │            steps: [                                │     │
│  │              {step: 1, description: "..."},       │     │
│  │              {step: 2, description: "..."}        │     │
│  │            ]                                       │     │
│  │          }                                         │     │
│  │  LLM:    Yes (planning & gap analysis)            │     │
│  └──────┬───────────────────────────────────────────┘     │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────┐     │
│  │  Node 3: Query Executor (Loop Node)              │     │
│  │  ───────────────────────────────                 │     │
│  │  Purpose: Execute the plan step-by-step          │     │
│  │                                                    │     │
│  │  For each step:                                   │     │
│  │    1. Generate ES query (LLM)                     │     │
│  │    2. Validate query                              │     │
│  │    3. Execute against ES service                  │     │
│  │    4. Analyze result                              │     │
│  │    5. Handle errors/ambiguities                   │     │
│  │    6. Store full result                           │     │
│  │    7. If more steps: loop back                    │     │
│  │    8. If done: proceed to format                  │     │
│  │                                                    │     │
│  │  Input:  query_plan, current_step,                │     │
│  │          previous_step_results                     │     │
│  │  Output: step_results, final_results              │     │
│  │  LLM:    Yes (ES query generation)                │     │
│  │  API:    Yes (ES service calls)                   │     │
│  └──────┬───────────────────────────────────────────┘     │
│         │          ▲                                       │
│         │          │                                       │
│         │          │ Loop back for next step              │
│         │          │ (conditional edge)                   │
│         │          │                                       │
│         │    ┌─────┴─────────┐                           │
│         │    │ More steps?   │                           │
│         │    │ Clarification?│                           │
│         │    │ Error retry?  │                           │
│         │    └───────────────┘                           │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Node 4: Response Formatter                      │    │
│  │  ───────────────────────                         │    │
│  │  Purpose: Format final results for user          │    │
│  │                                                    │    │
│  │  Input:  step_results, query_plan                 │    │
│  │  Output: response_message                         │    │
│  │  LLM:    Optional (formatting assistance)         │    │
│  └──────┬───────────────────────────────────────────┘    │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │     END      │                                         │
│  └──────────────┘                                         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 5.2 Node Count & Complexity

**Total Nodes: 4**
1. Query Classifier
2. Query Planner
3. Query Executor (Loop Node)
4. Response Formatter

**Rationale for Minimal Node Count:**
- POC phase prioritizes speed of development
- Each node has clear, focused responsibility
- Loop node handles complexity internally (appropriate for POC)
- Can refactor into more nodes later if needed

### 5.3 Data Flow

```
User Query
    ↓
[Classifier] 
    ↓
  intent
    ↓
[Planner]
    ↓
  query_plan {
    steps: [
      {step: 1, description: "Find folder X"},
      {step: 2, description: "Find docs in folder"}
    ]
  }
    ↓
[Executor Loop]
  ↓
  Step 1: Generate query → Execute → Store full result
  ↓
  Step 2: Generate query (using Step 1 result) → Execute → Store result
  ↓
  All steps done
    ↓
[Formatter]
    ↓
Final response to user
```

### 5.4 State Persistence

**LangGraph Checkpointing:**
- State saved after every node execution
- Enables resume after interrupts (human-in-the-loop)
- Supports multi-turn conversations
- Can inspect state at any point for debugging

**Checkpoint Storage:**
- POC: In-memory (MemorySaver)
- Production: PostgreSQL/Redis (persistent)

---

## 6. Detailed Component Specifications

### 6.1 Node 1: Query Classifier

#### 6.1.1 Purpose
Determine whether the user's query is a search/list operation or a different type of operation (move, delete, create, etc.).

#### 6.1.2 Responsibilities
- Analyze user intent from natural language
- Classify into predefined categories
- Route to appropriate handler

#### 6.1.3 Inputs (from State)
```python
{
  "user_query": str,              # "List documents in Tax folder"
  "conversation_history": List    # Previous messages for context
}
```

#### 6.1.4 Outputs (to State)
```python
{
  "intent": str,                  # "search" | "move" | "delete" | "create" | "other"
  "classification_confidence": str, # "high" | "medium" | "low"
  "classification_reasoning": str   # Why this classification
}
```

#### 6.1.5 LLM Interaction
**Model:** GPT-4 or Claude Sonnet
**Method:** Structured output (JSON)

**Prompt Template:**
```
You are analyzing user queries for a document management system (similar to Google Drive).

Your task: Determine the user's intent.

INTENT CATEGORIES:

1. "search" - User wants to find/view/list existing documents or folders
   Keywords: find, show, list, get, search, display, where, which, what
   Examples:
   - "Show me all W2 documents"
   - "List folders in Business directory"
   - "Find documents created last week"
   - "Which folder contains invoice.pdf?"

2. "move" - User wants to relocate documents or folders
   Keywords: move, relocate, transfer
   Examples:
   - "Move document X to folder Y"
   - "Relocate all receipts to Archive"

3. "delete" - User wants to remove documents or folders
   Keywords: delete, remove, trash
   Examples:
   - "Delete old tax documents"
   - "Remove duplicate files"

4. "create" - User wants to create new folders or upload documents
   Keywords: create, add, upload, new
   Examples:
   - "Create a folder called Projects"
   - "Add a new document"

5. "other" - Queries about system capabilities, help, or unclear intent
   Examples:
   - "How does the system work?"
   - "What can I do here?"

CONTEXT:
Previous conversation: {conversation_history}

USER QUERY:
{user_query}

Respond with JSON:
{
  "intent": "search" | "move" | "delete" | "create" | "other",
  "confidence": "high" | "medium" | "low",
  "reasoning": "Brief explanation of why you chose this intent"
}
```

#### 6.1.6 Routing Logic
```python
def route_after_classify(state):
    if state["intent"] == "search":
        return "planner"
    elif state["intent"] == "move":
        return "move_handler"  # Future agent
    elif state["intent"] == "delete":
        return "delete_handler"  # Future agent
    elif state["intent"] == "create":
        return "create_handler"  # Future agent
    else:  # "other"
        return "end"  # Respond with help message
```

#### 6.1.7 Error Handling
- If LLM returns invalid JSON: Retry once, then default to "other"
- If confidence is "low": Add note to state for downstream nodes
- Timeout (10s): Default to "other" with error message

---

### 6.2 Node 2: Query Planner

#### 6.2.1 Purpose
Analyze the search query and determine whether it can be answered with a single Elasticsearch query or requires multiple sequential queries. Generate a high-level execution plan.

#### 6.2.2 Core Responsibility
Perform **gap analysis**: Identify when the user references information that doesn't exist directly in the target entity and requires resolution through another entity.

#### 6.2.3 Inputs (from State)
```python
{
  "user_query": str,           # "List documents in Tax Documents folder"
  "intent": str,               # "search"
  "conversation_history": List # For context
}
```

**Static Inputs (provided via prompt):**
- Complete Elasticsearch mapping
- Multi-step query examples (see Section 8)
- Sample ES documents

#### 6.2.4 Outputs (to State)
```python
{
  "query_plan": {
    "plan_type": str,          # "single_step" | "multi_step"
    "reasoning": str,          # Explanation of why this approach
    "total_steps": int,        # 1, 2, or 3
    "steps": [
      {
        "step": int,           # 1, 2, 3...
        "description": str,    # Natural language: "Find folder named 'Tax Documents'"
        "depends_on_step": Optional[int]  # Which previous step this needs
      }
    ]
  },
  "current_step": int          # Initialize to 1
}
```

#### 6.2.5 Planning Logic

**The planner must reason through:**

1. **What does the user want?**
   - Target entity type (DOCUMENT or FOLDER)
   - Desired filters/conditions

2. **Can we query this directly?**
   - Check if all filter fields exist on the target entity
   - Example: User wants "documents in folder X"
     - Target: DOCUMENT
     - Filter needed: parent folder = X
     - Available field: `systemAttributes.parentId` (expects UUID)
     - User provided: folder name "X"
     - **Gap identified!** ✗

3. **Can we resolve the gap?**
   - Is there another entity that has this information?
   - Example: FOLDER entity has `commonAttributes.name`
   - **Resolution possible!** ✓

4. **Create step-by-step plan**
   - Step 1: Get the missing information
   - Step 2: Use that information in the main query

#### 6.2.6 LLM Interaction

**Model:** GPT-4 or Claude Sonnet  
**Method:** Structured JSON output

**Prompt Template:**
```
You are a query planner for an Elasticsearch-based document management system.

Your task: Determine if a search query can be answered with ONE Elasticsearch query or needs MULTIPLE sequential queries.

# ELASTICSEARCH MAPPING

{full_es_mapping}

# KEY STRUCTURAL LIMITATIONS

1. Parent-Child Relationships Use IDs:
   - Documents store parent folder via: systemAttributes.parentId (UUID)
   - Documents DO NOT store parent folder name
   - To find "documents in folder X by name", you need folder X's ID first

2. Entity References:
   - Users often reference entities by NAME (human-readable)
   - Elasticsearch relationships use IDs (UUIDs)
   - Gap: name → ID resolution often needed

# DECISION FRAMEWORK

Step 1: Parse User Intent
- What entity does user want? (DOCUMENT or FOLDER)
- What filters/conditions do they specify?

Step 2: Gap Analysis
For each filter the user specifies:
  - Does the target entity have this field directly?
  - If YES: Can query in single step ✓
  - If NO: Can we get this info from another entity?
    - If YES: Multi-step query needed
    - If NO: Query cannot be fulfilled

Step 3: Create Plan
- Single-step: Direct query possible
- Multi-step: Sequential queries needed

# EXAMPLES OF MULTI-STEP SCENARIOS

{examples from Section 8}

# USER QUERY

{user_query}

# INSTRUCTIONS

Analyze the query using the decision framework above.

Output JSON:
{
  "plan_type": "single_step" | "multi_step",
  "reasoning": "Detailed explanation of your analysis and why this approach is needed",
  "total_steps": 1 | 2 | 3,
  "steps": [
    {
      "step": 1,
      "description": "High-level natural language description of what this query should accomplish. Be specific but don't specify exact ES fields or syntax.",
      "depends_on_step": null | 1 | 2  // Only for steps that need results from previous steps
    }
  ]
}

IMPORTANT:
- Keep step descriptions high-level and natural
- Don't specify exact Elasticsearch fields or query syntax
- Focus on WHAT needs to be found, not HOW
- Example: "Find the folder named 'Tax Documents'" NOT "Query FOLDER where commonAttributes.name.keyword = 'Tax Documents'"
```

#### 6.2.7 Examples of Planner Output

**Example 1: Single-Step Query**
```
User: "Find all W2 documents"

Planner Output:
{
  "plan_type": "single_step",
  "reasoning": "User wants documents filtered by type. The field 'commonAttributes.documentType' exists directly on DOCUMENT entities. No additional information needed. Single query sufficient.",
  "total_steps": 1,
  "steps": [
    {
      "step": 1,
      "description": "Find all documents where document type is 'W2'"
    }
  ]
}
```

**Example 2: Multi-Step Query (Folder Name Resolution)**
```
User: "List documents in Tax Documents folder"

Planner Output:
{
  "plan_type": "multi_step",
  "reasoning": "User wants documents in a specific folder, referenced by name 'Tax Documents'. Documents only store parent folder ID (systemAttributes.parentId), not parent folder name. Need to first find the folder by name to get its ID, then query documents using that ID.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find the folder with name 'Tax Documents' to get its folder ID"
    },
    {
      "step": 2,
      "description": "Find all documents where the parent folder ID matches the ID from step 1",
      "depends_on_step": 1
    }
  ]
}
```

**Example 3: Multi-Step Query (Sibling Documents)**
```
User: "Show other documents in the same folder as Report.pdf"

Planner Output:
{
  "plan_type": "multi_step",
  "reasoning": "User wants sibling documents of 'Report.pdf'. To find siblings, we need the parent folder ID of 'Report.pdf' first, then query for other documents in that folder.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find the document named 'Report.pdf' to get its parent folder ID"
    },
    {
      "step": 2,
      "description": "Find all documents in the same parent folder, excluding the original document",
      "depends_on_step": 1
    }
  ]
}
```

#### 6.2.8 Validation

After plan generation, perform basic sanity checks:
- `total_steps` matches length of `steps` array
- Step numbers are sequential (1, 2, 3...)
- If `depends_on_step` is specified, that step number exists
- At least one step is defined

If validation fails: Retry once, then escalate to error handler

#### 6.2.9 Routing Logic
```python
def route_after_planner(state):
    # Always proceed to executor
    # Executor handles both single and multi-step plans
    return "executor"
```

---

### 6.3 Node 3: Query Executor (Loop Node)

#### 6.3.1 Purpose
Execute the query plan step-by-step. For each step:
1. Generate Elasticsearch DSL query
2. Validate query syntax and fields
3. Execute against Elasticsearch service
4. Analyze results
5. Handle errors, ambiguities, and clarifications
6. Store complete results for next step
7. Loop back if more steps remain

#### 6.3.2 Why a Loop Node?
This node loops back to itself for multi-step execution:
- Step 1: Generate query → Execute → Store result → Loop back
- Step 2: Generate query (using Step 1 result) → Execute → Store result → Loop back
- Step N: Generate query → Execute → Done → Proceed to formatter

**Alternative considered:** Separate nodes for each operation (generate, validate, execute, analyze)
**Rejected because:** Over-engineering for POC; loop node is simpler and sufficient

#### 6.3.3 Inputs (from State)
```python
{
  "query_plan": Dict,           # From planner
  "current_step": int,          # Which step we're on (1, 2, 3...)
  "total_steps": int,           # From query_plan
  "step_results": Dict[int, Dict],  # Results from completed steps
  "user_query": str,            # Original query
  "retry_count": int,           # For error handling
  "pending_clarification": Optional[Dict]  # If interrupted
}
```

#### 6.3.4 Outputs (to State)
```python
{
  "current_step": int,          # Updated if looping
  "step_results": {
    1: {                        # Complete ES document from step 1
      "_source": {...},         # Full result
      "metadata": {...}         # Execution metadata
    },
    2: {...}                    # Step 2 results
  },
  "final_results": Optional[List],  # If all steps complete
  "error": Optional[str],       # If fatal error
  "pending_clarification": Optional[Dict],  # If needs user input
  "retry_count": int            # Updated on errors
}
```

#### 6.3.5 Internal Operations

The executor performs these operations **for each step**:

##### **Operation 1: Generate ES Query**

**Purpose:** Convert step description into Elasticsearch DSL

**LLM Prompt Template:**
```
{EXISTING_ES_QUERY_GENERATION_PROMPT}

# ADDITIONAL CONTEXT FOR MULTI-STEP QUERIES

This is step {current_step} of {total_steps}.

Step Purpose: {step_description}
Example: "Find the folder named 'Tax Documents'"

{IF this step depends on previous step:}
## Previous Step Result

Step {previous_step} returned the following document:

{full_json_document_from_previous_step}

Instructions for using previous results:
- Extract the values you need from the JSON above
- Common extractions:
  - Folder ID: systemAttributes.id
  - Parent ID: systemAttributes.parentId
  - Document type: commonAttributes.documentType
  - Category: commonAttributes.applicationAttributes.category
  - Owner ID: systemAttributes.owner.ownerAccountId
  - Creation date: systemAttributes.createDate

User's Original Query: {user_query}

Generate the Elasticsearch query for step {current_step}.
Remember: Return ONLY the query object, not the full search request.
```

**Example Input to LLM (Step 2):**
```
This is step 2 of 2.

Step Purpose: Find all documents where the parent folder ID matches the ID from step 1

Previous Step Result:
{
  "_source": {
    "systemAttributes": {
      "id": "4d3a2df1-1678-498c-99ee-b55960542d30",
      "parentId": "root"
    },
    "commonAttributes": {
      "name": "Tax Documents"
    },
    "entityType": "FOLDER",
    "organizationAttributes": {
      "folderPath": "root/Tax Documents"
    }
  }
}

Instructions: Use the folder ID from above (4d3a2df1-1678-498c-99ee-b55960542d30) to find documents where systemAttributes.parentId equals this value.

Generate the Elasticsearch query for step 2.
```

**Expected LLM Output:**
```json
{
  "bool": {
    "must": [
      {
        "term": {
          "entityType.keyword": "DOCUMENT"
        }
      },
      {
        "term": {
          "systemAttributes.parentId.keyword": "4d3a2df1-1678-498c-99ee-b55960542d30"
        }
      }
    ]
  }
}
```

##### **Operation 2: Validate Query**

**Purpose:** Ensure generated query is syntactically valid and uses correct fields

**Validation Checks:**

1. **JSON Syntax**
   - Valid JSON structure
   - Proper Elasticsearch DSL format

2. **Field Existence**
   - Extract all field references from query
   - Check each field exists in mapping
   - Common errors:
     - Using text field without `.keyword` for exact match
     - Non-existent fields
     - Wrong nested path

3. **Query Structure**
   - `bool` queries have valid clauses (must, should, must_not, filter)
   - `term` queries used on keyword fields
   - `match` queries used on text fields
   - `nested` queries for nested fields

4. **Logic Sanity**
   - Not too broad (e.g., missing entityType filter)
   - No contradictory conditions

**Validation Implementation:**
```python
def validate_query(query: Dict, mapping: Dict) -> List[str]:
    errors = []
    
    # Check field existence
    used_fields = extract_all_fields(query)
    for field in used_fields:
        if not field_exists_in_mapping(field, mapping):
            errors.append(f"Field '{field}' does not exist in mapping")
        
        # Check keyword suffix
        if should_use_keyword(field, mapping) and not field.endswith('.keyword'):
            errors.append(f"Field '{field}' should use '.keyword' for exact match")
    
    # Check query structure
    if not has_entity_type_filter(query):
        errors.append("Query should specify entityType (DOCUMENT or FOLDER)")
    
    return errors
```

**On Validation Failure:**
- If `retry_count < 3`: Regenerate with error feedback
- If `retry_count >= 3`: Set fatal error, proceed to formatter

##### **Operation 3: Execute Query**

**Purpose:** Call Elasticsearch service with generated query

**API Call:**
```python
def execute_query(es_query: Dict) -> Dict:
    response = requests.post(
        url=f"{ES_SERVICE_URL}/search",
        json={
            "query": es_query,
            "size": 100  # Or from config
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    if response.status_code != 200:
        raise ExecutionError(f"ES service returned {response.status_code}")
    
    return response.json()
```

**Response Structure:**
```json
{
  "hits": {
    "total": {"value": 1},
    "hits": [
      {
        "_source": {...}  // Full document
      }
    ]
  }
}
```

##### **Operation 4: Analyze Result**

**Purpose:** Determine next action based on execution result

**Result Categories:**

1. **Success - Single Result** (Expected for step dependencies)
   ```
   result_count == 1
   → Extract full document
   → Store in step_results
   → Proceed to next step or finish
   ```

2. **Success - Multiple Results** (Expected for final step)
   ```
   result_count > 1
   
   IF this is the final step:
     → Store all results
     → Proceed to formatter
   
   IF this is NOT the final step (e.g., step 1 of folder lookup):
     → Ambiguity detected
     → Ask user which one to use
     → INTERRUPT
   ```

3. **Empty Result**
   ```
   result_count == 0
   
   IF this is step 1 of multi-step:
     → Cannot proceed (critical failure)
     → Set error: "Folder/Entity not found"
     → Proceed to formatter
   
   IF this is the final step:
     → Valid empty result
     → Proceed to formatter (no results message)
   ```

4. **Error**
   ```
   API error, timeout, etc.
   → Route to error handler
   ```

**Implementation:**
```python
def analyze_result(result: Dict, step: Dict, current_step: int, total_steps: int):
    count = result["hits"]["total"]["value"]
    
    if count == 0:
        if current_step < total_steps:
            return "critical_error", "Cannot proceed: Entity not found"
        else:
            return "empty_result", "No matching documents/folders found"
    
    elif count == 1:
        return "success", result["hits"]["hits"][0]["_source"]
    
    elif count > 1:
        if current_step < total_steps:
            # Need single result to proceed
            return "needs_clarification", result["hits"]["hits"]
        else:
            # Multiple results OK for final step
            return "success", [hit["_source"] for hit in result["hits"]["hits"]]
```

##### **Operation 5: Handle Clarification (Human-in-the-Loop)**

**Trigger:** Step N returned multiple results when expecting single result

**Example Scenario:**
```
Step 1: Find folder named "Tax"
Result: Found 3 folders named "Tax"
  1. /root/Personal/Tax
  2. /root/Business/Tax
  3. /root/Archive/Tax

Action: Ask user which one
```

**Clarification Message:**
```python
clarification = {
    "type": "multiple_choice",
    "question": f"I found {count} folders named '{folder_name}'. Which one would you like?",
    "options": [
        {
            "number": 1,
            "display": format_result_for_display(result_1),
            "value": result_1  # Full ES document
        },
        {
            "number": 2,
            "display": format_result_for_display(result_2),
            "value": result_2
        },
        ...
    ]
}

state["pending_clarification"] = clarification
return state  # This triggers INTERRUPT
```

**LangGraph Interrupt:**
- Graph execution pauses
- State is checkpointed
- Clarification question returned to user
- System waits for user response

**Resume After User Response:**
```python
# User selects option 2
user_response = "2"

# Graph resumes
selected_result = state["pending_clarification"]["options"][1]["value"]

# Store selected result
state["step_results"][current_step] = selected_result
state["pending_clarification"] = None

# Continue to next step
state["current_step"] += 1
```

##### **Operation 6: Store Results**

**Purpose:** Save complete step result for use in subsequent steps

**Storage Format:**
```python
state["step_results"][current_step] = {
    "_source": full_es_document,  # Complete document from ES
    "metadata": {
        "query": es_query,          # Query that was executed
        "execution_time_ms": time,  # Performance tracking
        "result_count": count        # Original result count
    }
}
```

**Why Store Full Document:**
- Next step's LLM can extract any field it needs
- No hardcoded extraction logic
- Flexible for any query pattern
- Easier debugging (can see exactly what was found)

##### **Operation 7: Loop Decision**

**Determine Next Action:**

```python
# If there's a pending clarification, loop back (after user responds)
if state.get("pending_clarification"):
    return "executor"  # Will resume after interrupt

# If there's a fatal error, stop
if state.get("error"):
    return "formatter"

# If more steps remain, loop back
if state["current_step"] < state["total_steps"]:
    state["current_step"] += 1
    return "executor"

# All steps complete
else:
    # Move final results to top level for formatter
    state["final_results"] = state["step_results"][state["total_steps"]]
    return "formatter"
```

#### 6.3.6 Error Handling Within Executor

**Error Categories:**

1. **Validation Errors** (before execution)
   - Invalid ES syntax
   - Non-existent fields
   - **Recovery:** Regenerate query with feedback (max 3 attempts)

2. **Execution Errors** (API failures)
   - Network timeout
   - 500 server error
   - **Recovery:** Retry with exponential backoff (max 2 attempts)

3. **Critical Errors** (cannot proceed)
   - Step 1 returns 0 results in multi-step
   - Max retries exceeded
   - **Recovery:** None, set error and proceed to formatter

**Retry Logic:**
```python
MAX_RETRIES = 3

if error_type == "validation":
    if state["retry_count"] < MAX_RETRIES:
        state["retry_count"] += 1
        # Regenerate with feedback
        return state  # Loop back to query generation
    else:
        state["error"] = "Could not generate valid query after 3 attempts"
        return state  # Proceed to formatter

elif error_type == "execution":
    if state["retry_count"] < 2:
        state["retry_count"] += 1
        time.sleep(2 ** state["retry_count"])  # Exponential backoff
        # Retry execution
        return state  # Loop back to execution
    else:
        state["error"] = "Service unavailable after retries"
        return state
```

#### 6.3.7 Routing Logic

```python
def route_after_executor(state):
    # If interrupted for clarification, stay in executor
    if state.get("pending_clarification"):
        return "executor"
    
    # If error, go to formatter
    if state.get("error"):
        return "formatter"
    
    # If more steps, loop back
    if state["current_step"] < state["total_steps"]:
        return "executor"
    
    # All done
    return "formatter"
```

---

### 6.4 Node 4: Response Formatter

#### 6.4.1 Purpose
Format the final results or error messages into a user-friendly response.

#### 6.4.2 Inputs (from State)
```python
{
  "final_results": Optional[List[Dict] | Dict],  # From executor
  "error": Optional[str],                         # If execution failed
  "query_plan": Dict,                             # Original plan
  "user_query": str,                              # Original query
  "step_results": Dict[int, Dict]                 # All step results
}
```

#### 6.4.3 Outputs (to State)
```python
{
  "response_message": str,   # Final message to user
  "metadata": {
    "total_steps_executed": int,
    "execution_time_ms": int,
    "result_count": int
  }
}
```

#### 6.4.4 Formatting Logic

**Success Case - Single Step:**
```python
if state["query_plan"]["plan_type"] == "single_step":
    results = state["final_results"]
    count = len(results) if isinstance(results, list) else 1
    
    message = f"Found {count} result(s):\n\n"
    message += format_results_list(results)
```

**Success Case - Multi-Step:**
```python
if state["query_plan"]["plan_type"] == "multi_step":
    results = state["final_results"]
    count = len(results) if isinstance(results, list) else 1
    
    message = f"Found {count} result(s):\n\n"
    message += format_results_list(results)
    
    # Add transparency note
    step_1_entity = state["step_results"][1]["_source"]["commonAttributes"]["name"]
    message += f"\n\n(Note: Resolved '{step_1_entity}' to complete your search)"
```

**Empty Results:**
```python
message = "No documents or folders found matching your criteria.\n\n"
message += "Suggestions:\n"
message += "- Try broader search terms\n"
message += "- Check spelling of folder/document names\n"
message += "- List all available folders to find the right one"
```

**Error Case:**
```python
error_messages = {
    "folder_not_found": "I couldn't find a folder with that name. Would you like me to list all your folders?",
    "service_unavailable": "I'm having trouble reaching the search service. Please try again in a moment.",
    "invalid_query": "I had trouble understanding your search request. Could you rephrase it?"
}

message = error_messages.get(state["error"], "An error occurred: " + state["error"])
```

#### 6.4.5 Result Formatting

**For Documents:**
```
📄 Document Name
   Type: W2
   Folder: /root/Tax Documents/2024
   Created: Jan 15, 2024
   Size: 1.2 MB
```

**For Folders:**
```
📁 Folder Name
   Path: /root/Business/Receipts
   Contains: 15 documents
   Created: Dec 1, 2023
```

#### 6.4.6 Optional LLM Enhancement

For better formatting, can use LLM:
```
Prompt: Format these search results in a user-friendly way:
{results}

Make it scannable, highlight key information, use emojis for visual clarity.
```

But for POC, simple string formatting is sufficient.

---

## 7. State Management

### 7.1 Complete State Schema

```python
from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    # ============================================
    # INPUT - From User
    # ============================================
    user_query: str                    # "List documents in Tax folder"
    conversation_id: str               # Unique conversation identifier
    conversation_history: List[Dict]   # Previous messages for context
    
    # ============================================
    # CLASSIFICATION - Node 1
    # ============================================
    intent: str                        # "search" | "move" | "delete" | "create" | "other"
    classification_confidence: str     # "high" | "medium" | "low"
    classification_reasoning: str      # LLM's explanation
    
    # ============================================
    # PLANNING - Node 2
    # ============================================
    query_plan: Optional[Dict]         # Complete plan from planner
    # Structure:
    # {
    #   "plan_type": "single_step" | "multi_step",
    #   "reasoning": str,
    #   "total_steps": int,
    #   "steps": [
    #     {
    #       "step": int,
    #       "description": str,
    #       "depends_on_step": Optional[int]
    #     }
    #   ]
    # }
    
    total_steps: int                   # From query_plan
    current_step: int                  # Which step executor is on (1-indexed)
    
    # ============================================
    # EXECUTION - Node 3
    # ============================================
    step_results: Dict[int, Dict]      # Results from each step
    # Structure:
    # {
    #   1: {
    #     "_source": {...},            # Full ES document
    #     "metadata": {
    #       "query": {...},
    #       "execution_time_ms": int,
    #       "result_count": int
    #     }
    #   },
    #   2: {...}
    # }
    
    final_results: Optional[Any]       # Final results (list or single doc)
    
    # ============================================
    # ERROR HANDLING
    # ============================================
    error: Optional[str]               # Fatal error message
    retry_count: int                   # Current retry attempt
    max_retries: int                   # Maximum allowed retries (default: 3)
    
    # ============================================
    # HUMAN-IN-THE-LOOP
    # ============================================
    pending_clarification: Optional[Dict]  # Active clarification request
    # Structure:
    # {
    #   "type": "multiple_choice" | "free_text",
    #   "question": str,
    #   "options": [
    #     {
    #       "number": int,
    #       "display": str,
    #       "value": Any
    #     }
    #   ]
    # }
    
    user_clarification_response: Optional[str]  # User's response to clarification
    
    # ============================================
    # OUTPUT - Node 4
    # ============================================
    response_message: str              # Final formatted response
    metadata: Dict[str, Any]           # Execution metadata
    # Structure:
    # {
    #   "total_steps_executed": int,
    #   "execution_time_ms": int,
    #   "result_count": int,
    #   "plan_type": str
    # }
```

### 7.2 State Initialization

```python
def create_initial_state(user_query: str, conversation_id: str) -> AgentState:
    return {
        # Input
        "user_query": user_query,
        "conversation_id": conversation_id,
        "conversation_history": [],
        
        # Classification (populated by Node 1)
        "intent": "",
        "classification_confidence": "",
        "classification_reasoning": "",
        
        # Planning (populated by Node 2)
        "query_plan": None,
        "total_steps": 0,
        "current_step": 1,
        
        # Execution (populated by Node 3)
        "step_results": {},
        "final_results": None,
        
        # Error handling
        "error": None,
        "retry_count": 0,
        "max_retries": 3,
        
        # Human-in-the-loop
        "pending_clarification": None,
        "user_clarification_response": None,
        
        # Output (populated by Node 4)
        "response_message": "",
        "metadata": {}
    }
```

### 7.3 State Update Pattern

Each node follows this pattern:

```python
def node_function(state: AgentState) -> AgentState:
    # 1. Read from state
    user_query = state["user_query"]
    
    # 2. Perform operations
    result = do_something(user_query)
    
    # 3. Update state and return
    return {
        **state,                    # Preserve existing state
        "new_field": result,        # Add new data
        "updated_field": state["updated_field"] + 1  # Update existing
    }
```

### 7.4 Checkpointing

**LangGraph automatically checkpoints state:**
- After every node execution
- Before interrupts (human-in-the-loop)
- After receiving user input

**Checkpoint Configuration:**

```python
from langgraph.checkpoint.memory import MemorySaver

# For POC (in-memory)
checkpointer = MemorySaver()

# For production (persistent)
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver(connection_string="postgresql://...")
```

**Accessing Checkpoints:**

```python
# Get current state for a conversation
state = checkpointer.get_state(conversation_id)

# Resume from checkpoint
app.invoke(
    {"user_clarification_response": "Option 2"},
    config={"configurable": {"thread_id": conversation_id}}
)
```

---

## 8. Multi-Step Query Patterns & Examples

This section provides comprehensive examples of scenarios requiring multi-step queries. These examples should be included in the **Planner prompt** to teach the LLM what patterns to recognize.

### 8.1 Category 1: Name-to-ID Resolution

The most common pattern. User references entity by name, but queries require ID.

#### Example 1.1: Folder Name to Documents
```
User Query: "List documents in folder 'Tax Documents'"

Analysis:
- Target: DOCUMENT entities
- Filter: Parent folder = "Tax Documents"
- Gap: Documents store systemAttributes.parentId (UUID), not folder name
- Resolution: Find folder by name first to get ID

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "User references folder by name 'Tax Documents' but documents only store parent folder ID. Need to resolve folder name to ID first.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find the folder with name 'Tax Documents' to get its folder ID"
    },
    {
      "step": 2,
      "description": "Find all documents where the parent folder ID matches the ID from step 1",
      "depends_on_step": 1
    }
  ]
}
```

#### Example 1.2: Folder Name to Subfolders
```
User Query: "Show me subfolders under 'Business'"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "User wants subfolders of a folder referenced by name. Folders store parentId as UUID. Need folder ID first.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find the folder named 'Business' to get its ID"
    },
    {
      "step": 2,
      "description": "Find all folders where parent ID matches the Business folder ID",
      "depends_on_step": 1
    }
  ]
}
```

#### Example 1.3: Document Name to Folder
```
User Query: "Which folder contains 'Invoice_2024.pdf'?"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "User wants to find the folder containing a specific document. Need to first find the document to get its parentId, then find the folder with that ID.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find the document named 'Invoice_2024.pdf' to get its parent folder ID"
    },
    {
      "step": 2,
      "description": "Find the folder with the ID that matches the parent folder ID from step 1",
      "depends_on_step": 1
    }
  ]
}
```

### 8.2 Category 2: Sibling/Related Entity Queries

Finding entities related to another entity.

#### Example 2.1: Sibling Documents
```
User Query: "Show other documents in the same folder as 'Report.pdf'"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "To find sibling documents, need to first find 'Report.pdf' to get its parent folder ID, then query for other documents in that folder.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find the document named 'Report.pdf' to get its parent folder ID"
    },
    {
      "step": 2,
      "description": "Find all documents with the same parent folder ID, excluding the original document",
      "depends_on_step": 1
    }
  ]
}
```

#### Example 2.2: Parent Folder of Subfolder
```
User Query: "Show the parent folder of 'Subfolder1'"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "Need to find Subfolder1 first to get its parentFolderId, then find the folder with that ID.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find the folder named 'Subfolder1' to get its parent folder ID"
    },
    {
      "step": 2,
      "description": "Find the folder with ID matching the parent folder ID from step 1",
      "depends_on_step": 1
    }
  ]
}
```

### 8.3 Category 3: Attribute-Based Matching

Finding entities with the same attribute value as another entity.

#### Example 3.1: Documents with Same Category
```
User Query: "Show all documents with the same category as document 'Invoice_Jan.pdf'"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "Need to first find 'Invoice_Jan.pdf' to extract its category, then search for documents with that category.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find the document named 'Invoice_Jan.pdf' to get its category value"
    },
    {
      "step": 2,
      "description": "Find all documents where category matches the category from step 1",
      "depends_on_step": 1
    }
  ]
}
```

#### Example 3.2: Folders by Same Owner
```
User Query: "Show all folders owned by the same person who owns folder 'Projects'"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "Need to find 'Projects' folder first to get owner ID, then find all folders with that owner.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find the folder named 'Projects' to get the owner account ID"
    },
    {
      "step": 2,
      "description": "Find all folders owned by the same account ID from step 1",
      "depends_on_step": 1
    }
  ]
}
```

#### Example 3.3: Documents by Same Creator
```
User Query: "Show all documents created by the same person who created 'Budget_2024.xlsx'"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "Need to find the document first to extract creator user ID, then find all documents by that creator.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find document 'Budget_2024.xlsx' to get the creator user ID"
    },
    {
      "step": 2,
      "description": "Find all documents created by the same creator user ID from step 1",
      "depends_on_step": 1
    }
  ]
}
```

### 8.4 Category 4: Copy/Version Tracking

Working with copied documents.

#### Example 4.1: Find All Copies
```
User Query: "Show all copies of document 'Template_Letter.docx'"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "Need to find the original document to get its ID, then find all documents where copiedFrom equals that ID.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find document named 'Template_Letter.docx' to get its document ID"
    },
    {
      "step": 2,
      "description": "Find all documents where the copiedFrom field equals the ID from step 1",
      "depends_on_step": 1
    }
  ]
}
```

#### Example 4.2: Find Original Document
```
User Query: "Show the original document that 'Copy_of_Report.pdf' was copied from"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "Need to find the copy first to get its copiedFrom value, then find the document with that ID.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find document 'Copy_of_Report.pdf' to get the copiedFrom field value"
    },
    {
      "step": 2,
      "description": "Find the document with ID matching the copiedFrom value from step 1",
      "depends_on_step": 1
    }
  ]
}
```

### 8.5 Category 5: Temporal/Date-Based Queries

Queries involving date comparisons.

#### Example 5.1: Documents Created After Another
```
User Query: "Show documents uploaded after 'Report.pdf' was uploaded"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "Need to find Report.pdf first to get its creation date, then find documents created after that date.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find document 'Report.pdf' to get its creation date"
    },
    {
      "step": 2,
      "description": "Find all documents where creation date is after the date from step 1",
      "depends_on_step": 1
    }
  ]
}
```

### 8.6 Category 6: Combined Filters with Name Resolution

Multiple conditions where one requires name resolution.

#### Example 6.1: W2 Documents in Named Folder
```
User Query: "Show W2 documents in 'Tax Documents' folder"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "User wants documents filtered by both type (W2) and folder name. Folder name requires ID resolution.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find folder named 'Tax Documents' to get its ID"
    },
    {
      "step": 2,
      "description": "Find documents where document type is W2 and parent folder ID matches the ID from step 1",
      "depends_on_step": 1
    }
  ]
}
```

#### Example 6.2: Documents from App in Folder
```
User Query: "Show QuickBooks documents in 'Expenses' folder"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "Need to combine folder name filter with offering ID filter. Folder name requires resolution.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find folder named 'Expenses' to get its ID"
    },
    {
      "step": 2,
      "description": "Find documents where offering ID contains 'quickbooks' and parent folder ID matches step 1",
      "depends_on_step": 1
    }
  ]
}
```

### 8.7 Category 7: Hierarchical Path Queries

Working with folder hierarchies.

#### Example 7.1: All Documents in Folder Tree
```
User Query: "Show all documents under 'Projects' folder including subfolders"

Plan:
{
  "plan_type": "multi_step",
  "reasoning": "Need to find Projects folder first, then use its ID to find all documents in the folder tree using folderPathIds.",
  "total_steps": 2,
  "steps": [
    {
      "step": 1,
      "description": "Find folder named 'Projects' to get its folder ID"
    },
    {
      "step": 2,
      "description": "Find all documents where folderPathIds array contains the folder ID from step 1",
      "depends_on_step": 1
    }
  ]
}
```

### 8.8 Counter-Examples: Single-Step Queries

Important to also show when multi-step is NOT needed.

#### Counter-Example 1: Direct Document Type Search
```
User Query: "Find all W2 documents"

Plan:
{
  "plan_type": "single_step",
  "reasoning": "Query only requires filtering documents by type. The field 'commonAttributes.documentType' exists directly on DOCUMENT entities. No additional information needed.",
  "total_steps": 1,
  "steps": [
    {
      "step": 1,
      "description": "Find all documents where document type is W2"
    }
  ]
}
```

#### Counter-Example 2: Folder ID Provided
```
User Query: "List documents in folder ID 4d3a2df1-1678-498c-99ee-b55960542d30"

Plan:
{
  "plan_type": "single_step",
  "reasoning": "User provided folder ID directly. Can query documents by parentId in single step.",
  "total_steps": 1,
  "steps": [
    {
      "step": 1,
      "description": "Find all documents where parent folder ID equals 4d3a2df1-1678-498c-99ee-b55960542d30"
    }
  ]
}
```

#### Counter-Example 3: Root Level Query
```
User Query: "Show folders at root level"

Plan:
{
  "plan_type": "single_step",
  "reasoning": "Query for folders where parentId is 'root'. Direct query possible.",
  "total_steps": 1,
  "steps": [
    {
      "step": 1,
      "description": "Find all folders where parent ID is 'root'"
    }
  ]
}
```

### 8.9 Using These Examples

**In the Planner Prompt:**

```
# MULTI-STEP QUERY EXAMPLES

Below are examples of queries that require multiple steps and why:

## Name-to-ID Resolution

{Include examples 1.1, 1.2, 1.3}

## Sibling/Related Entities

{Include examples 2.1, 2.2}

## Attribute Matching

{Include examples 3.1, 3.2, 3.3}

## Copy Tracking

{Include examples 4.1, 4.2}

## Date-Based Queries

{Include example 5.1}

## Combined Filters

{Include examples 6.1, 6.2}

## SINGLE-STEP COUNTER-EXAMPLES

Not all queries need multiple steps. These can be done in one:

{Include counter-examples 1, 2, 3}
```

---

## 9. Prompt Engineering Guidelines

### 9.1 Planner Prompt Structure

**Complete Template:**

```markdown
# ROLE

You are a query planner for an Elasticsearch-based document management system (similar to Google Drive).

Your task: Determine if a search query needs ONE Elasticsearch query or MULTIPLE sequential queries.

# SYSTEM ARCHITECTURE

The system stores two types of entities:
- DOCUMENT: Files uploaded by users (PDFs, images, spreadsheets, etc.)
- FOLDER: Containers that organize documents and other folders

Key structural limitation:
- Parent-child relationships use UUIDs
- Users reference entities by NAME (human-readable)
- Queries require IDs (UUIDs)
- Gap: name → ID resolution often needed

# ELASTICSEARCH MAPPING

{full_mapping_from_document}

# KEY FIELDS FOR MULTI-STEP DETECTION

Documents:
- systemAttributes.id: Unique document ID (UUID)
- systemAttributes.parentId: Parent folder ID (UUID) - NOT parent folder name
- commonAttributes.name: Document name
- entityType: "DOCUMENT"

Folders:
- systemAttributes.id: Unique folder ID (UUID)
- systemAttributes.parentId: Parent folder ID (UUID)
- organizationAttributes.parentFolderId: Same as systemAttributes.parentId
- commonAttributes.name: Folder name
- entityType: "FOLDER"

# DECISION FRAMEWORK

Step 1: Parse User Intent
- What entity type does user want? (DOCUMENT or FOLDER)
- What filters/conditions did they specify?

Step 2: Gap Analysis
For each filter specified:
  Q: Does the target entity have this field directly?
  
  IF YES:
    → Single-step query possible
    
  IF NO:
    Q: Can we get this information from another entity?
    
    IF YES:
      → Multi-step query needed
      → Step 1: Get missing information
      → Step 2: Use that information in main query
    
    IF NO:
      → Query cannot be fulfilled

Step 3: Create Plan
Output structured plan with:
- plan_type: "single_step" or "multi_step"
- reasoning: Explanation of your analysis
- steps: Array of high-level step descriptions

# COMMON MULTI-STEP PATTERNS

{Include all examples from Section 8}

# USER QUERY

{user_query}

# OUTPUT FORMAT

Respond with JSON only (no markdown, no explanation outside JSON):

{
  "plan_type": "single_step" | "multi_step",
  "reasoning": "Detailed explanation of your gap analysis and why this approach is needed. Be specific about what fields are missing and how you'll resolve them.",
  "total_steps": 1 | 2 | 3,
  "steps": [
    {
      "step": 1,
      "description": "High-level natural language description. Focus on WHAT to find, not HOW. Example: 'Find the folder named Tax Documents' NOT 'Query FOLDER where commonAttributes.name.keyword equals Tax Documents'",
      "depends_on_step": null  // or 1, 2 for dependent steps
    }
  ]
}

# CRITICAL INSTRUCTIONS

1. Keep step descriptions NATURAL and HIGH-LEVEL
   - Good: "Find the folder named 'Tax Documents'"
   - Bad: "Query entityType=FOLDER where commonAttributes.name.keyword='Tax Documents'"

2. Don't specify Elasticsearch syntax in descriptions
   - The query generator will handle ES DSL
   - Focus on the intent, not the implementation

3. Only create multi-step plans when truly necessary
   - If the field exists on the target entity, use single-step
   - Example: "Find W2 documents" is single-step (documentType field exists)

4. Maximum 3 steps
   - Most queries are 1-2 steps
   - 3+ steps usually indicates over-complication

5. Be explicit about dependencies
   - If step 2 needs results from step 1, set "depends_on_step": 1
```

### 9.2 Executor Query Generation Prompt

**Template for Step N:**

```markdown
{EXISTING_ES_QUERY_GENERATION_PROMPT}

# ADDITIONAL CONTEXT - MULTI-STEP EXECUTION

You are generating a query for step {current_step} of {total_steps}.

## Step Purpose
{step_description}

## User's Original Query
{user_query}

{IF step depends on previous step:}

## Previous Step Result

Step {previous_step} returned this document:

```json
{full_previous_step_result}
```

### How to Use Previous Results

Common field extractions:
- Folder ID: systemAttributes.id
- Parent folder ID: systemAttributes.parentId or organizationAttributes.parentFolderId
- Document type: commonAttributes.documentType
- Category: commonAttributes.applicationAttributes.category
- Owner ID: systemAttributes.owner.ownerAccountId
- Creator ID: systemAttributes.creatorMetadata.creatorUserId
- Creation date: systemAttributes.createDate
- Tags: commonAttributes.tags
- Relationship ID: commonAttributes.applicationAttributes.relationshipId

Instructions:
1. Look at the previous step result JSON
2. Extract the value you need based on the step description
3. Use that value in your query
4. If the value is a UUID, use it with the .keyword suffix

Example:
- Step description: "Find documents in that folder"
- Previous result has: "systemAttributes.id": "abc-123-xyz"
- Your query should filter: systemAttributes.parentId.keyword = "abc-123-xyz"

{END IF}

# OUTPUT

Generate the Elasticsearch query object for this step.

Remember:
- Return ONLY the query object (not the full search request)
- Use .keyword suffix for exact matches on text fields
- Always include entityType filter (DOCUMENT or FOLDER)
- Follow all rules from the main query generation prompt
```

### 9.3 Prompt Best Practices

#### 9.3.1 Use Examples Generously
- LLMs learn best from examples
- Show both positive (multi-step) and negative (single-step) cases
- Include reasoning in examples

#### 9.3.2 Structure Over Prose
```
Good:
# DECISION FRAMEWORK
Step 1: ...
Step 2: ...

Bad:
When you're analyzing the query, first you should think about what the user wants, and then...
```

#### 9.3.3 Explicit Output Format
```
Good:
Respond with JSON:
{
  "plan_type": "single_step" | "multi_step",
  ...
}

Bad:
Please provide a plan for the query.
```

#### 9.3.4 Critical Instructions at End
```
# CRITICAL INSTRUCTIONS

1. ...
2. ...
3. ...
```

Place most important rules at the end - recent research shows LLMs pay more attention to end of prompts.

---

## 10. Error Handling & Recovery

### 10.1 Error Categories

#### 10.1.1 Classification Errors
**Error:** LLM returns invalid JSON or wrong intent

**Recovery:**
1. Retry with stricter prompt (once)
2. Default to "other" intent
3. Return help message to user

#### 10.1.2 Planning Errors
**Error:** LLM generates invalid plan structure

**Recovery:**
1. Validate plan structure
2. If invalid, retry with validation errors in prompt (once)
3. If still invalid, fallback to single-step assumption

#### 10.1.3 Query Generation Errors
**Error:** Generated ES query is invalid

**Recovery:**
1. Validate query
2. Provide feedback to LLM: "Field X doesn't exist, did you mean Y?"
3. Retry generation (max 3 times)
4. If max retries exceeded, return error to user

**Example Validation Feedback:**
```
Previous attempt generated invalid query. Errors:

1. Field 'commonAttributes.folderName' does not exist
   → Did you mean 'commonAttributes.name'?

2. Missing .keyword suffix on exact match
   → Field 'entityType' should be 'entityType.keyword' for term query

Please regenerate the query fixing these errors.
```

#### 10.1.4 Execution Errors
**Error:** API call fails (network, timeout, 500 error)

**Recovery:**
1. Retry with exponential backoff (max 2 times)
2. If persistent failure, return service unavailable error

#### 10.1.5 Empty Results
**Error:** Query returns 0 results

**Handling:**
- If step 1 of multi-step: Critical error, cannot proceed
- If final step: Valid outcome, inform user

#### 10.1.6 Multiple Results (Unexpected)
**Error:** Step 1 returns multiple results when expecting one

**Recovery:**
1. Present options to user
2. Wait for user selection (interrupt)
3. Resume with selected result

### 10.2 Retry Strategy

```python
RETRY_CONFIG = {
    "llm_generation": {
        "max_retries": 3,
        "backoff": None,  # No backoff for LLM calls
        "timeout": 30
    },
    "es_execution": {
        "max_retries": 2,
        "backoff": "exponential",  # 2s, 4s
        "timeout": 10
    },
    "validation": {
        "max_retries": 3,
        "provide_feedback": True
    }
}
```

### 10.3 Human-in-the-Loop Error Recovery

**When to Interrupt:**
1. Ambiguous query (multiple interpretations possible)
2. Multiple results when expecting single (step 1 of folder lookup)
3. Confidence low on classification

**When Not to Interrupt:**
1. Validation errors (auto-retry)
2. Network errors (auto-retry)
3. Empty results (inform user, don't ask)

### 10.4 Error Messages to User

**Good Error Messages:**
```
❌ "I couldn't find a folder named 'Tax Documents'. Would you like me to:
   1. List all your folders
   2. Search for folders with similar names
   3. Try a different search"

✅ Clear options, actionable next steps
```

**Bad Error Messages:**
```
❌ "Query execution failed with status code 404"
❌ "ElasticsearchException: field mapping not found"

❌ Too technical, not actionable
```

---

## 11. Success Criteria

### 11.1 Functional Requirements

**Must Have (POC):**
- ✅ Correctly classify search queries (>95% accuracy)
- ✅ Generate valid ES queries for single-step searches (>90% success)
- ✅ Successfully execute folder name → documents multi-step queries (>80%)
- ✅ Handle folder name ambiguity (multiple folders with same name)
- ✅ Return formatted results to user
- ✅ Handle empty results gracefully

**Should Have (POC):**
- ✅ Support 2-3 other multi-step patterns (sibling docs, attribute matching)
- ✅ Retry logic for validation errors
- ✅ Conversation context for follow-up queries
- ✅ Performance: <5s response time for single-step, <10s for multi-step

**Nice to Have (Future):**
- ⭕ Fuzzy name matching ("Tax Docs" → "Tax Documents")
- ⭕ Query optimization (combine filters efficiently)
- ⭕ Learning from failures (log and improve)

### 11.2 Quality Metrics

**Accuracy Metrics:**
- Query classification accuracy: >95%
- Single-step query success rate: >90%
- Multi-step query success rate: >80%
- False positive clarifications: <5%

**Performance Metrics:**
- Single-step response time: <5s (p95)
- Multi-step response time: <10s (p95)
- LLM call latency: <2s per call
- ES query execution: <500ms per query

**User Experience Metrics:**
- Successful query completion rate: >85%
- User clarification abandonment: <10%
- Retry rate: <15%

### 11.3 Testing Strategy

**Unit Tests:**
- Each node function in isolation
- State transformations
- Validation logic
- Error handling

**Integration Tests:**
- Full graph execution end-to-end
- Single-step queries (10+ examples)
- Multi-step queries (20+ examples covering all categories)
- Error scenarios
- Interrupt/resume flows

**User Acceptance Testing:**
- Real users test with actual queries
- Measure success rate
- Collect feedback on results quality
- Identify edge cases

---

## 12. Future Considerations

### 12.1 Beyond POC: Production Enhancements

**Performance Optimization:**
- Query caching (folder name → ID mappings)
- Parallel execution where possible
- Query result pagination
- Streaming responses

**Advanced Query Capabilities:**
- Aggregations and analytics
- Complex boolean logic (AND, OR, NOT combinations)
- Fuzzy matching and typo tolerance
- Semantic search (embedding-based)

**Enhanced Error Handling:**
- Circuit breaker for ES service
- Fallback to cached results
- Proactive error prediction

**User Experience:**
- Query suggestions and auto-complete
- Visual query builder
- Result preview and refinement
- Export results in multiple formats

### 12.2 Scalability Considerations

**For High Volume:**
- Distributed checkpointing (Redis cluster)
- Load balancing across multiple LLM endpoints
- Query queue management
- Rate limiting per user

### 12.3 Extensibility

**Adding New Agents:**
The current architecture supports adding other agents:
- Move agent (move documents/folders)
- Delete agent (delete with safety checks)
- Create agent (create folders, upload documents)
- Share agent (manage permissions)

**Integration Points:**
- All agents share the classifier node
- Routing logic in classifier directs to appropriate agent
- Shared state schema patterns
- Common error handling

### 12.4 Monitoring & Observability

**Metrics to Track:**
- Requests per minute (by intent type)
- Success rate per node
- Latency per node
- LLM token usage
- ES query performance
- Error rate by category
- User satisfaction (thumbs up/down)

**Logging:**
- Full state at each checkpoint
- LLM prompts and responses
- ES queries and results
- Error stack traces
- User interactions

**Alerting:**
- Success rate drops below threshold
- Latency exceeds SLA
- Error rate spike
- Service availability issues

### 12.5 Cost Optimization

**LLM Costs:**
- Use cheaper models for classification (GPT-3.5 vs GPT-4)
- Cache classification results for similar queries
- Optimize prompt length (remove unnecessary examples)
- Batch requests where possible

**ES Costs:**
- Query optimization (use filters vs queries where appropriate)
- Result size limiting
- Index optimization
- Caching frequent queries

---

## Appendix A: Complete LangGraph Construction

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Define state
class AgentState(TypedDict):
    # ... (full schema from Section 7.1)
    pass

# Create graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("classifier", query_classifier_node)
graph.add_node("planner", query_planner_node)
graph.add_node("executor", query_executor_loop_node)
graph.add_node("formatter", response_formatter_node)

# Define routing functions
def route_after_classify(state):
    if state["intent"] == "search":
        return "planner"
    else:
        return "formatter"  # Or route to other agents in future

def route_after_executor(state):
    if state.get("pending_clarification"):
        return "executor"  # Resume after interrupt
    elif state.get("error"):
        return "formatter"
    elif state["current_step"] < state["total_steps"]:
        return "executor"  # Loop back
    else:
        return "formatter"

# Add edges
from langgraph.graph import START

graph.add_edge(START, "classifier")
graph.add_conditional_edges(
    "classifier",
    route_after_classify,
    {
        "planner": "planner",
        "formatter": "formatter"
    }
)
graph.add_edge("planner", "executor")
graph.add_conditional_edges(
    "executor",
    route_after_executor,
    {
        "executor": "executor",
        "formatter": "formatter"
    }
)
graph.add_edge("formatter", END)

# Compile with checkpointing
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# Usage
result = app.invoke(
    {
        "user_query": "List documents in Tax Documents folder",
        "conversation_id": "conv-123"
    },
    config={"configurable": {"thread_id": "conv-123"}}
)
```

---

## Appendix B: Glossary

- **Agent**: AI system that can perceive, reason, and act
- **Checkpoint**: Saved state snapshot in LangGraph
- **Clarification**: Question posed to user to resolve ambiguity
- **ES**: Elasticsearch
- **ES DSL**: Elasticsearch Domain Specific Language (query syntax)
- **Gap Analysis**: Identifying missing information needed to fulfill query
- **Human-in-the-Loop**: Pattern where agent pauses for user input
- **Interrupt**: LangGraph mechanism to pause execution
- **LLM**: Large Language Model
- **Multi-Step Query**: Query requiring multiple sequential ES requests
- **Plan**: High-level strategy for executing a query
- **Single-Step Query**: Query that can be fulfilled with one ES request
- **State**: Data structure passed between nodes in LangGraph
- **UUID**: Universally Unique Identifier (folder/document IDs)

---

**End of PRD**

---

**Document Control:**
- Version: 1.0
- Last Updated: November 16, 2025
- Next Review: After POC completion
- Owner: AI Architecture Team
- Approvers: Engineering Lead, Product Manager