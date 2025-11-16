"""
LLM service wrapper for Anthropic Claude API.

Provides a standardized interface for LLM interactions with retry logic,
error handling, and JSON response parsing.

Example:
    >>> from search_agent.services import LLMService
    >>> llm = LLMService()
    >>> response = llm.call_with_retry("What is 2+2?")
    >>> print(response)
    '4'
"""

import time
import json
from typing import Optional, Dict, Any

from anthropic import Anthropic, APIError, AuthenticationError, APIConnectionError

from search_agent.config import settings


class LLMService:
    """
    Service for interacting with Anthropic Claude API.

    Handles API calls with retry logic, timeout management, and
    JSON response parsing.

    Attributes:
        client: Anthropic API client
        model: Claude model to use
        max_retries: Maximum retry attempts
        timeout: API call timeout in seconds

    Example:
        >>> llm = LLMService()
        >>> response = llm.call_with_retry("Explain LangGraph in one sentence")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = settings.LLM_MODEL,
        max_retries: int = settings.MAX_RETRIES,
        timeout: int = settings.LLM_TIMEOUT_SECONDS
    ):
        """
        Initialize LLM service.

        Args:
            api_key: Anthropic API key (defaults to settings)
            model: Claude model to use
            max_retries: Maximum retry attempts for API calls
            timeout: Timeout for API calls in seconds

        Raises:
            ValueError: If API key is not provided
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Set it as an environment variable "
                "or pass it to LLMService constructor."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_delays = settings.RETRY_BACKOFF_DELAYS

    def call(
        self,
        prompt: str,
        max_tokens: int = settings.LLM_MAX_TOKENS,
        temperature: float = settings.LLM_TEMPERATURE,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Make a single API call to Claude (no retry).

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            system_prompt: Optional system prompt

        Returns:
            Response text from Claude

        Raises:
            APIError: If API call fails
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            "timeout": self.timeout
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text.strip()

    def call_with_retry(
        self,
        prompt: str,
        max_tokens: int = settings.LLM_MAX_TOKENS,
        temperature: float = settings.LLM_TEMPERATURE,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Call Claude API with exponential backoff retry logic.

        Retries on network errors and API failures (not auth errors).

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Response text from Claude

        Raises:
            AuthenticationError: If API key is invalid (no retry)
            Exception: If all retries fail

        Example:
            >>> llm = LLMService()
            >>> response = llm.call_with_retry("What is LangGraph?")
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return self.call(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt
                )

            except AuthenticationError as e:
                # Don't retry on auth errors
                raise Exception(f"Authentication failed: {str(e)}")

            except (APIConnectionError, APIError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Wait before retrying
                    delay = self.retry_delays[attempt] if attempt < len(self.retry_delays) else self.retry_delays[-1]
                    time.sleep(delay)
                    continue
                else:
                    # Max retries exceeded
                    raise Exception(
                        f"API call failed after {self.max_retries} attempts: {str(last_error)}"
                    )

        # Should not reach here, but just in case
        raise Exception(f"API call failed: {str(last_error)}")

    def call_with_json_response(
        self,
        prompt: str,
        max_tokens: int = settings.LLM_MAX_TOKENS,
        temperature: float = settings.LLM_TEMPERATURE,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Claude API and parse response as JSON.

        Handles JSON extraction from markdown code blocks.

        Args:
            prompt: User prompt (should request JSON response)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Parsed JSON response as dictionary

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            Exception: If API call fails

        Example:
            >>> llm = LLMService()
            >>> result = llm.call_with_json_response(
            ...     "Return JSON: {\"answer\": 42}"
            ... )
            >>> result["answer"]
            42
        """
        response_text = self.call_with_retry(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt
        )

        # Handle case where response is wrapped in ```json blocks
        response_text = response_text.strip()

        if response_text.startswith("```json"):
            # Extract JSON from markdown code block
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            # Extract from generic code block
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Failed to parse LLM response as JSON. Response: {response_text[:200]}...",
                e.doc,
                e.pos
            )

    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimation of token count for text.

        Uses simple heuristic: ~4 characters per token.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count

        Example:
            >>> llm = LLMService()
            >>> llm.estimate_tokens("Hello world")
            3
        """
        # Simple heuristic: ~4 characters per token
        return len(text) // 4


# Singleton instance for convenience
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Get singleton LLM service instance.

    Creates instance on first call, returns cached instance on subsequent calls.

    Returns:
        LLM service instance

    Example:
        >>> llm = get_llm_service()
        >>> response = llm.call_with_retry("Hello")
    """
    global _llm_service_instance

    if _llm_service_instance is None:
        _llm_service_instance = LLMService()

    return _llm_service_instance
