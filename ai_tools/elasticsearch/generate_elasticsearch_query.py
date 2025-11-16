"""
Elasticsearch Query Generator Tool

This tool generates syntactically valid Elasticsearch DSL queries for the entities-v4 index
based on natural language descriptions using Claude Sonnet 4.5.

Dependencies:
    - anthropic >= 0.18.0
    - elasticsearch-dsl >= 8.0.0

Environment Variables:
    - ANTHROPIC_API_KEY: Valid Anthropic API key (required)
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Requires: anthropic >= 0.18.0
try:
    from anthropic import Anthropic, APIError, AuthenticationError, APIConnectionError
except ImportError:
    Anthropic = None
    APIError = None
    AuthenticationError = None
    APIConnectionError = None

# Requires: elasticsearch-dsl >= 8.0.0
try:
    from elasticsearch_dsl import Q, Search
    from elasticsearch_dsl.exceptions import ValidationException
except ImportError:
    Q = None
    Search = None
    ValidationException = None


# --- Default Resource Paths ---

# Get the directory containing this script
_SCRIPT_DIR = Path(__file__).parent.resolve()
_RESOURCES_DIR = _SCRIPT_DIR / "resources"

DEFAULT_MAPPING_PATH = _RESOURCES_DIR / "Mapping.json"
DEFAULT_FIELD_DESCRIPTIONS_PATH = _RESOURCES_DIR / "FieldDescriptions.json"
DEFAULT_FEW_SHOT_EXAMPLES_PATH = _RESOURCES_DIR / "FewShotExamples.json"
DEFAULT_FULL_DOCUMENT_PATH = _RESOURCES_DIR / "FullDocument.json"
DEFAULT_PROMPT_TEMPLATE_PATH = _RESOURCES_DIR / "prompt_template.txt"


# --- Resource Loading Functions ---

def _load_json_file(file_path: Path) -> Any:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON content
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _load_elasticsearch_mapping(mapping_path: Optional[Path] = None) -> str:
    """
    Load Elasticsearch mapping from JSON file.
    
    Args:
        mapping_path: Optional custom path to mapping file
        
    Returns:
        Mapping as JSON string
    """
    path = mapping_path or DEFAULT_MAPPING_PATH
    mapping_dict = _load_json_file(path)
    return json.dumps(mapping_dict, indent=2)


def _load_field_descriptions(descriptions_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load field descriptions from JSON file.
    
    Args:
        descriptions_path: Optional custom path to descriptions file
        
    Returns:
        Dictionary of field descriptions
    """
    path = descriptions_path or DEFAULT_FIELD_DESCRIPTIONS_PATH
    return _load_json_file(path)


def _load_few_shot_examples(examples_path: Optional[Path] = None) -> list:
    """
    Load few-shot examples from JSON file.
    
    Args:
        examples_path: Optional custom path to examples file
        
    Returns:
        List of example dictionaries
    """
    path = examples_path or DEFAULT_FEW_SHOT_EXAMPLES_PATH
    return _load_json_file(path)


def _load_full_document(full_document_path: Optional[Path] = None) -> str:
    """
    Load full document example from JSON file.
    
    Args:
        full_document_path: Optional custom path to full document file
        
    Returns:
        Full document as JSON string
    """
    path = full_document_path or DEFAULT_FULL_DOCUMENT_PATH
    full_document_dict = _load_json_file(path)
    return json.dumps(full_document_dict, indent=2)


