"""
Checkpointing utilities for LangGraph state persistence.

Provides checkpoint implementations for different backends:
- MemorySaver: In-memory (POC/testing)
- PostgresSaver: PostgreSQL (production)
- RedisSaver: Redis (production, fast access)

Usage:
    from search_agent.utils.checkpointing import get_checkpointer

    # POC/testing
    checkpointer = get_checkpointer("memory")

    # Production with PostgreSQL
    checkpointer = get_checkpointer("postgres", connection_string="postgresql://...")

    # Production with Redis
    checkpointer = get_checkpointer("redis", redis_url="redis://localhost:6379")
"""

import logging
from typing import Literal, Optional
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


def get_checkpointer(
    backend: Literal["memory", "postgres", "redis"] = "memory",
    **kwargs
) -> MemorySaver:
    """
    Get a checkpointer instance for the specified backend.

    Args:
        backend: Checkpointer backend ("memory", "postgres", "redis")
        **kwargs: Backend-specific configuration
            For postgres: connection_string (str)
            For redis: redis_url (str), redis_client (Redis)

    Returns:
        Checkpointer instance

    Raises:
        ValueError: If backend is not supported or configuration is invalid
        ImportError: If required backend library is not installed

    Examples:
        >>> # In-memory checkpointer (POC)
        >>> checkpointer = get_checkpointer("memory")

        >>> # PostgreSQL checkpointer (production)
        >>> checkpointer = get_checkpointer(
        ...     "postgres",
        ...     connection_string="postgresql://user:pass@localhost/db"
        ... )

        >>> # Redis checkpointer (production)
        >>> checkpointer = get_checkpointer(
        ...     "redis",
        ...     redis_url="redis://localhost:6379"
        ... )
    """
    if backend == "memory":
        logger.info("Using MemorySaver checkpointer (in-memory)")
        return MemorySaver()

    elif backend == "postgres":
        return _create_postgres_checkpointer(**kwargs)

    elif backend == "redis":
        return _create_redis_checkpointer(**kwargs)

    else:
        raise ValueError(
            f"Unsupported checkpointer backend: {backend}. "
            f"Must be one of: memory, postgres, redis"
        )


def _create_postgres_checkpointer(connection_string: Optional[str] = None, **kwargs) -> MemorySaver:
    """
    Create PostgreSQL checkpointer.

    Args:
        connection_string: PostgreSQL connection string
        **kwargs: Additional PostgreSQL configuration

    Returns:
        PostgresSaver instance

    Raises:
        ImportError: If langgraph-checkpoint-postgres is not installed
        ValueError: If connection_string is not provided
    """
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
    except ImportError as e:
        raise ImportError(
            "PostgreSQL checkpointer requires 'langgraph-checkpoint-postgres'. "
            "Install it with: pip install langgraph-checkpoint-postgres"
        ) from e

    if not connection_string:
        raise ValueError(
            "PostgreSQL checkpointer requires 'connection_string' parameter. "
            "Example: postgresql://user:password@localhost:5432/dbname"
        )

    logger.info(f"Creating PostgreSQL checkpointer: {connection_string.split('@')[1] if '@' in connection_string else 'localhost'}")

    try:
        checkpointer = PostgresSaver(connection_string, **kwargs)
        logger.info("✓ PostgreSQL checkpointer created successfully")
        return checkpointer
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL checkpointer: {e}")
        raise


def _create_redis_checkpointer(
    redis_url: Optional[str] = None,
    redis_client = None,
    **kwargs
) -> MemorySaver:
    """
    Create Redis checkpointer.

    Args:
        redis_url: Redis connection URL (e.g., "redis://localhost:6379")
        redis_client: Existing Redis client instance (alternative to redis_url)
        **kwargs: Additional Redis configuration

    Returns:
        RedisSaver instance

    Raises:
        ImportError: If langgraph-checkpoint-redis is not installed
        ValueError: If neither redis_url nor redis_client is provided
    """
    try:
        from langgraph.checkpoint.redis import RedisSaver
    except ImportError as e:
        raise ImportError(
            "Redis checkpointer requires 'langgraph-checkpoint-redis'. "
            "Install it with: pip install langgraph-checkpoint-redis"
        ) from e

    if not redis_url and not redis_client:
        raise ValueError(
            "Redis checkpointer requires either 'redis_url' or 'redis_client' parameter. "
            "Example redis_url: redis://localhost:6379"
        )

    logger.info(f"Creating Redis checkpointer: {redis_url or 'custom client'}")

    try:
        if redis_client:
            checkpointer = RedisSaver(redis_client, **kwargs)
        else:
            import redis
            client = redis.from_url(redis_url)
            checkpointer = RedisSaver(client, **kwargs)

        logger.info("✓ Redis checkpointer created successfully")
        return checkpointer
    except Exception as e:
        logger.error(f"Failed to create Redis checkpointer: {e}")
        raise


