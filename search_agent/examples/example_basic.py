"""
Basic example demonstrating Phase 1 components.

This example shows how to:
1. Create initial state
2. Use the mock Elasticsearch service
3. Call the LLM service
4. Work with Pydantic models

NOTE: This is a Phase 1 example. Full agent workflow examples
will be added in Phase 6 after all nodes are implemented.
"""

import json
from search_agent.core.state import create_initial_state
from search_agent.core.models import QueryPlan, Step
from search_agent.services import get_elasticsearch_service, get_llm_service
from search_agent.utils import format_document_for_display
from search_agent.config import settings


def example_1_create_state():
    """Example 1: Creating and inspecting agent state."""
    print("=" * 60)
    print("Example 1: Creating Agent State")
    print("=" * 60)

    state = create_initial_state(
        user_query="List documents in Tax Documents folder",
        conversation_id="example-conv-1"
    )

    print(f"\nUser Query: {state['user_query']}")
    print(f"Conversation ID: {state['conversation_id']}")
    print(f"Created At: {state['created_at']}")
    print(f"Current Step: {state['current_step']}")
    print(f"Total Steps: {state['total_steps']}")

    print("\nState keys:", list(state.keys()))


def example_2_mock_elasticsearch():
    """Example 2: Using mock Elasticsearch service."""
    print("\n" + "=" * 60)
    print("Example 2: Mock Elasticsearch Service")
    print("=" * 60)

    # Get mock ES service
    es_service = get_elasticsearch_service()

    # Query for a folder
    folder_query = {
        "bool": {
            "must": [
                {"term": {"entityType.keyword": "FOLDER"}},
                {"term": {"commonAttributes.name.keyword": "Tax Documents"}}
            ]
        }
    }

    print("\nQuerying for folder 'Tax Documents'...")
    result = es_service.search(folder_query)

    print(f"Found {result['hits']['total']['value']} folder(s)")

    if result['hits']['hits']:
        folder = result['hits']['hits'][0]['_source']
        print(f"Folder Name: {folder['commonAttributes']['name']}")
        print(f"Folder ID: {folder['systemAttributes']['id']}")
        print(f"Folder Path: {folder['organizationAttributes']['folderPath']}")

        # Now query for documents in that folder
        folder_id = folder['systemAttributes']['id']
        doc_query = {
            "bool": {
                "must": [
                    {"term": {"entityType.keyword": "DOCUMENT"}},
                    {"term": {"systemAttributes.parentId.keyword": folder_id}}
                ]
            }
        }

        print(f"\nQuerying for documents in folder {folder_id}...")
        doc_result = es_service.search(doc_query)

        print(f"Found {doc_result['hits']['total']['value']} document(s)")

        for hit in doc_result['hits']['hits']:
            doc = hit['_source']
            print("\n" + format_document_for_display(doc))


def example_3_llm_service():
    """Example 3: Using LLM service."""
    print("\n" + "=" * 60)
    print("Example 3: LLM Service")
    print("=" * 60)

    # Check if API key is configured
    if not settings.ANTHROPIC_API_KEY:
        print("⚠️  ANTHROPIC_API_KEY not set. Skipping LLM example.")
        print("Set the API key to run this example:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        return

    llm = get_llm_service()

    # Simple query
    print("\nAsking LLM: What is 2+2?")
    response = llm.call_with_retry("What is 2+2? Answer with just the number.")
    print(f"Response: {response}")

    # JSON response
    print("\nAsking LLM for JSON response...")
    json_prompt = """
Return a JSON object with the following structure:
{
  "answer": <the sum of 5+3>,
  "explanation": "brief explanation"
}

Return ONLY the JSON, no other text.
"""
    json_response = llm.call_with_json_response(json_prompt)
    print(f"JSON Response: {json.dumps(json_response, indent=2)}")


def example_4_pydantic_models():
    """Example 4: Working with Pydantic models."""
    print("\n" + "=" * 60)
    print("Example 4: Pydantic Models")
    print("=" * 60)

    # Create a query plan
    plan = QueryPlan(
        plan_type="multi_step",
        reasoning="User references folder by name but documents need folder ID",
        total_steps=2,
        steps=[
            Step(
                step=1,
                description="Find the folder named 'Tax Documents' to get its ID"
            ),
            Step(
                step=2,
                description="Find all documents where parent folder ID matches step 1",
                depends_on_step=1
            )
        ]
    )

    print("\nCreated Query Plan:")
    print(plan.model_dump_json(indent=2))

    # Validate the plan
    print("\nPlan is valid! ✓")
    print(f"Plan Type: {plan.plan_type}")
    print(f"Total Steps: {plan.total_steps}")
    print(f"Steps: {len(plan.steps)}")

    # Try creating an invalid plan
    print("\n\nTrying to create invalid plan (single_step with 2 steps)...")
    try:
        invalid_plan = QueryPlan(
            plan_type="single_step",
            reasoning="Test",
            total_steps=2,
            steps=[
                Step(step=1, description="Step 1"),
                Step(step=2, description="Step 2")
            ]
        )
    except Exception as e:
        print(f"✓ Validation error caught: {str(e)[:80]}...")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("SEARCH AGENT - PHASE 1 EXAMPLES")
    print("=" * 60)

    example_1_create_state()
    example_2_mock_elasticsearch()
    example_3_llm_service()
    example_4_pydantic_models()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
