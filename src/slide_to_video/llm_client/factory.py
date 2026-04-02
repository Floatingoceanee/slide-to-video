"""
Factory functions to create LLM clients.
"""

from typing import Dict, Any, Optional
import logging

from .base import LLMClient

logger = logging.getLogger(__name__)

# Registry of available providers
_PROVIDER_REGISTRY: Dict[str, type] = {}


def register_provider(name: str, client_class: type) -> None:
    """
    Register an LLM provider.

    Args:
        name: Provider name (e.g., 'glm', 'claude')
        client_class: The client class to register
    """
    _PROVIDER_REGISTRY[name.lower()] = client_class
    logger.debug(f"Registered LLM provider: {name}")


def get_available_providers() -> list:
    """Return list of available provider names."""
    return list(_PROVIDER_REGISTRY.keys())


def create_llm_client(
    provider: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs,
) -> LLMClient:
    """
    Create an LLM client by provider name.

    Args:
        provider: Provider name (glm, claude, qwen, kimi, ollama, openai-compatible)
        model: Model name
        api_key: API key (optional, uses env var if not set)
        api_url: API URL (optional, uses default if not set)
        temperature: Default temperature for requests
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured LLMClient instance

    Raises:
        ValueError: If provider is not supported
    """
    provider_lower = provider.lower()

    if provider_lower not in _PROVIDER_REGISTRY:
        available = ", ".join(get_available_providers())
        raise ValueError(
            f"Unknown LLM provider: {provider}. Available providers: {available}"
        )

    client_class = _PROVIDER_REGISTRY[provider_lower]

    return client_class(
        model=model,
        api_key=api_key,
        api_url=api_url,
        temperature=temperature,
        **kwargs,
    )


def get_llm_client_from_config(config: Dict[str, Any]) -> LLMClient:
    """
    Create an LLM client from a config dictionary.

    Expected config format:
    ```yaml
    llm:
      provider: glm
      model: "glm-4-flash"
      api_key: "xxx"         # optional
      api_url: null          # optional
      temperature: 0.7
    ```

    Args:
        config: Config dictionary with 'llm' key

    Returns:
        Configured LLMClient instance
    """
    llm_config = config.get("llm", {})

    if not llm_config:
        raise ValueError("No LLM configuration found in config")

    provider = llm_config.get("provider")
    if not provider:
        raise ValueError("LLM provider not specified in config")

    return create_llm_client(
        provider=provider,
        model=llm_config.get("model"),
        api_key=llm_config.get("api_key"),
        api_url=llm_config.get("api_url"),
        temperature=llm_config.get("temperature", 0.7),
    )


def auto_discover_providers():
    """Auto-discover and register all available providers."""
    import importlib
    import os

    # List of provider modules to try importing
    provider_modules = [
        "glm_client",
        "claude_client",
        "qwen_client",
        "kimi_client",
        "ollama_client",
        "openai_compatible",
    ]

    current_dir = os.path.dirname(__file__)

    for module_name in provider_modules:
        module_path = os.path.join(current_dir, f"{module_name}.py")
        if os.path.exists(module_path):
            try:
                import_path = f".{module_name}"
                importlib.import_module(import_path, package="slide_to_video.llm_client")
                logger.debug(f"Auto-discovered LLM provider module: {module_name}")
            except ImportError as e:
                logger.debug(f"Could not import {module_name}: {e}")
