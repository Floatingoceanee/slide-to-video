"""
LLM-based subtitle proofreading module.

Provides integration with LLM APIs (GLM, OpenAI, etc.)
for intelligent subtitle error correction.
"""

from .glm_client import GLMClient, get_glm_client

__all__ = ["GLMClient", "get_glm_client"]
