# Elasticsearch Query Generator

A Claude Sonnet 4.5-powered tool that generates syntactically valid Elasticsearch DSL queries from natural language descriptions for the `entities-v4` index.

## Features

- ✅ Loads mapping, field descriptions, and examples from external JSON files
- ✅ Supports custom resource paths for flexibility
- ✅ Validates generated queries using elasticsearch-dsl
- ✅ Handles ambiguous queries and provides helpful error messages
- ✅ Includes fallback to embedded resources if files can't be loaded

## Quick Start

### Basic Usage

```python
from ai_tools.elasticsearch.generate_elasticsearch_query import generate_elasticsearch_query

# Set your API key
import os
os.environ['ANTHROPIC_API_KEY'] = 'your-key-here'

# Generate a query
result = generate_elasticsearch_query("Find all W2 documents for 2024")

if 'elasticsearch_query' in result:
    print("Generated query:", result['elasticsearch_query'])
else:
    print("Error:", result['error'], result['message'])
```

### Command Line Usage

```bash
export ANTHROPIC_API_KEY='your-key-here'
python generate_elasticsearch_query.py "Find all W2 documents for 2024"
```

## Advanced Usage

### Custom Resource Paths

You can override the default resource files:

```python
from pathlib import Path

result = generate_elasticsearch_query(
    "Find all receipts",
    mapping_path=Path("custom/mapping.json"),
    field_descriptions_path=Path("custom/descriptions.json"),
    few_shot_examples_path=Path("custom/examples.json")
)
```

### Provide Resources Directly

For testing or runtime modifications:

```python
custom_mapping = '{"entities-v4": {...}}'
custom_descriptions = {"field1": "Description 1", ...}
custom_examples = [{"natural_language": "...", "elasticsearch_query": {...}}]

result = generate_elasticsearch_query(
    "Find documents",
    mapping=custom_mapping,
    field_descriptions=custom_descriptions,
    few_shot_examples=custom_examples
)
```

## Resource Files

The tool loads resources from `ai_tools/elasticsearch/resources/` (packaged with pip):

- **Mapping.json**: Complete Elasticsearch mapping for entities-v4 index
- **FieldDescriptions.json**: Human-readable descriptions of field meanings
- **FewShotExamples.json**: Example queries showing natural language → ES DSL
- **prompt_template.txt**: LLM prompt template with placeholders

### Resource File Format

**FieldDescriptions.json**:
```json
{
  "entityType": "Type of entity: DOCUMENT or FOLDER",
  "commonAttributes.documentType": "Type/classification of the document"
}
```

**FewShotExamples.json**:
```json
[
  {
    "natural_language": "Find all W2 documents",
    "notes": "Simple document type query",
    "elasticsearch_query": {
      "bool": {
        "must": [
          {"term": {"entityType.keyword": "DOCUMENT"}},
          {"term": {"commonAttributes.documentType.keyword": "W2"}}
        ]
      }
    }
  }
]
```

**prompt_template.txt**:
```
Your prompt text here...

## Elasticsearch Mapping
{{MAPPING}}

## Field Descriptions
{{FIELD_DESCRIPTIONS}}

## Examples
{{FEW_SHOT_EXAMPLES}}

## User Query
"{{USER_QUERY}}"
```

Available placeholders:
- `{{MAPPING}}` - Elasticsearch mapping JSON
- `{{FIELD_DESCRIPTIONS}}` - Formatted field descriptions
- `{{FEW_SHOT_EXAMPLES}}` - Formatted examples
- `{{USER_QUERY}}` - User's natural language query

## Prompt Engineering with Claude Prompt Bench

For prompt optimization, use the split prompts in `Prompts/`:

- **elasticsearch_system_prompt.txt**: System instructions with mapping and descriptions (~215K chars)
- **elasticsearch_user_prompt_template.txt**: User prompt with examples (~6K chars)

### Using in Prompt Bench

1. Copy `elasticsearch_system_prompt.txt` → System field
2. Copy `elasticsearch_user_prompt_template.txt` → User field
3. Replace `{{USER_QUERY}}` with test queries
4. Test different variations of rules, examples, descriptions

### Why Split?

- **System prompt**: Cached by Claude, includes static mapping/descriptions
- **User prompt**: Variable content (examples, query), easier to iterate
- **Result**: Lower cost, faster experimentation

## API Response Format

### Success Response

```python
{
  "elasticsearch_query": {
    "bool": {
      "must": [...]
    }
  }
}
```

### Error Response

```python
{
  "error": "ERROR_CODE",
  "message": "Detailed explanation"
}
```

**Error Codes**:
- `EMPTY_QUERY`: Query parameter is empty
- `AMBIGUOUS_QUERY`: LLM cannot confidently map the query
- `UNSUPPORTED_FIELD`: Query references non-existent fields
- `INVALID_API_KEY`: Missing or invalid ANTHROPIC_API_KEY
- `MALFORMED_RESPONSE`: Invalid JSON from LLM
- `VALIDATION_FAILED`: Generated query failed validation
- `LLM_API_FAILURE`: API call failed after retries
- `RESOURCE_LOAD_ERROR`: Failed to load external resources

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Required. Your Anthropic API key.

### Constants (in code)

```python
MODEL_NAME = "claude-sonnet-4-5-20250929"
TEMPERATURE = 0.0
TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # Exponential backoff
```

## Dependencies

```
anthropic >= 0.18.0
elasticsearch-dsl >= 8.0.0
```

## Examples

### Find documents by type
```python
generate_elasticsearch_query("Find all 1099 forms")
```

### Find documents in a folder
```python
generate_elasticsearch_query("Get all documents under folder ID abc-123")
```

### Complex query with multiple conditions
```python
generate_elasticsearch_query(
    "Find receipts from 2024 that are not PCI and have REALM auth type"
)
```

### Nested field query
```python
generate_elasticsearch_query(
    "Find documents with offering ID Intuit.qbo.documents"
)
```

## Modifying Resources

To update the tool's behavior, edit the files in `ai_tools/elasticsearch/resources/`:

1. **Add field descriptions**: Edit `FieldDescriptions.json`
2. **Update mapping**: Edit `Mapping.json`
3. **Add examples**: Edit `FewShotExamples.json`
4. **Modify prompt**: Edit `prompt_template.txt`

Changes take effect immediately - no code modifications needed!

**Note**: Resources are packaged with pip, so they're distributed with the tool. After modifying, reinstall the package:
```bash
pip install -e .  # For development
# or
pip install --upgrade akhera-ai-tools  # For production
```

## Troubleshooting

### Resource loading fails

If external resource files cannot be loaded, the tool will raise a `FileNotFoundError` or `json.JSONDecodeError`. Ensure:
- Resources are properly packaged (run `pip install -e .` in development)
- Resource files exist in `ai_tools/elasticsearch/resources/`
- JSON files are valid

### Validation fails

If a generated query fails validation, the LLM may have produced invalid DSL. Check the error message and consider:
- Adding more few-shot examples for similar queries
- Clarifying field descriptions
- Refining system prompt rules

### API timeout

Increase `TIMEOUT_SECONDS` for complex queries or slow network connections.

## Architecture

```
generate_elasticsearch_query(query)
  ↓
1. Load resources (JSON files or provided data)
  ↓
2. Build LLM prompt (system + user + examples)
  ↓
3. Call Claude Sonnet 4.5 API (with retries)
  ↓
4. Parse JSON response
  ↓
5. Validate with elasticsearch-dsl
  ↓
6. Return query or error
```

## License

See repository root for license information.

