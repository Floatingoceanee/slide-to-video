"""
GLM (智谱AI) LLM client implementation.
"""

import os
import logging
from typing import Optional

from .base import LLMClient
from .factory import register_provider

logger = logging.getLogger(__name__)


class GLMClient(LLMClient):
    """Client for Zhipu AI (GLM) API."""

    DEFAULT_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    DEFAULT_MODEL = "glm-4-flash"  # Free tier model, fast and cost-effective

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ):
        """
        Initialize GLM client.

        Args:
            model: Model name. Defaults to glm-4-flash.
            api_key: GLM API key. If None, reads from GLM_API_KEY env var.
            api_url: API URL. Defaults to official GLM endpoint.
            temperature: Sampling temperature (0-1). Lower = more deterministic.
            **kwargs: Additional arguments (ignored)
        """
        self._model = model or self.DEFAULT_MODEL
        self._api_key = api_key or os.environ.get("GLM_API_KEY")
        if not self._api_key:
            raise ValueError(
                "GLM API key not provided. Set GLM_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self._api_url = api_url or self.DEFAULT_API_URL
        self._temperature = temperature

    @property
    def provider(self) -> str:
        return "glm"

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
        Send a chat completion request to GLM API.

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
            "top_p": 0.7,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        logger.debug(f"Calling GLM API (model={self._model})...")

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
            # Clean up any markdown code blocks if present
            content = self._clean_response(content)
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid GLM API response format: {data}")
            raise ValueError(f"Invalid API response: {e}")

        return content

    def _clean_response(self, content: str) -> str:
        """Clean up markdown code blocks from response."""
        if "```" in content:
            lines = content.split("\n")
            in_code_block = False
            cleaned_lines = []
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or not line.strip().startswith("```"):
                    cleaned_lines.append(line)
            content = "\n".join(cleaned_lines).strip()
        return content


# Register this provider
register_provider("glm", GLMClient)
