"""
Claude (Anthropic) LLM client implementation.
"""

import os
import logging
from typing import Optional

from .base import LLMClient
from .factory import register_provider

logger = logging.getLogger(__name__)


class ClaudeClient(LLMClient):
    """Client for Anthropic Claude API."""

    DEFAULT_API_URL = "https://api.anthropic.com/v1/messages"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ):
        """
        Initialize Claude client.

        Args:
            model: Model name. Defaults to claude-3-5-sonnet-20241022.
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
            api_url: API URL. Defaults to official Anthropic endpoint.
            temperature: Sampling temperature (0-1). Lower = more deterministic.
            **kwargs: Additional arguments (ignored)
        """
        self._model = model or self.DEFAULT_MODEL
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self._api_url = api_url or self.DEFAULT_API_URL
        self._temperature = temperature

    @property
    def provider(self) -> str:
        return "claude"

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
        Send a chat completion request to Claude API.

        Args:
            prompt: The user prompt/message
            temperature: Sampling temperature (overrides default)
            max_tokens: Maximum tokens to generate (defaults to 4096)

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
        tokens = max_tokens or 4096

        headers = {
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self._model,
            "max_tokens": tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        if temp is not None:
            payload["temperature"] = temp

        logger.debug(f"Calling Claude API (model={self._model})...")

        response = requests.post(
            self._api_url,
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()

        data = response.json()

        try:
            # Claude returns content as a list of content blocks
            content_blocks = data["content"]
            text_content = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    text_content += block.get("text", "")
            return text_content
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid Claude API response format: {data}")
            raise ValueError(f"Invalid API response: {e}")


# Register this provider
register_provider("claude", ClaudeClient)
