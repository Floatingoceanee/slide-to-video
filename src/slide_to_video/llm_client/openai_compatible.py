"""
OpenAI-compatible generic LLM client implementation.

This client can be used with any API that follows the OpenAI chat completions format.
"""

import os
import logging
from typing import Optional

from .base import LLMClient
from .factory import register_provider

logger = logging.getLogger(__name__)


class OpenAICompatibleClient(LLMClient):
    """Client for OpenAI-compatible APIs."""

    # No default URL - must be provided
    DEFAULT_MODEL = "gpt-4o"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ):
        """
        Initialize OpenAI-compatible client.

        Args:
            model: Model name. Defaults to gpt-4o.
            api_key: API key. If None, reads from OPENAI_API_KEY env var.
            api_url: API URL (required for non-OpenAI endpoints).
            temperature: Sampling temperature (0-1). Lower = more deterministic.
            **kwargs: Additional arguments (ignored)
        """
        self._model = model or self.DEFAULT_MODEL
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")

        # API URL is required for non-standard endpoints
        self._api_url = api_url or os.environ.get("OPENAI_API_URL")
        if not self._api_url:
            # Default to OpenAI's API
            self._api_url = "https://api.openai.com/v1/chat/completions"

        self._temperature = temperature

    @property
    def provider(self) -> str:
        return "openai-compatible"

    @property
    def model(self) -> str:
        return self._model

    def chat(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request to OpenAI-compatible API.

        Args:
            prompt: The user prompt/message
            temperature: Sampling temperature (overrides default)
            max_tokens: Maximum tokens to generate (optional)

        Returns:
            The generated response text
        """
        try:
            import requests
        except ImportError:
            raise RuntimeError(
                "requests library not installed. Install with: pip install requests"
            )

        temp = temperature if temperature is not None else self._temperature

        headers = {
            "Content-Type": "application/json",
        }

        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        logger.debug(f"Calling OpenAI-compatible API (model={self._model})...")

        response = requests.post(
            self._api_url,
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid API response format: {data}")
            raise ValueError(f"Invalid API response: {e}")


# Register this provider with multiple names for flexibility
register_provider("openai-compatible", OpenAICompatibleClient)
register_provider("openai", OpenAICompatibleClient)
