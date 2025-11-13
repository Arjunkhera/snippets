# Tool: generate_elasticsearch_query

## Overview

**Description:** Generates syntactically valid Elasticsearch queries for the entities-v4 index based on natural language descriptions. This tool uses Claude Sonnet 4.5 with embedded mapping information, field descriptions, and few-shot examples to translate user queries into proper Elasticsearch DSL queries.

**Function Name:** `generate_elasticsearch_query`

**Target Index:** entities-v4

---

## Input Parameters

### query
- **Type:** `str`
- **Required:** Yes
- **Description:** Natural language query describing the search requirement. Examples:
  - "Fetch my W2's"
  - "Fetch all documents under FolderId ABC"
  - "Find all receipts that are not PCI"
  - "Search for documents with offering ID xyz"

---

## Success Output

When the tool successfully generates and validates an Elasticsearch query, it returns:

```json
{
  "elasticsearch_query": {
    "bool": {
      "must": [
        {
          "term": {
            "commonAttributes.documentType.keyword": "W2"
          }
        }
      ]
    }
  }
}
```

**Structure:**
- `elasticsearch_query` (object): A valid Elasticsearch DSL query object that can be executed directly against the entities-v4 index

---

## Error Outputs

The tool returns structured error responses for various failure scenarios:

### 1. EMPTY_QUERY
**Condition:** Query parameter is empty, null, or contains only whitespace

```json
{
  "error": "EMPTY_QUERY",
  "message": "Query cannot be empty. Please provide a natural language search description."
}
```

### 2. AMBIGUOUS_QUERY
**Condition:** The LLM cannot confidently map the query to Elasticsearch fields due to ambiguity

```json
{
  "error": "AMBIGUOUS_QUERY",
  "message": "The query is ambiguous. Please clarify: [specific ambiguity details from LLM]"
}
```

### 3. LLM_API_FAILURE
**Condition:** Anthropic API fails after all retry attempts (network error, service down, rate limiting)

```json
{
  "error": "LLM_API_FAILURE",
  "message": "Failed to generate query due to LLM API error: [error details]"
}
```

### 4. INVALID_API_KEY
**Condition:** ANTHROPIC_API_KEY environment variable is missing or invalid

```json
{
  "error": "INVALID_API_KEY",
  "message": "Anthropic API key is missing or invalid. Please set ANTHROPIC_API_KEY environment variable."
}
```

### 5. MALFORMED_RESPONSE
**Condition:** LLM returns a response that is not valid JSON or doesn't match expected structure

```json
{
  "error": "MALFORMED_RESPONSE",
  "message": "LLM generated an invalid response format: [details]"
}
```

### 6. VALIDATION_FAILED
**Condition:** Generated query fails elasticsearch-dsl validation (syntactically invalid ES query)

```json
{
  "error": "VALIDATION_FAILED",
  "message": "Generated query failed validation: [validation error details from elasticsearch-dsl]"
}
```

### 7. UNSUPPORTED_FIELD
**Condition:** Query references fields that don't exist in the entities-v4 mapping

```json
{
  "error": "UNSUPPORTED_FIELD",
  "message": "Query references unsupported field(s): [field names]. Available fields can be found in the mapping."
}
```

---

## Constraints & Behaviors

### Dependencies
- **Required Python packages:**
  - `anthropic` (>= 0.18.0) - For Claude Sonnet 4.5 API access
  - `elasticsearch-dsl` (>= 8.0.0) - For query validation

### Environment Variables
- **ANTHROPIC_API_KEY** (required): Valid Anthropic API key for making LLM requests

### LLM Configuration
- **Model:** claude-sonnet-4-5-20250929 (Claude Sonnet 4.5)
- **Temperature:** 0.0 (deterministic output)
- **Timeout:** 60 seconds per request
- **Retry Logic:** 3 attempts with exponential backoff (2s, 4s, 8s delays)

### Embedded Resources
The tool includes three embedded resources in the code:

1. **Elasticsearch Mapping** - Complete mapping from `Resources/Schemas/Mapping.json`
2. **Field Descriptions** - Semantic descriptions for each field (see `field_descriptions` section below)
3. **Few-Shot Examples** - Example natural language → ES query pairs (see `examples` section below)

### Validation Behavior
- All generated queries are validated using `elasticsearch-dsl` before being returned
- Validation ensures syntactic correctness only (not semantic correctness)
- If validation fails, the tool returns `VALIDATION_FAILED` error immediately (no retry)
- The tool does NOT execute queries - it only generates and validates them

### Query Generation Principles
- **Explicit Only:** Generate queries based only on what the user explicitly requests (no assumptions)
- **No Default Filters:** Do not add authentication, authorization, or other filters unless specified in the query
- **Pattern Agnostic:** Choose the most appropriate ES query pattern for the use case (bool, term, match, nested, etc.)
- **Ambiguity Handling:** If the query is ambiguous, return `AMBIGUOUS_QUERY` error asking for clarification

---

## LLM Prompt Foundation

This section defines the core prompt structure that will be used to instruct the LLM. The actual implementation will include the complete mapping, field descriptions, and examples embedded within this prompt template.

### System Role

