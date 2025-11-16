#!/usr/bin/env python3
"""
Generate split prompt files for Claude Prompt Bench from Elasticsearch Query Generator resources.

This script reads the resource files (mapping, field descriptions, full document example, 
few-shot examples, prompt_template.txt) and generates two separate markdown files optimized 
for use in Claude Prompt Bench:
- elasticsearch_system_prompt.md: Contains rules from prompt_template.txt, mapping, field 
  descriptions, full document example, and few-shot examples (cached)
- elasticsearch_user_prompt_template.md: Contains only the task description and user query placeholder

The script extracts rules/instructions from prompt_template.txt, so any changes to that file
will be reflected in the generated system prompt.

Usage:
    python generate_prompt_bench_files.py
    # or
    ./generate_prompt_bench_files.py
"""

import json
from pathlib import Path


def load_resources():
    """Load all resource files needed for prompt generation."""
    resources_dir = Path(__file__).parent / "resources"
    
    # Load mapping
    with open(resources_dir / "Mapping.json", 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    # Load field descriptions
    with open(resources_dir / "FieldDescriptions.json", 'r', encoding='utf-8') as f:
        field_descriptions = json.load(f)
    
    # Load few-shot examples
    with open(resources_dir / "FewShotExamples.json", 'r', encoding='utf-8') as f:
        few_shot_examples = json.load(f)
    
    # Load full document example
    with open(resources_dir / "FullDocument.json", 'r', encoding='utf-8') as f:
        full_document = json.load(f)
    
    # Load prompt template
    with open(resources_dir / "prompt_template.txt", 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    return mapping, field_descriptions, few_shot_examples, full_document, prompt_template


def generate_system_prompt(mapping, field_descriptions, few_shot_examples, full_document, prompt_template):
    """Generate the system prompt with rules, mapping, field descriptions, full document, and examples from template."""
    
    # Extract the rules/instructions section from the template
    # Everything before "## Elasticsearch Mapping" is the rules section
    template_parts = prompt_template.split("## Elasticsearch Mapping")
    rules_section = template_parts[0].strip()
    
    # Remove placeholders and user query sections from rules
    rules_section = rules_section.split("## User Query")[0].strip()
    
    # Convert mapping to formatted JSON string
    mapping_str = json.dumps(mapping, indent=2)
    
    # Format field descriptions
    descriptions_str = "\n".join([f"- **{key}**: {value}" for key, value in field_descriptions.items()])
    
    # Convert full document to formatted JSON string
    full_document_str = json.dumps(full_document, indent=2)
    
    # Format few-shot examples
    examples_str = ""
    for i, example in enumerate(few_shot_examples, 1):
        examples_str += f"\n### Example {i}\n"
        examples_str += f"**Natural Language**: {example['natural_language']}\n\n"
        examples_str += f"**Elasticsearch Query**:\n```json\n{json.dumps(example['elasticsearch_query'], indent=2)}\n```\n"
    
    # Build complete system prompt using the template structure
    system_prompt = f"""{rules_section}

## Elasticsearch Mapping

Below is the complete mapping for the entities-v4 index. Refer to this for all field names and types:

```json
{mapping_str}
```

## Field Descriptions

The following descriptions explain the semantic meaning of key fields in the mapping:

{descriptions_str}

## Sample Document

Here is a complete example of what a document looks like in the entities-v4 index. This shows you the actual structure and data that exists in the index:

```json
{full_document_str}
```

## Examples

Here are example natural language queries and their corresponding Elasticsearch queries:

{examples_str}"""
    
    return system_prompt


def generate_user_prompt_template():
    """Generate the user prompt template with just the task and user query placeholder."""
    
    # Build complete user prompt template
    user_prompt_template = """## Your Task

Convert the following natural language query into a valid Elasticsearch DSL query for the entities-v4 index.

## User Query

"{{USER_QUERY}}"

## Your Response

Return ONLY valid JSON. Either:
1. A valid Elasticsearch query object, OR
2. An error object with "error" and "message" fields

Do not include any explanatory text outside the JSON."""
    
    return user_prompt_template


def main():
    """Main function to generate prompt bench files."""
    print("=" * 60)
    print("ELASTICSEARCH PROMPT BENCH FILE GENERATOR")
    print("=" * 60)
    print()
    
    # Load resources
    print("📦 Loading resources...")
    try:
        mapping, field_descriptions, few_shot_examples, full_document, prompt_template = load_resources()
        print(f"   ✅ Loaded mapping: {len(json.dumps(mapping)):,} characters")
        print(f"   ✅ Loaded {len(field_descriptions)} field descriptions")
        print(f"   ✅ Loaded {len(few_shot_examples)} few-shot examples")
        print(f"   ✅ Loaded full document: {len(json.dumps(full_document)):,} characters")
        print(f"   ✅ Loaded prompt template: {len(prompt_template):,} characters")
    except Exception as e:
        print(f"   ❌ Error loading resources: {e}")
        return 1
    print()
    
    # Generate prompts
    print("🔨 Generating prompt files...")
    try:
        system_prompt = generate_system_prompt(mapping, field_descriptions, few_shot_examples, full_document, prompt_template)
        user_prompt_template = generate_user_prompt_template()
        print(f"   ✅ System prompt: {len(system_prompt):,} characters (includes {len(few_shot_examples)} examples)")
        print(f"   ✅ User prompt template: {len(user_prompt_template):,} characters")
    except Exception as e:
        print(f"   ❌ Error generating prompts: {e}")
        return 1
    print()
    
    # Create output directory (at repository root)
    repo_root = Path(__file__).parent.parent.parent
    output_dir = repo_root / "Prompts"
    output_dir.mkdir(exist_ok=True)
    
    # Write files
    print("💾 Writing files...")
    try:
        system_file = output_dir / "elasticsearch_system_prompt.md"
        with open(system_file, 'w', encoding='utf-8') as f:
            f.write(system_prompt)
        print(f"   ✅ Written: {system_file}")
        
        user_file = output_dir / "elasticsearch_user_prompt_template.md"
        with open(user_file, 'w', encoding='utf-8') as f:
            f.write(user_prompt_template)
        print(f"   ✅ Written: {user_file}")
    except Exception as e:
        print(f"   ❌ Error writing files: {e}")
        return 1
    print()
    
    print("=" * 60)
    print("✅ SUCCESS")
    print("=" * 60)
    print()
    print("Files generated for Claude Prompt Bench:")
    print(f"  • System prompt: {system_file}")
    print(f"  • User template:  {user_file}")
    print()
    print("Usage in Prompt Bench:")
    print("  1. Use elasticsearch_system_prompt.md as your system prompt")
    print("  2. Use elasticsearch_user_prompt_template.md as your user prompt")
    print("  3. Replace {{USER_QUERY}} with actual queries in your test cases")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())

