"""
GLM API client for subtitle proofreading.

Uses Zhipu AI (GLM) API to proofread SRT subtitle files.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GLMClient:
    """Client for Zhipu AI (GLM) API."""

    DEFAULT_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    DEFAULT_MODEL = "glm-4-flash"  # Free tier model, fast and cost-effective

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: float = 0.1,
    ):
        """
        Initialize GLM client.

        Args:
            api_key: GLM API key. If None, reads from GLM_API_KEY env var.
            model: Model name. Defaults to glm-4-flash.
            api_url: API URL. Defaults to official GLM endpoint.
            temperature: Sampling temperature (0-1). Lower = more deterministic.
        """
        self.api_key = api_key or os.environ.get("GLM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GLM API key not provided. Set GLM_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.model = model or self.DEFAULT_MODEL
        self.api_url = api_url or self.DEFAULT_API_URL
        self.temperature = temperature

    def _create_proofread_prompt(self, script_text: str, srt_content: str) -> str:
        """
        Create the prompt for LLM proofreading.

        Args:
            script_text: Original script text (reference)
            srt_content: SRT content to proofread

        Returns:
            Formatted prompt string
        """
        return f"""You are a subtitle proofreading assistant.

**Task**: Correct speech-to-text errors in the SRT file using the original script as reference.

**Rules**:
1. Keep ALL timestamps EXACTLY as they are
2. Keep the segment structure (do not merge or split segments)
3. Only fix words that are clearly recognition errors
4. Match the style and vocabulary of the original script
5. Preserve punctuation style from the SRT (not the script)
6. Return ONLY the corrected SRT content, nothing else

**Original Script** (reference for correct wording):
{script_text}

**SRT to Proofread**:
{srt_content}

Return the corrected SRT:"""

    def proofread_srt(
        self,
        script_text: str,
        srt_content: str,
        timeout: int = 120,
    ) -> str:
        """
        Proofread SRT content using GLM API.

        Args:
            script_text: Original script text as reference
            srt_content: SRT content to proofread
            timeout: Request timeout in seconds

        Returns:
            Proofread SRT content

        Raises:
            requests.RequestException: API call failed
            ValueError: Invalid response from API
        """
        try:
            import requests
        except ImportError:
            raise RuntimeError(
                "requests library not installed. Install with: pip install requests"
            )

        prompt = self._create_proofread_prompt(script_text, srt_content)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "top_p": 0.7,
        }

        logger.info(f"Calling GLM API (model={self.model})...")

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"GLM API request failed: {e}")
            raise

        data = response.json()

        # Extract the content from GLM response
        try:
            content = data["choices"][0]["message"]["content"]
            # Clean up any markdown code blocks if present
            if "```" in content:
                # Extract content from code blocks
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
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid GLM API response format: {data}")
            raise ValueError(f"Invalid API response: {e}")

        logger.info("GLM API proofreading completed")
        return content


def get_glm_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> GLMClient:
    """
    Factory function to create GLM client with config.

    Args:
        api_key: API key (or from GLM_API_KEY env var)
        model: Model name
        temperature: Temperature setting

    Returns:
        Configured GLMClient instance
    """
    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    if model:
        kwargs["model"] = model
    if temperature is not None:
        kwargs["temperature"] = temperature

    return GLMClient(**kwargs)