```
You are an expert Elasticsearch query generator for the entities-v4 index. Your task is to convert natural language search descriptions into syntactically valid Elasticsearch DSL queries.
```

### Instructions to LLM

```
## Your Task

Convert the user's natural language query into a valid Elasticsearch DSL query for the entities-v4 index.

## Rules

1. **Use Only Valid Fields:** Only use fields that exist in the provided mapping below. Do not invent or assume fields.

2. **Exact Matches:** For text fields that have a .keyword subfield, use the .keyword version for exact matching (e.g., "entityType.keyword" not "entityType").

3. **Field Types:** Respect field types from the mapping:
   - Use `term` for exact matches on keyword/boolean/integer fields
   - Use `match` for full-text search on text fields
   - Use `range` for date/numeric ranges
   - Use `nested` queries for nested object arrays

4. **Query Structure:** Return ONLY the query object itself, not a complete search request. For example:
   ```json
   {
     "bool": {
       "must": [...]
     }
   }
   ```
   NOT:
   ```json
   {
     "query": {
       "bool": { ... }
     }
   }
   ```

5. **Ambiguity:** If the query is ambiguous or unclear, respond with:
   ```json
   {
     "error": "AMBIGUOUS_QUERY",
     "message": "Specific explanation of what is ambiguous and what clarification is needed"
   }
   ```

6. **Unknown Fields:** If the query asks for fields not in the mapping, respond with:
   ```json
   {
     "error": "UNSUPPORTED_FIELD",
     "message": "Field(s) not found in mapping: [list fields]"
   }
   ```

7. **Explicit Only:** Only include filters/conditions that are explicitly mentioned in the user's query. Do NOT add authentication, authorization, or other implicit filters.

8. **Best Practices:**
   - Combine multiple conditions with `bool` queries (must, should, must_not, filter)
   - Use `filter` context for exact matches that don't need scoring
   - Use `must` context when scoring/relevance matters
   - Handle both DOCUMENT and FOLDER entity types appropriately based on the query

## Elasticsearch Mapping

Below is the complete mapping for the entities-v4 index. Refer to this for all field names and types:

[MAPPING_JSON_PLACEHOLDER - To be embedded from Resources/Schemas/Mapping.json]

## Field Descriptions

The following descriptions explain the semantic meaning of key fields in the mapping:

[FIELD_DESCRIPTIONS_PLACEHOLDER - To be loaded from Resources/Schemas/FieldDescriptions.json]

## Examples

Here are example natural language queries and their corresponding Elasticsearch queries:

[EXAMPLES_PLACEHOLDER - To be loaded from Resources/Schemas/FewShotExamples.json]

## User Query

Now, convert this natural language query to an Elasticsearch DSL query:

"{user_query}"

## Your Response

Return ONLY valid JSON. Either:
1. A valid Elasticsearch query object, OR
2. An error object with "error" and "message" fields

Do not include any explanatory text outside the JSON.
```

### Output Format Requirements

The LLM must return one of:

**Success Response:**
```json
{
  "bool": {
    "must": [...]
  }
}
```

**Error Response:**
```json
{
  "error": "ERROR_CODE",
  "message": "Description"
}
```

---

## Implementation Notes

### File Structure
- **Tool Location:** `ai_tools/elasticsearch/generate_elasticsearch_query.py`
- **Tests Location:** `tests/elasticsearch/test_generate_elasticsearch_query.py`

### Embedded Resources Format

#### Field Descriptions
Create file: `Resources/Schemas/FieldDescriptions.json`

Expected format:
```json
{
  "entityType": "The type of entity: DOCUMENT or FOLDER",
  "authorization.isPci": "Boolean flag indicating if the document contains PCI (Payment Card Industry) sensitive data",
  "commonAttributes.documentType": "The classification/type of the document (e.g., W2, receipt, invoice, 1099)",
  "systemAttributes.parentId": "The unique identifier of the parent folder containing this entity",
  ...
}
```

**TODO:** Extract all field paths from mapping and create template for user to fill in descriptions.

#### Few-Shot Examples
Create file: `Resources/Schemas/FewShotExamples.json`

Expected format:
```json
[
  {
    "natural_language": "Search for documents under a specific client with relationship ID 9341455527283258",
    "elasticsearch_query": {
      "bool": {
        "must": [
          {
            "term": {
              "entityType.keyword": "FOLDER"
            }
          },
          {
            "term": {
              "commonAttributes.applicationAttributes.relationshipId.keyword": "9341455527283258"
            }
          }
        ]
      }
    }
  },
  ...
]
```

**TODO:** Reformat SampleSearchQueries.md into this JSON structure.

### Implementation Steps

1. Load embedded resources (mapping, field descriptions, examples) at module level
2. Construct prompt with user query
3. Call Anthropic API with retry logic
4. Parse LLM response
5. Validate with elasticsearch-dsl
6. Return result

### Testing Requirements

Tests should cover:
- Successful query generation for each example type
- All error conditions (empty query, ambiguous, API failure, etc.)
- Validation catches malformed queries
- Field path validation works correctly
- Retry logic functions properly
- LLM response parsing handles edge cases

---

## Version History

- **v1.0.0** (Initial) - Basic query generation with validation
