"""
Validation and formatting utilities.

Provides helper functions for query validation, field extraction,
and result formatting.
"""

from typing import Dict, Any, List, Set


def extract_fields_from_query(query: Dict[str, Any]) -> Set[str]:
    """
    Extract all field names referenced in an Elasticsearch query.

    Recursively traverses the query structure to find all field references.

    Args:
        query: Elasticsearch DSL query object

    Returns:
        Set of field names referenced in the query

    Example:
        >>> query = {
        ...     "bool": {
        ...         "must": [
        ...             {"term": {"entityType.keyword": "FOLDER"}},
        ...             {"term": {"commonAttributes.name.keyword": "Tax"}}
        ...         ]
        ...     }
        ... }
        >>> fields = extract_fields_from_query(query)
        >>> "entityType.keyword" in fields
        True
    """
    fields: Set[str] = set()

    def extract_recursive(obj: Any) -> None:
        """Recursively extract fields from nested structures."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Known query types that contain field names as keys
                if key in {"term", "terms", "match", "range", "prefix", "wildcard", "exists"}:
                    if isinstance(value, dict):
                        # Field names are the keys
                        fields.update(value.keys())
                elif key == "nested":
                    # Nested queries have path and query
                    if isinstance(value, dict):
                        if "path" in value:
                            fields.add(value["path"])
                        if "query" in value:
                            extract_recursive(value["query"])
                else:
                    # Recurse into nested structures
                    extract_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_recursive(item)

    extract_recursive(query)
    return fields


def validate_elasticsearch_query(query: Dict[str, Any]) -> List[str]:
    """
    Validate an Elasticsearch query structure.

    Performs basic structural validation (more comprehensive validation
    will be added in Phase 3).

    Args:
        query: Elasticsearch DSL query object

    Returns:
        List of validation error messages (empty if valid)

    Example:
        >>> query = {"bool": {"must": []}}
        >>> errors = validate_elasticsearch_query(query)
        >>> len(errors)
        0
    """
    errors = []

    # Must be a dictionary
    if not isinstance(query, dict):
        errors.append("Query must be a dictionary")
        return errors

    # Must have at least one valid root key
    valid_root_keys = {
        "bool", "match", "term", "terms", "range",
        "match_all", "nested", "prefix", "wildcard", "exists"
    }

    if not any(key in query for key in valid_root_keys):
        errors.append(
            f"Query must contain at least one of: {', '.join(sorted(valid_root_keys))}"
        )

    # Validate bool query structure
    if "bool" in query:
        bool_query = query["bool"]
        if not isinstance(bool_query, dict):
            errors.append("bool query value must be a dictionary")
        else:
            valid_bool_clauses = {"must", "should", "must_not", "filter"}
            invalid_clauses = set(bool_query.keys()) - valid_bool_clauses
            if invalid_clauses:
                errors.append(
                    f"Invalid bool clauses: {', '.join(sorted(invalid_clauses))}. "
                    f"Valid clauses: {', '.join(sorted(valid_bool_clauses))}"
                )

            # Each clause must be a list
            for clause in valid_bool_clauses:
                if clause in bool_query and not isinstance(bool_query[clause], list):
                    errors.append(f"bool.{clause} must be a list")

    return errors


def format_folder_path(folder_source: Dict[str, Any]) -> str:
    """
    Format a folder's path for display.

    Args:
        folder_source: Elasticsearch _source document for a folder

    Returns:
        Formatted folder path string

    Example:
        >>> folder = {
        ...     "organizationAttributes": {
        ...         "folderPath": "root/Tax Documents/2024"
        ...     },
        ...     "commonAttributes": {
        ...         "name": "2024"
        ...     }
        ... }
        >>> format_folder_path(folder)
        '/root/Tax Documents/2024'
    """
    # Try to get folder path
    folder_path = (
        folder_source.get("organizationAttributes", {})
        .get("folderPath", "")
    )

    if folder_path:
        # Convert "root/..." to "/root/..."
        if not folder_path.startswith("/"):
            folder_path = "/" + folder_path
        return folder_path

    # Fallback: use name
    name = folder_source.get("commonAttributes", {}).get("name", "Unknown")
    return f"/{name}"


def format_document_for_display(doc_source: Dict[str, Any]) -> str:
    """
    Format a document for user-friendly display.

    Args:
        doc_source: Elasticsearch _source document

    Returns:
        Formatted string representation

    Example:
        >>> doc = {
        ...     "commonAttributes": {
        ...         "name": "W2_2024.pdf",
        ...         "documentType": "W2",
        ...         "taxYear": "2024"
        ...     },
        ...     "systemAttributes": {
        ...         "createDate": 1700000000000,
        ...         "size": 326603
        ...     },
        ...     "organizationAttributes": {
        ...         "folderPath": "root/Tax Documents"
        ...     }
        ... }
        >>> print(format_document_for_display(doc))
        📄 W2_2024.pdf
           Type: W2
           Tax Year: 2024
           Folder: /root/Tax Documents
           Size: 319.0 KB
    """
    common = doc_source.get("commonAttributes", {})
    system = doc_source.get("systemAttributes", {})
    org = doc_source.get("organizationAttributes", {})

    name = common.get("name", "Unknown")
    doc_type = common.get("documentType", "Unknown")
    tax_year = common.get("taxYear", "")
    folder_path = org.get("folderPath", "")
    size = system.get("size", 0)

    # Format size
    if size > 0:
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} bytes"
    else:
        size_str = "Unknown"

    # Build display string
    lines = [f"📄 {name}"]
    lines.append(f"   Type: {doc_type}")

    if tax_year:
        lines.append(f"   Tax Year: {tax_year}")

    if folder_path:
        if not folder_path.startswith("/"):
            folder_path = "/" + folder_path
        lines.append(f"   Folder: {folder_path}")

    lines.append(f"   Size: {size_str}")

    return "\n".join(lines)


def format_folder_for_display(folder_source: Dict[str, Any]) -> str:
    """
    Format a folder for user-friendly display.

    Args:
        folder_source: Elasticsearch _source document for a folder

    Returns:
        Formatted string representation

    Example:
        >>> folder = {
        ...     "commonAttributes": {
        ...         "name": "Tax Documents",
        ...         "description": "Tax-related documents"
        ...     },
        ...     "organizationAttributes": {
        ...         "folderPath": "root/Tax Documents"
        ...     },
        ...     "systemAttributes": {
        ...         "createDate": 1700000000000
        ...     }
        ... }
        >>> print(format_folder_for_display(folder))
        📁 Tax Documents
           Path: /root/Tax Documents
           Description: Tax-related documents
    """
    common = folder_source.get("commonAttributes", {})
    org = folder_source.get("organizationAttributes", {})

    name = common.get("name", "Unknown")
    description = common.get("description", "")
    folder_path = org.get("folderPath", "")

    lines = [f"📁 {name}"]

    if folder_path:
        if not folder_path.startswith("/"):
            folder_path = "/" + folder_path
        lines.append(f"   Path: {folder_path}")

    if description:
        lines.append(f"   Description: {description}")

    return "\n".join(lines)
