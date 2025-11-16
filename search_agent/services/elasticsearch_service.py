"""
Elasticsearch service interface and mock implementation.

The ElasticsearchService provides an abstraction for ES queries, making it easy
to swap between mock (Phase 1) and real (Phase 3+) implementations.

Example:
    >>> from search_agent.config import settings
    >>> if settings.USE_MOCK_ELASTICSEARCH:
    ...     es_service = MockElasticsearchService()
    ... else:
    ...     es_service = ElasticsearchService(settings.ELASTICSEARCH_URL)
    >>> results = es_service.search({"match_all": {}})
"""

import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from search_agent.config import settings


class ElasticsearchServiceInterface(ABC):
    """
    Abstract interface for Elasticsearch operations.

    All ES service implementations must implement these methods.
    """

    @abstractmethod
    def search(
        self,
        query: Dict[str, Any],
        size: int = 100,
        index: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an Elasticsearch query.

        Args:
            query: Elasticsearch DSL query object (not wrapped in {"query": ...})
            size: Maximum number of results to return
            index: Index name (defaults to config value)

        Returns:
            Elasticsearch response with hits, total, etc.

        Raises:
            ElasticsearchError: If query execution fails
        """
        pass

    @abstractmethod
    def validate_query(self, query: Dict[str, Any]) -> List[str]:
        """
        Validate an Elasticsearch query structure.

        Args:
            query: Elasticsearch DSL query object

        Returns:
            List of validation error messages (empty list if valid)
        """
        pass


class ElasticsearchService(ElasticsearchServiceInterface):
    """
    Real Elasticsearch service implementation.

    This will be implemented in Phase 3+ when connecting to actual ES.
    For now, raises NotImplementedError.

    Args:
        elasticsearch_url: ES instance URL
        index: Default index name

    Example:
        >>> es = ElasticsearchService("http://localhost:9200")
        >>> results = es.search({"match_all": {}})
    """

    def __init__(
        self,
        elasticsearch_url: str = settings.ELASTICSEARCH_URL,
        index: str = settings.ELASTICSEARCH_INDEX
    ):
        self.elasticsearch_url = elasticsearch_url
        self.index = index
        # TODO Phase 3: Initialize real Elasticsearch client here
        # from elasticsearch import Elasticsearch
        # self.client = Elasticsearch([elasticsearch_url])

    def search(
        self,
        query: Dict[str, Any],
        size: int = 100,
        index: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an Elasticsearch query.

        Phase 3 Implementation: Use real Elasticsearch client.
        """
        raise NotImplementedError(
            "Real Elasticsearch service not implemented yet. "
            "Set USE_MOCK_ELASTICSEARCH=True in config for Phase 1."
        )

    def validate_query(self, query: Dict[str, Any]) -> List[str]:
        """
        Validate an Elasticsearch query structure.

        Phase 3 Implementation: Use elasticsearch-dsl validation.
        """
        raise NotImplementedError(
            "Real Elasticsearch validation not implemented yet. "
            "Set USE_MOCK_ELASTICSEARCH=True in config for Phase 1."
        )


class MockElasticsearchService(ElasticsearchServiceInterface):
    """
    Mock Elasticsearch service for testing and Phase 1 development.

    Returns realistic sample data based on the query structure.
    Simulates network delay for realistic testing.

    Example:
        >>> es = MockElasticsearchService()
        >>> results = es.search({
        ...     "bool": {
        ...         "must": [
        ...             {"term": {"entityType.keyword": "FOLDER"}},
        ...             {"term": {"commonAttributes.name.keyword": "Tax Documents"}}
        ...         ]
        ...     }
        ... })
        >>> results["hits"]["total"]["value"]
        1
    """

    def __init__(self, delay_ms: int = settings.MOCK_ES_DELAY_MS):
        """
        Initialize mock service.

        Args:
            delay_ms: Simulated network delay in milliseconds
        """
        self.delay_ms = delay_ms
        self._load_sample_data()

    def _load_sample_data(self):
        """Load sample documents for mock responses."""
        # Sample folder document
        self.sample_folder = {
            "_index": "entities-v4",
            "_id": "folder-tax-documents",
            "_score": 1.0,
            "_source": {
                "entityType": "FOLDER",
                "systemAttributes": {
                    "id": "4d3a2df1-1678-498c-99ee-b55960542d30",
                    "parentId": "root",
                    "createDate": 1700000000000,
                    "modifyDate": 1700000000000,
                    "owner": {
                        "ownerAccountId": "test-account-123",
                        "ownerAccountType": "REALM"
                    }
                },
                "commonAttributes": {
                    "name": "Tax Documents",
                    "description": "Folder for tax-related documents"
                },
                "organizationAttributes": {
                    "folderPath": "root/Tax Documents",
                    "parentFolderId": "root",
                    "folderPathIds": ["root", "4d3a2df1-1678-498c-99ee-b55960542d30"]
                }
            }
        }

        # Sample document
        self.sample_document = {
            "_index": "entities-v4",
            "_id": "doc-w2-2024",
            "_score": 1.0,
            "_source": {
                "entityType": "DOCUMENT",
                "systemAttributes": {
                    "id": "30398388-e3ee-467a-b342-3bc8c33f3af8",
                    "parentId": "4d3a2df1-1678-498c-99ee-b55960542d30",
                    "createDate": 1700000000000,
                    "modifyDate": 1700000000000,
                    "owner": {
                        "ownerAccountId": "test-account-123",
                        "ownerAccountType": "REALM"
                    },
                    "originalDocumentName": "W2_2024.pdf",
                    "size": 326603
                },
                "commonAttributes": {
                    "name": "W2_2024.pdf",
                    "documentType": "W2",
                    "taxYear": "2024",
                    "description": "W2 form for 2024"
                },
                "organizationAttributes": {
                    "folderPath": "root/Tax Documents",
                    "parentFolderId": "4d3a2df1-1678-498c-99ee-b55960542d30",
                    "folderPathIds": ["root", "4d3a2df1-1678-498c-99ee-b55960542d30"]
                }
            }
        }

    def search(
        self,
        query: Dict[str, Any],
        size: int = 100,
        index: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a mock Elasticsearch query.

        Returns realistic sample data based on the query structure.
        Simulates network delay.

        Args:
            query: Elasticsearch DSL query object
            size: Maximum number of results (not used in mock)
            index: Index name (not used in mock)

        Returns:
            Mock Elasticsearch response
        """
        # Simulate network delay
        if self.delay_ms > 0:
            time.sleep(self.delay_ms / 1000.0)

        # Analyze query to determine what to return
        query_str = json.dumps(query).lower()

        # Check if looking for folder
        if '"entitytype.keyword": "folder"' in query_str or '"entitytype": "folder"' in query_str:
            # Check if looking for specific folder name
            if '"tax documents"' in query_str or '"tax"' in query_str:
                # Return folder result
                return {
                    "took": self.delay_ms,
                    "timed_out": False,
                    "hits": {
                        "total": {"value": 1, "relation": "eq"},
                        "max_score": 1.0,
                        "hits": [self.sample_folder]
                    }
                }
            else:
                # Generic folder query
                return {
                    "took": self.delay_ms,
                    "timed_out": False,
                    "hits": {
                        "total": {"value": 1, "relation": "eq"},
                        "max_score": 1.0,
                        "hits": [self.sample_folder]
                    }
                }

        # Check if looking for documents
        elif '"entitytype.keyword": "document"' in query_str or '"entitytype": "document"' in query_str:
            # Check if filtering by parent folder ID
            if '4d3a2df1-1678-498c-99ee-b55960542d30' in query_str:
                # Return documents in Tax Documents folder
                return {
                    "took": self.delay_ms,
                    "timed_out": False,
                    "hits": {
                        "total": {"value": 3, "relation": "eq"},
                        "max_score": 1.0,
                        "hits": [
                            self.sample_document,
                            {
                                **self.sample_document,
                                "_id": "doc-1099-2024",
                                "_source": {
                                    **self.sample_document["_source"],
                                    "systemAttributes": {
                                        **self.sample_document["_source"]["systemAttributes"],
                                        "id": "doc-1099-2024-id",
                                        "originalDocumentName": "1099_2024.pdf"
                                    },
                                    "commonAttributes": {
                                        **self.sample_document["_source"]["commonAttributes"],
                                        "name": "1099_2024.pdf",
                                        "documentType": "1099"
                                    }
                                }
                            },
                            {
                                **self.sample_document,
                                "_id": "doc-receipt-jan",
                                "_source": {
                                    **self.sample_document["_source"],
                                    "systemAttributes": {
                                        **self.sample_document["_source"]["systemAttributes"],
                                        "id": "doc-receipt-jan-id",
                                        "originalDocumentName": "Receipt_Jan.pdf"
                                    },
                                    "commonAttributes": {
                                        **self.sample_document["_source"]["commonAttributes"],
                                        "name": "Receipt_Jan.pdf",
                                        "documentType": "receipt"
                                    }
                                }
                            }
                        ]
                    }
                }
            else:
                # Generic document query
                return {
                    "took": self.delay_ms,
                    "timed_out": False,
                    "hits": {
                        "total": {"value": 1, "relation": "eq"},
                        "max_score": 1.0,
                        "hits": [self.sample_document]
                    }
                }

        # Default: return empty results
        return {
            "took": self.delay_ms,
            "timed_out": False,
            "hits": {
                "total": {"value": 0, "relation": "eq"},
                "max_score": None,
                "hits": []
            }
        }

    def validate_query(self, query: Dict[str, Any]) -> List[str]:
        """
        Validate an Elasticsearch query structure (mock implementation).

        For Phase 1, performs basic structural validation.

        Args:
            query: Elasticsearch DSL query object

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Basic structural validation
        if not isinstance(query, dict):
            errors.append("Query must be a dictionary")
            return errors

        # Check for common query types
        valid_root_keys = {"bool", "match", "term", "terms", "range", "match_all", "nested", "prefix"}
        if not any(key in query for key in valid_root_keys):
            errors.append(f"Query must contain at least one of: {', '.join(valid_root_keys)}")

        # Validate bool query structure if present
        if "bool" in query:
            bool_query = query["bool"]
            if not isinstance(bool_query, dict):
                errors.append("bool query must be a dictionary")
            else:
                valid_bool_keys = {"must", "should", "must_not", "filter"}
                for key in bool_query.keys():
                    if key not in valid_bool_keys:
                        errors.append(f"Invalid bool clause: {key}")

        return errors


def get_elasticsearch_service() -> ElasticsearchServiceInterface:
    """
    Factory function to get the appropriate Elasticsearch service.

    Returns mock or real service based on configuration.

    Returns:
        Elasticsearch service instance

    Example:
        >>> es_service = get_elasticsearch_service()
        >>> results = es_service.search({"match_all": {}})
    """
    if settings.USE_MOCK_ELASTICSEARCH:
        return MockElasticsearchService()
    else:
        return ElasticsearchService()
