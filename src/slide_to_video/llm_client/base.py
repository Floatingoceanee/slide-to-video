"""
Abstract base class for LLM clients.
"""

from abc import ABC, abstractmethod
from typing import Optional


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def chat(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request.

        Args:
            prompt: The user prompt/message
            temperature: Sampling temperature (0-1). Lower = more deterministic.
            max_tokens: Maximum tokens to generate (optional)

        Returns:
            The generated response text
        """
        pass

    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name (e.g., 'glm', 'claude')."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Return the model name."""
        pass
