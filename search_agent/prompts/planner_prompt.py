"""
Query Planner Prompt Template.

This module provides the prompt template for the query planner node.
The planner determines whether a search query needs single-step or multi-step execution.
"""

import json
from pathlib import Path
from typing import Dict, Any

from search_agent.config import settings


def load_es_mapping() -> Dict[str, Any]:
    """
    Load Elasticsearch mapping from resources.

    Returns:
        Dict containing the ES mapping

    Raises:
        FileNotFoundError: If mapping file doesn't exist
        json.JSONDecodeError: If mapping file is invalid JSON
    """
    mapping_path = settings.es_mapping_path

    if not mapping_path.exists():
        raise FileNotFoundError(
            f"ES mapping file not found: {mapping_path}. "
            f"Ensure ai_tools/elasticsearch/resources/Mapping.json exists."
        )

    with open(mapping_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_multi_step_examples() -> str:
    """
    Get multi-step query examples from PRD Section 8.

    Returns:
        Formatted string containing example queries and their plans
    """
    return """
## Category 1: Name-to-ID Resolution

**Example 1.1: Folder Name to Documents**
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

**Example 1.2: Folder Name to Subfolders**
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

**Example 1.3: Document Name to Folder**
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

## Category 2: Sibling/Related Entity Queries

**Example 2.1: Sibling Documents**
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

**Example 2.2: Parent Folder of Subfolder**
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

## Category 3: Attribute-Based Matching

**Example 3.1: Documents with Same Category**
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

## Category 4: Combined Filters with Name Resolution

**Example 4.1: W2 Documents in Named Folder**
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

## SINGLE-STEP COUNTER-EXAMPLES

**Counter-Example 1: Direct Document Type Search**
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

**Counter-Example 2: Folder ID Provided**
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

**Counter-Example 3: Root Level Query**
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
"""


def build_planner_prompt(user_query: str) -> str:
    """
    Build the complete planner prompt for a given user query.

    Args:
        user_query: The natural language query from the user

    Returns:
        Complete formatted prompt for the LLM

    Raises:
        FileNotFoundError: If ES mapping file is not found
    """
    # Load ES mapping
    es_mapping = load_es_mapping()
    mapping_json = json.dumps(es_mapping, indent=2)

    # Get examples
    examples = get_multi_step_examples()

    # Build complete prompt
    prompt = f"""# ROLE

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

{mapping_json}

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

{examples}

# USER QUERY

{user_query}

# OUTPUT FORMAT

Respond with JSON only (no markdown, no explanation outside JSON):

{{
  "plan_type": "single_step" | "multi_step",
  "reasoning": "Detailed explanation of your gap analysis and why this approach is needed. Be specific about what fields are missing and how you'll resolve them.",
  "total_steps": 1 | 2 | 3,
  "steps": [
    {{
      "step": 1,
      "description": "High-level natural language description. Focus on WHAT to find, not HOW. Example: 'Find the folder named Tax Documents' NOT 'Query FOLDER where commonAttributes.name.keyword equals Tax Documents'",
      "depends_on_step": null  // or 1, 2 for dependent steps
    }}
  ]
}}

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

6. Output ONLY valid JSON - no markdown code blocks, no additional text
"""

    return prompt


if __name__ == "__main__":
    # Test the prompt generation
    test_query = "List documents in Tax Documents folder"
    prompt = build_planner_prompt(test_query)
    print("Planner Prompt Generated Successfully")
    print(f"Prompt length: {len(prompt)} characters")
    print("\n" + "=" * 50)
    print("Sample prompt (first 500 chars):")
    print(prompt[:500])