def _load_prompt_template(template_path: Optional[Path] = None) -> str:
    """
    Load prompt template from text file.
    
    Args:
        template_path: Optional custom path to template file
        
    Returns:
        Prompt template string
        
    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    path = template_path or DEFAULT_PROMPT_TEMPLATE_PATH
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# --- Configuration Constants ---

MODEL_NAME = "claude-sonnet-4-5-20250929"
TEMPERATURE = 0.0
TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # Exponential backoff in seconds


# --- Helper Functions ---

def _build_llm_prompt(
    user_query: str,
    mapping: Optional[str] = None,
    field_descriptions: Optional[Dict[str, str]] = None,
    few_shot_examples: Optional[list] = None,
    full_document: Optional[str] = None,
    prompt_template: Optional[str] = None
) -> str:
    """
    Builds the complete prompt for the LLM including mapping, descriptions, and examples.

    Args:
        user_query: The natural language query from the user
        mapping: Optional Elasticsearch mapping JSON string (loads from file if not provided)
        field_descriptions: Optional field descriptions dict (loads from file if not provided)
        few_shot_examples: Optional few-shot examples list (loads from file if not provided)
        full_document: Optional full document example JSON string (loads from file if not provided)
        prompt_template: Optional prompt template string (loads from file if not provided)

    Returns:
        Complete prompt string
        
    Raises:
        FileNotFoundError: If required resource files cannot be found
        json.JSONDecodeError: If resource files contain invalid JSON
    """
    # Load resources if not provided
    if mapping is None:
        mapping = _load_elasticsearch_mapping()
    if field_descriptions is None:
        field_descriptions = _load_field_descriptions()
    if few_shot_examples is None:
        few_shot_examples = _load_few_shot_examples()
    if full_document is None:
        full_document = _load_full_document()
    if prompt_template is None:
        prompt_template = _load_prompt_template()

    # Format field descriptions
    descriptions_str = "\n".join([f"- **{k}**: {v}" for k, v in field_descriptions.items()])

    # Format few-shot examples
    examples_str = ""
    for i, example in enumerate(few_shot_examples, 1):
        examples_str += f"\n### Example {i}\n"
        examples_str += f"**Natural Language**: {example['natural_language']}\n\n"
        examples_str += f"**Elasticsearch Query**:\n```json\n{json.dumps(example['elasticsearch_query'], indent=2)}\n```\n"

    # Replace placeholders in template
    prompt = prompt_template.replace("{{MAPPING}}", mapping)
    prompt = prompt.replace("{{FIELD_DESCRIPTIONS}}", descriptions_str)
    prompt = prompt.replace("{{FULL_DOCUMENT}}", full_document)
    prompt = prompt.replace("{{FEW_SHOT_EXAMPLES}}", examples_str)
    prompt = prompt.replace("{{USER_QUERY}}", user_query)

    return prompt


def _call_llm_with_retry(prompt: str, api_key: str) -> Dict[str, Any]:
    """
    Calls the Anthropic API with retry logic.

    Args:
        prompt: The complete prompt to send
        api_key: Anthropic API key

    Returns:
        Parsed JSON response from the LLM

    Raises:
        Exception: If all retries fail
    """
    client = Anthropic(api_key=api_key)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=4096,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=TIMEOUT_SECONDS
            )

            # Extract text from response
            response_text = response.content[0].text.strip()

            # Parse JSON from response
            # Handle case where response might be wrapped in ```json blocks
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            parsed_response = json.loads(response_text)
            return parsed_response

        except (APIConnectionError, APIError) as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            else:
                raise Exception(f"API call failed after {MAX_RETRIES} attempts: {str(e)}")
        except AuthenticationError as e:
            # Don't retry on auth errors
            raise Exception(f"Authentication failed: {str(e)}")
        except json.JSONDecodeError as e:
            # Don't retry on JSON parsing errors - this is a malformed response
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")


def _validate_query(query_dict: Dict[str, Any]) -> None:
    """
    Validates an Elasticsearch query using elasticsearch-dsl library.

    Args:
        query_dict: The query dictionary to validate

    Raises:
        Exception: If validation fails
    """
    try:
        # Create a Search object and apply the query
        s = Search()
        s = s.query(Q(query_dict))

        # Attempt to convert to dict (this triggers validation)
        _ = s.to_dict()

    except Exception as e:
        raise Exception(f"Query validation failed: {str(e)}")


# --- Main Tool Function ---

def generate_elasticsearch_query(
    query: str,
    mapping: Optional[str] = None,
    field_descriptions: Optional[Dict[str, str]] = None,
    few_shot_examples: Optional[list] = None,
    full_document: Optional[str] = None,
    mapping_path: Optional[Path] = None,
    field_descriptions_path: Optional[Path] = None,
    few_shot_examples_path: Optional[Path] = None,
    full_document_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generates a syntactically valid Elasticsearch DSL query for the entities-v4 index
    based on a natural language description.

    This tool uses Claude Sonnet 4.5 with mapping information, field descriptions,
    full document example, and few-shot examples to translate user queries into proper 
    Elasticsearch DSL queries.

    Args:
        query: Natural language query describing the search requirement.
               Examples: "Fetch my W2's", "Find all documents under FolderId ABC"
        mapping: Optional Elasticsearch mapping JSON string (loads from file if not provided)
        field_descriptions: Optional field descriptions dict (loads from file if not provided)
        few_shot_examples: Optional few-shot examples list (loads from file if not provided)
        full_document: Optional full document example JSON string (loads from file if not provided)
        mapping_path: Optional custom path to mapping JSON file
        field_descriptions_path: Optional custom path to field descriptions JSON file
        few_shot_examples_path: Optional custom path to few-shot examples JSON file
        full_document_path: Optional custom path to full document JSON file

    Returns:
        A dictionary containing either:
        - {"elasticsearch_query": <valid ES query object>} on success
        - {"error": <ERROR_CODE>, "message": <description>} on failure

    Error Codes:
        - EMPTY_QUERY: Query parameter is empty or whitespace
        - AMBIGUOUS_QUERY: LLM cannot confidently map the query
        - LLM_API_FAILURE: Anthropic API failed after retries
        - INVALID_API_KEY: ANTHROPIC_API_KEY missing or invalid
        - MALFORMED_RESPONSE: Invalid JSON from LLM
        - VALIDATION_FAILED: Query failed elasticsearch-dsl validation
        - UNSUPPORTED_FIELD: Query references non-existent fields
        - RESOURCE_LOAD_ERROR: Failed to load external resources

    Environment Variables:
        ANTHROPIC_API_KEY: Valid Anthropic API key (required)

    Dependencies:
        - anthropic >= 0.18.0
        - elasticsearch-dsl >= 8.0.0
    
    Default Resource Paths:
        - Mapping: Resources/Schemas/Mapping.json
        - Field Descriptions: Resources/Schemas/FieldDescriptions.json
        - Few-Shot Examples: Resources/Schemas/FewShotExamples.json
        - Full Document: Resources/Schemas/FullDocument.json
    """
    # Check for empty query
    if not query or not query.strip():
        return {
            "error": "EMPTY_QUERY",
            "message": "Query cannot be empty. Please provide a natural language search description."
        }

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "error": "INVALID_API_KEY",
            "message": "Anthropic API key is missing or invalid. Please set ANTHROPIC_API_KEY environment variable."
        }

    # Load resources from custom paths if provided
    try:
        if mapping_path is not None and mapping is None:
            mapping = _load_elasticsearch_mapping(mapping_path)
        if field_descriptions_path is not None and field_descriptions is None:
            field_descriptions = _load_field_descriptions(field_descriptions_path)
        if few_shot_examples_path is not None and few_shot_examples is None:
            few_shot_examples = _load_few_shot_examples(few_shot_examples_path)
        if full_document_path is not None and full_document is None:
            full_document = _load_full_document(full_document_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {
            "error": "RESOURCE_LOAD_ERROR",
            "message": f"Failed to load external resources: {str(e)}"
        }

    try:
        # Build the prompt
        prompt = _build_llm_prompt(
            query.strip(),
            mapping=mapping,
            field_descriptions=field_descriptions,
            few_shot_examples=few_shot_examples,
            full_document=full_document
        )

        # Call LLM with retry logic
        try:
            llm_response = _call_llm_with_retry(prompt, api_key)
        except Exception as e:
            error_msg = str(e)
            if "Authentication" in error_msg or "API key" in error_msg:
                return {
                    "error": "INVALID_API_KEY",
                    "message": f"Anthropic API key is missing or invalid. Please set ANTHROPIC_API_KEY environment variable."
                }
            elif "JSON" in error_msg or "parse" in error_msg:
                return {
                    "error": "MALFORMED_RESPONSE",
                    "message": f"LLM generated an invalid response format: {error_msg}"
                }
            else:
                return {
                    "error": "LLM_API_FAILURE",
                    "message": f"Failed to generate query due to LLM API error: {error_msg}"
                }

        # Check if LLM returned an error
        if "error" in llm_response:
            error_code = llm_response.get("error")
            error_message = llm_response.get("message", "No message provided")

            # Return the error as-is (AMBIGUOUS_QUERY or UNSUPPORTED_FIELD)
            return {
                "error": error_code,
                "message": error_message
            }

        # LLM returned a query - validate it
        try:
            _validate_query(llm_response)
        except Exception as e:
            return {
                "error": "VALIDATION_FAILED",
                "message": f"Generated query failed validation: {str(e)}"
            }

        # Success - return the validated query
        return {
            "elasticsearch_query": llm_response
        }

    except Exception as e:
        # Catch-all for unexpected errors
        return {
            "error": "LLM_API_FAILURE",
            "message": f"An unexpected error occurred: {str(e)}"
        }


# --- Main Entry Point ---

def main():
    """
    Main function to demonstrate the usage of generate_elasticsearch_query when script is run directly.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate_elasticsearch_query.py <natural_language_query>")
        print("\nExample:")
        print('  python generate_elasticsearch_query.py "Find all W2 documents"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    result = generate_elasticsearch_query(query)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
