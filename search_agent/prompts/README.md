# Prompts

This directory contains prompt templates for LLM interactions.

## Prompt Implementation Status

### Phase 2: Query Planner
- [ ] `planner_prompt.py` - Prompt template for query planning

### Phase 3: Query Executor
- [ ] `executor_prompt.py` - Prompt template for ES query generation

### Phase 4: Classifier
- [ ] `classifier_prompt.py` - Prompt template for intent classification

## Prompt Template Pattern

All prompts should follow this structure:

```python
from typing import Dict, Any
from search_agent.config import settings

def build_<node>_prompt(
    user_query: str,
    **context: Any
) -> str:
    """
    Build prompt for <node> node.

    Args:
        user_query: User's natural language query
        **context: Additional context for the prompt

    Returns:
        Complete prompt string ready for LLM
    """
    # Load any required resources
    mapping = load_mapping()
    examples = load_examples()

    # Build prompt sections
    prompt = f"""
# ROLE

You are a [description]...

# CONTEXT

{context}

# TASK

{user_query}

# OUTPUT FORMAT

Return JSON:
{{
  "field": "value"
}}
"""

    return prompt
```

## Resource Loading

Prompts can access resources from the existing ES query tool:

```python
from search_agent.config import settings

# ES mapping
mapping_path = settings.es_mapping_path
with open(mapping_path) as f:
    mapping = json.load(f)

# Field descriptions
field_desc_path = settings.es_field_descriptions_path
with open(field_desc_path) as f:
    field_descriptions = json.load(f)

# Few-shot examples
examples_path = settings.es_few_shot_examples_path
with open(examples_path) as f:
    examples = json.load(f)
```

## Testing Prompts

Test prompts by:
1. Building the prompt with sample inputs
2. Calling LLM with the prompt
3. Validating the response structure

```python
from search_agent.services import get_llm_service

llm = get_llm_service()
prompt = build_planner_prompt("test query")
response = llm.call_with_json_response(prompt)

# Validate response structure
assert "plan_type" in response
assert "steps" in response
```
