"""
Unified LLM client module.

Provides a unified interface for multiple LLM providers:
- GLM (智谱AI)
- Claude (Anthropic)
- Qwen (通义千问)
- Kimi (月之暗面)
- Ollama (本地模型)
- OpenAI-Compatible (通用 API)
"""

from .base import LLMClient
from .factory import create_llm_client, get_llm_client_from_config, auto_discover_providers

# Auto-discover providers after factory is fully loaded
auto_discover_providers()

__all__ = [
    "LLMClient",
    "create_llm_client",
    "get_llm_client_from_config",
]
