"""
Qwen (通义千问) LLM client implementation.
"""

import os
import logging
from typing import Optional

from .base import LLMClient
from .factory import register_provider

logger = logging.getLogger(__name__)


class QwenClient(LLMClient):
    """Client for Alibaba Qwen (通义千问) API via DashScope."""

    DEFAULT_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    DEFAULT_MODEL = "qwen-turbo"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ):
        """
        Initialize Qwen client.

        Args:
            model: Model name. Defaults to qwen-turbo.
            api_key: DashScope API key. If None, reads from DASHSCOPE_API_KEY env var.
            api_url: API URL. Defaults to DashScope OpenAI-compatible endpoint.
            temperature: Sampling temperature (0-1). Lower = more deterministic.
            **kwargs: Additional arguments (ignored)
        """
        self._model = model or self.DEFAULT_MODEL
        self._api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self._api_key:
            raise ValueError(
                "DashScope API key not provided. Set DASHSCOPE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self._api_url = api_url or self.DEFAULT_API_URL
        self._temperature = temperature

    @property
    def provider(self) -> str:
        return "qwen"

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
        Send a chat completion request to Qwen API.

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
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        logger.debug(f"Calling Qwen API (model={self._model})...")

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
            logger.error(f"Invalid Qwen API response format: {data}")
            raise ValueError(f"Invalid API response: {e}")


# Register this provider
register_provider("qwen", QwenClient)