def get_checkpointer_from_config(config: dict) -> MemorySaver:
    """
    Create checkpointer from configuration dictionary.

    Args:
        config: Configuration dict with keys:
            - backend: "memory" | "postgres" | "redis"
            - connection_string: (for postgres)
            - redis_url: (for redis)
            - redis_client: (for redis, alternative to redis_url)

    Returns:
        Checkpointer instance

    Examples:
        >>> config = {
        ...     "backend": "postgres",
        ...     "connection_string": "postgresql://localhost/db"
        ... }
        >>> checkpointer = get_checkpointer_from_config(config)

        >>> config = {
        ...     "backend": "redis",
        ...     "redis_url": "redis://localhost:6379"
        ... }
        >>> checkpointer = get_checkpointer_from_config(config)
    """
    backend = config.get("backend", "memory")

    # Extract backend-specific config
    backend_config = {
        k: v for k, v in config.items()
        if k not in ["backend"]
    }

    return get_checkpointer(backend, **backend_config)


def validate_checkpointer_config(config: dict) -> tuple[bool, Optional[str]]:
    """
    Validate checkpointer configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (is_valid, error_message)
            is_valid: True if config is valid
            error_message: Error description if invalid, None if valid

    Examples:
        >>> config = {"backend": "memory"}
        >>> is_valid, error = validate_checkpointer_config(config)
        >>> assert is_valid

        >>> config = {"backend": "postgres"}  # Missing connection_string
        >>> is_valid, error = validate_checkpointer_config(config)
        >>> assert not is_valid
    """
    backend = config.get("backend")

    # Check backend is specified
    if not backend:
        return False, "Missing 'backend' in configuration"

    # Check backend is valid
    valid_backends = ["memory", "postgres", "redis"]
    if backend not in valid_backends:
        return False, f"Invalid backend '{backend}'. Must be one of: {', '.join(valid_backends)}"

    # Backend-specific validation
    if backend == "postgres":
        if "connection_string" not in config:
            return False, "PostgreSQL backend requires 'connection_string'"

    elif backend == "redis":
        if "redis_url" not in config and "redis_client" not in config:
            return False, "Redis backend requires 'redis_url' or 'redis_client'"

    return True, None


if __name__ == "__main__":
    # Test checkpointer creation
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 70)
    print("Checkpointing Utilities - Test")
    print("=" * 70)

    # Test 1: Memory checkpointer
    print("\n1. Creating memory checkpointer...")
    memory_checkpointer = get_checkpointer("memory")
    print(f"   ✓ Created: {type(memory_checkpointer).__name__}")

    # Test 2: Configuration validation
    print("\n2. Testing configuration validation...")

    test_configs = [
        {"backend": "memory"},
        {"backend": "postgres", "connection_string": "postgresql://localhost/test"},
        {"backend": "redis", "redis_url": "redis://localhost:6379"},
        {"backend": "invalid"},
        {"backend": "postgres"},  # Missing connection_string
    ]

    for config in test_configs:
        is_valid, error = validate_checkpointer_config(config)
        status = "✓" if is_valid else "✗"
        print(f"   {status} {config}")
        if error:
            print(f"      Error: {error}")

    # Test 3: PostgreSQL checkpointer (will fail if library not installed)
    print("\n3. Testing PostgreSQL checkpointer creation...")
    try:
        pg_config = {
            "backend": "postgres",
            "connection_string": "postgresql://localhost/test"
        }
        # This will fail if library not installed - that's expected
        pg_checkpointer = get_checkpointer_from_config(pg_config)
        print(f"   ✓ Created: {type(pg_checkpointer).__name__}")
    except ImportError as e:
        print(f"   ⚠ Skipped (library not installed): {e}")
    except Exception as e:
        print(f"   ⚠ Skipped (connection failed): {e}")

    # Test 4: Redis checkpointer (will fail if library not installed)
    print("\n4. Testing Redis checkpointer creation...")
    try:
        redis_config = {
            "backend": "redis",
            "redis_url": "redis://localhost:6379"
        }
        redis_checkpointer = get_checkpointer_from_config(redis_config)
        print(f"   ✓ Created: {type(redis_checkpointer).__name__}")
    except ImportError as e:
        print(f"   ⚠ Skipped (library not installed): {e}")
    except Exception as e:
        print(f"   ⚠ Skipped (connection failed): {e}")

    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)
    print("""
Notes:
- MemorySaver is always available (built-in)
- PostgresSaver requires: pip install langgraph-checkpoint-postgres
- RedisSaver requires: pip install langgraph-checkpoint-redis
- Production deployments should use persistent backends (Postgres/Redis)
""")
