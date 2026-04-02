"""
Ollama (local models) LLM client implementation.
"""

import os
import logging
from typing import Optional

from .base import LLMClient
from .factory import register_provider

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    """Client for Ollama local model API."""

    DEFAULT_API_URL = "http://localhost:11434/api/chat"
    DEFAULT_MODEL = "llama3.2"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ):
        """
        Initialize Ollama client.

        Args:
            model: Model name. Defaults to llama3.2.
            api_key: API key (not used for Ollama, kept for interface consistency).
            api_url: API URL. Defaults to localhost:11434. Can also set OLLAMA_HOST env var.
            temperature: Sampling temperature (0-1). Lower = more deterministic.
            **kwargs: Additional arguments (ignored)
        """
        self._model = model or self.DEFAULT_MODEL

        # Ollama URL can be set via env var or parameter
        self._api_url = api_url or os.environ.get("OLLAMA_HOST")
        if self._api_url:
            # Ensure we use the /api/chat endpoint
            if not self._api_url.endswith("/api/chat"):
                self._api_url = self._api_url.rstrip("/") + "/api/chat"
        else:
            self._api_url = self.DEFAULT_API_URL

        self._temperature = temperature
        # api_key is ignored for Ollama but stored for interface consistency
        self._api_key = api_key

    @property
    def provider(self) -> str:
        return "ollama"

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
        Send a chat completion request to Ollama API.

        Args:
            prompt: The user prompt/message
            temperature: Sampling temperature (overrides default)
            max_tokens: Maximum tokens to generate (maps to num_predict in Ollama)

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

        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": temp,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        logger.debug(f"Calling Ollama API (model={self._model})...")

        try:
            response = requests.post(
                self._api_url,
                headers=headers,
                json=payload,
                timeout=300,  # Local models may take longer
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Could not connect to Ollama at {self._api_url}. "
                "Make sure Ollama is running (e.g., run 'ollama serve')."
            )

        data = response.json()

        try:
            content = data["message"]["content"]
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid Ollama API response format: {data}")
            raise ValueError(f"Invalid API response: {e}")


# Register this provider
register_provider("ollama", OllamaClient)
