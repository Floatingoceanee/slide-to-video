"""
GLM client exports.

Re-exports GLMClient and get_glm_client for backward compatibility.
"""

from .glm_client import GLMClient, get_glm_client


__all__ = ["GLMClient", "get_glm_client"]
