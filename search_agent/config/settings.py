"""
Configuration settings for the search agent.

Uses pydantic-settings for environment variable management with validation.
Configuration can be overridden via environment variables or .env file.

Example:
    >>> from search_agent.config import settings
    >>> print(settings.ANTHROPIC_API_KEY)
    >>> print(settings.MAX_RETRIES)
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden by setting environment variables with the same name.
    For example, set ANTHROPIC_API_KEY environment variable to override the API key.
    """

    # ===== LLM Configuration =====

    ANTHROPIC_API_KEY: str = Field(
        default="",
        description="Anthropic API key for Claude access (required)"
    )

    LLM_MODEL: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Claude model to use for query generation"
    )

    LLM_TEMPERATURE: float = Field(
        default=0.0,
        description="Temperature for LLM calls (0.0 = deterministic)"
    )

    LLM_MAX_TOKENS: int = Field(
        default=4096,
        description="Maximum tokens for LLM responses"
    )

    LLM_TIMEOUT_SECONDS: int = Field(
        default=60,
        description="Timeout for LLM API calls in seconds"
    )

    # ===== Elasticsearch Configuration =====

    ELASTICSEARCH_URL: str = Field(
        default="http://localhost:9200",
        description="Elasticsearch service URL (used in Phase 3+)"
    )

    ELASTICSEARCH_INDEX: str = Field(
        default="entities-v4",
        description="Elasticsearch index name"
    )

    ELASTICSEARCH_TIMEOUT: int = Field(
        default=10,
        description="Timeout for ES queries in seconds"
    )

    # ===== Retry Configuration =====

    MAX_RETRIES: int = Field(
        default=3,
        description="Maximum retry attempts for validation errors"
    )

    MAX_EXECUTION_RETRIES: int = Field(
        default=2,
        description="Maximum retry attempts for execution errors"
    )

    RETRY_BACKOFF_DELAYS: list[int] = Field(
        default=[2, 4, 8],
        description="Exponential backoff delays in seconds"
    )

    # ===== Query Execution Configuration =====

    DEFAULT_RESULT_SIZE: int = Field(
        default=100,
        description="Default number of results to return from ES queries"
    )

    MAX_STEPS: int = Field(
        default=3,
        description="Maximum number of steps allowed in a multi-step query"
    )

    # ===== Resource Paths =====

    PROMPTS_DIR: Path = Field(
        default=Path(__file__).parent.parent.resolve() / "prompts",
        description="Directory containing prompt templates"
    )

    # Path to existing ES query tool resources
    ES_TOOL_RESOURCES_DIR: Path = Field(
        default=Path(__file__).parent.parent.parent.resolve() / "ai_tools" / "elasticsearch" / "resources",
        description="Directory containing ES mapping and examples"
    )

    # ===== Logging Configuration =====

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    ENABLE_DEBUG_LOGGING: bool = Field(
        default=False,
        description="Enable detailed debug logging"
    )

    # ===== LangGraph Configuration =====

    ENABLE_CHECKPOINTING: bool = Field(
        default=True,
        description="Enable LangGraph state checkpointing"
    )

    CHECKPOINTER_TYPE: str = Field(
        default="memory",
        description="Checkpointer type: 'memory', 'postgres', or 'redis' (Phase 5+)"
    )

    POSTGRES_CONNECTION_STRING: str = Field(
        default="",
        description="PostgreSQL connection string for checkpointing (optional)"
    )

    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis URL for checkpointing (optional)"
    )

    # ===== Mock Service Configuration (Phase 1) =====

    USE_MOCK_ELASTICSEARCH: bool = Field(
        default=True,
        description="Use mock Elasticsearch service (Phase 1)"
    )

    MOCK_ES_DELAY_MS: int = Field(
        default=100,
        description="Simulated delay for mock ES calls in milliseconds"
    )

    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def validate_required_settings(self) -> None:
        """
        Validate that required settings are present.

        Raises:
            ValueError: If required settings are missing
        """
        if not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Set it as an environment variable "
                "or in a .env file."
            )

    @property
    def es_mapping_path(self) -> Path:
        """Path to Elasticsearch mapping file."""
        return self.ES_TOOL_RESOURCES_DIR / "Mapping.json"

    @property
    def es_field_descriptions_path(self) -> Path:
        """Path to Elasticsearch field descriptions file."""
        return self.ES_TOOL_RESOURCES_DIR / "FieldDescriptions.json"

    @property
    def es_few_shot_examples_path(self) -> Path:
        """Path to Elasticsearch few-shot examples file."""
        return self.ES_TOOL_RESOURCES_DIR / "FewShotExamples.json"

    @property
    def es_full_document_path(self) -> Path:
        """Path to Elasticsearch full document example file."""
        return self.ES_TOOL_RESOURCES_DIR / "FullDocument.json"

    @property
    def es_prompt_template_path(self) -> Path:
        """Path to Elasticsearch query generation prompt template."""
        return self.ES_TOOL_RESOURCES_DIR / "prompt_template.txt"


# Create singleton settings instance
settings = Settings()


# Convenience function for validation
def validate_settings() -> None:
    """
    Validate all required settings.

    Call this at application startup to ensure configuration is valid.

    Raises:
        ValueError: If required settings are missing or invalid
    """
    settings.validate_required_settings()

    # Validate that resource paths exist
    if not settings.ES_TOOL_RESOURCES_DIR.exists():
        raise ValueError(
            f"ES tool resources directory not found: {settings.ES_TOOL_RESOURCES_DIR}. "
            f"Make sure ai_tools/elasticsearch/resources exists."
        )

    required_files = [
        settings.es_mapping_path,
        settings.es_field_descriptions_path,
        settings.es_few_shot_examples_path,
        settings.es_full_document_path,
        settings.es_prompt_template_path,
    ]

    for file_path in required_files:
        if not file_path.exists():
            raise ValueError(f"Required resource file not found: {file_path}")


if __name__ == "__main__":
    # Test configuration
    print("Search Agent Configuration")
    print("=" * 50)
    print(f"LLM Model: {settings.LLM_MODEL}")
    print(f"Elasticsearch URL: {settings.ELASTICSEARCH_URL}")
    print(f"Max Retries: {settings.MAX_RETRIES}")
    print(f"Use Mock ES: {settings.USE_MOCK_ELASTICSEARCH}")
    print(f"ES Resources Dir: {settings.ES_TOOL_RESOURCES_DIR}")
    print()

    try:
        validate_settings()
        print("✓ Configuration is valid")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
