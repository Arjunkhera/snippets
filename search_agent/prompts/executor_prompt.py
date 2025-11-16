"""
Query Executor Prompt Template.

This module provides the prompt template for the query executor node.
It builds on the existing Elasticsearch query generator and adds multi-step execution context.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from search_agent.config import settings


def load_es_prompt_template() -> str:
    """
    Load the existing Elasticsearch query generation prompt template.

    Returns:
        Prompt template string with placeholders

    Raises:
        FileNotFoundError: If prompt template file doesn't exist
    """
    template_path = settings.es_prompt_template_path

    if not template_path.exists():
        raise FileNotFoundError(
            f"ES prompt template file not found: {template_path}. "
            f"Ensure ai_tools/elasticsearch/resources/prompt_template.txt exists."
        )

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_es_resources() -> Dict[str, Any]:
    """
    Load all Elasticsearch resources (mapping, descriptions, examples, etc.).

    Returns:
        Dictionary containing all ES resources

    Raises:
        FileNotFoundError: If resource files don't exist
    """
    resources = {}

    # Load mapping
    with open(settings.es_mapping_path, 'r', encoding='utf-8') as f:
        resources['mapping'] = json.load(f)

    # Load field descriptions
    with open(settings.es_field_descriptions_path, 'r', encoding='utf-8') as f:
        resources['field_descriptions'] = json.load(f)

    # Load few-shot examples
    with open(settings.es_few_shot_examples_path, 'r', encoding='utf-8') as f:
        resources['few_shot_examples'] = json.load(f)

    # Load full document example
    with open(settings.es_full_document_path, 'r', encoding='utf-8') as f:
        resources['full_document'] = json.load(f)

    return resources


def build_executor_prompt(
    step_description: str,
    user_query: str,
    current_step: int,
    total_steps: int,
    previous_step_result: Optional[Dict[str, Any]] = None,
    depends_on_step: Optional[int] = None
) -> str:
    """
    Build the complete executor prompt for ES query generation.

    This integrates with the existing ES query generator and adds multi-step context.

    Args:
        step_description: Natural language description of what this step should do
        user_query: Original user query for context
        current_step: Current step number (1-indexed)
        total_steps: Total number of steps in the plan
        previous_step_result: Result from previous step (if this step depends on it)
        depends_on_step: Step number this step depends on

    Returns:
        Complete formatted prompt for the LLM

    Raises:
        FileNotFoundError: If ES resources are not found

    Example:
        >>> prompt = build_executor_prompt(
        ...     step_description="Find documents in that folder",
        ...     user_query="List documents in Tax Documents folder",
        ...     current_step=2,
        ...     total_steps=2,
        ...     previous_step_result={"_source": {"systemAttributes": {"id": "abc-123"}}},
        ...     depends_on_step=1
        ... )
    """
    # Load ES resources
    resources = load_es_resources()

    # Load base ES prompt template
    base_template = load_es_prompt_template()

    # Replace placeholders in base template
    prompt = base_template.replace(
        "{{MAPPING}}",
        json.dumps(resources['mapping'], indent=2)
    )

    # Format field descriptions
    field_desc_lines = []
    for field, description in resources['field_descriptions'].items():
        field_desc_lines.append(f"- **{field}**: {description}")
    prompt = prompt.replace(
        "{{FIELD_DESCRIPTIONS}}",
        "\n".join(field_desc_lines)
    )

    prompt = prompt.replace(
        "{{FULL_DOCUMENT}}",
        json.dumps(resources['full_document'], indent=2)
    )

    # Format few-shot examples
    examples_lines = []
    for example in resources['few_shot_examples']:
        examples_lines.append(f"**Query:** {example['query']}")
        examples_lines.append("**Elasticsearch DSL:**")
        examples_lines.append("```json")
        examples_lines.append(json.dumps(example['elasticsearch_query'], indent=2))
        examples_lines.append("```")
        examples_lines.append("")
    prompt = prompt.replace(
        "{{FEW_SHOT_EXAMPLES}}",
        "\n".join(examples_lines)
    )

    # Add multi-step context BEFORE the user query section
    multi_step_context = f"""
## Multi-Step Query Execution Context

This is **step {current_step} of {total_steps}** in a multi-step query execution plan.

**Step Purpose:** {step_description}

**Original User Query:** "{user_query}"
"""

    # Add previous step results if this step depends on another
    if depends_on_step is not None and previous_step_result is not None:
        # Extract the _source if it's wrapped in metadata
        if "_source" in previous_step_result:
            result_data = previous_step_result["_source"]
        else:
            result_data = previous_step_result

        multi_step_context += f"""
## Previous Step Result

Step {depends_on_step} returned the following document:

```json
{json.dumps(result_data, indent=2)}
```

### Instructions for Using Previous Results

Extract the values you need from the JSON above. Common field extractions:

- **Folder ID**: `systemAttributes.id`
- **Parent Folder ID**: `systemAttributes.parentId` or `organizationAttributes.parentFolderId`
- **Document ID**: `systemAttributes.id`
- **Document Type**: `commonAttributes.documentType`
- **Category**: `commonAttributes.applicationAttributes.category`
- **Owner ID**: `systemAttributes.owner.ownerAccountId`
- **Creator ID**: `systemAttributes.creatorMetadata.creatorUserId`
- **Creation Date**: `systemAttributes.createDate`
- **Tags**: `commonAttributes.tags`
- **Relationship ID**: `commonAttributes.applicationAttributes.relationshipId`

**Example:**
If the step description says "Find documents in that folder" and the previous result contains:
```json
{{
  "systemAttributes": {{
    "id": "abc-123-xyz"
  }}
}}
```
Then you should use `systemAttributes.parentId.keyword` with value `"abc-123-xyz"` to find documents.

### Important Notes

1. **Use the exact value from the previous result** - don't modify or transform it
2. **Use .keyword suffix** for exact UUID matches (e.g., `systemAttributes.parentId.keyword`)
3. **Extract from the correct field** based on what the step description asks for
4. **The previous result is a single document** that you're using to get reference values
"""

    # Insert multi-step context before "## User Query" section
    prompt = prompt.replace(
        "## User Query",
        multi_step_context + "\n## User Query (for this specific step)"
    )

    # Replace the user query placeholder with step description
    # For multi-step, we want the LLM to focus on the step description
    if total_steps > 1:
        query_text = step_description
    else:
        query_text = user_query

    prompt = prompt.replace("{{USER_QUERY}}", query_text)

    return prompt


if __name__ == "__main__":
    # Test the prompt generation
    test_prompt = build_executor_prompt(
        step_description="Find the folder named 'Tax Documents' to get its folder ID",
        user_query="List documents in Tax Documents folder",
        current_step=1,
        total_steps=2
    )
    print("Executor Prompt Generated Successfully")
    print(f"Prompt length: {len(test_prompt)} characters")
    print("\n" + "=" * 50)
    print("Sample prompt (first 500 chars):")
    print(test_prompt[:500])
