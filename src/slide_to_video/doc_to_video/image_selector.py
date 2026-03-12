"""
Image selector using LLM.

Uses GLM API to analyze and select the most important images
from documentation that demonstrate core system functionality.
"""

import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def select_important_images(
    images: List[Dict],
    doc_content: str,
    max_count: int = 30,
    api_key: Optional[str] = None,
    model: str = "glm-4-flash",
) -> List[Dict]:
    """
    Use LLM to select important images that demonstrate core functionality.

    Args:
        images: List of image dicts from extract_image_references()
        doc_content: Full document content for context
        max_count: Maximum number of images to select
        api_key: GLM API key (or use GLM_API_KEY env var)
        model: LLM model name

    Returns:
        Selected images list (subset of input), ordered by importance
    """
    if not images:
        logger.warning("No images to select from")
        return []

    # Filter out non-existent images first
    valid_images = [img for img in images if img.get("exists", False)]
    if len(valid_images) < len(images):
        logger.info(
            f"Filtered out {len(images) - len(valid_images)} non-existent images"
        )

    if not valid_images:
        logger.warning("No valid images found")
        return []

    # If we have fewer images than max_count, return all valid ones
    if len(valid_images) <= max_count:
        logger.info(
            f"Only {len(valid_images)} valid images, returning all (max_count={max_count})"
        )
        return valid_images

    # Use LLM to select important images
    try:
        selected_indices = _call_llm_for_selection(
            valid_images, doc_content, max_count, api_key, model
        )
    except Exception as e:
        logger.error(f"LLM selection failed: {e}. Returning first {max_count} images.")
        return valid_images[:max_count]

    # Build result list from selected indices
    selected_images = []
    for idx in selected_indices:
        if 0 <= idx < len(valid_images):
            selected_images.append(valid_images[idx])

    logger.info(f"Selected {len(selected_images)} images from {len(valid_images)} candidates")
    return selected_images


def _call_llm_for_selection(
    images: List[Dict],
    doc_content: str,
    max_count: int,
    api_key: Optional[str],
    model: str,
) -> List[int]:
    """
    Call LLM to select important image indices.

    Returns:
        List of selected image indices (0-based)
    """
    # Import GLM client
    from ..llm_proofread.glm_client import GLMClient

    # Build image list description for the prompt
    image_list = []
    for i, img in enumerate(images):
        desc = f"[{i}] {img.get('alt', 'No description')}"
        # Include brief context if available
        context = img.get("context", "")[:200]  # Truncate context
        if context:
            desc += f" - Context: {context[:100]}..."
        image_list.append(desc)

    prompt = f"""You are analyzing a technical documentation for a software platform.

**Task**: Select the most important images that demonstrate core system functionality.

**Selection Criteria** (in order of importance):
1. Images showing UI operations (forms, tables, buttons, interfaces)
2. Images showing configuration screens or settings
3. Images showing data flow, architecture, or process diagrams
4. Images showing example outputs or results

**Images to Skip**:
- Logos and decorative graphics
- Purely text screenshots (unless showing important UI)
- Duplicate or very similar images
- Images without meaningful content

**Document Summary** (first 3000 chars):
{doc_content[:3000]}

**Images Found** ({len(images)} total):
{chr(10).join(image_list)}

**Requirements**:
- Select at most {max_count} images
- Return indices in order of importance (most important first)

**Output Format**: Return ONLY a JSON array of selected image indices.
Example: [0, 2, 5, 7, 10]"""

    # Create GLM client and call API
    client = GLMClient(api_key=api_key, model=model, temperature=0.3)

    try:
        import requests
    except ImportError:
        raise RuntimeError("requests library required. Install with: pip install requests")

    headers = {
        "Authorization": f"Bearer {client.api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": client.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": client.temperature,
        "top_p": 0.7,
    }

    logger.info(f"Calling GLM API for image selection (model={model})...")

    response = requests.post(
        client.api_url,
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    data = response.json()

    # Extract content from response
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise ValueError(f"Invalid API response: {e}")

    # Parse JSON from response
    indices = _parse_json_indices(content, len(images))
    return indices


def _parse_json_indices(content: str, max_index: int) -> List[int]:
    """
    Parse JSON array of indices from LLM response.

    Handles various response formats:
    - Pure JSON: [0, 1, 2]
    - JSON in code block: ```json\n[0, 1, 2]\n```
    - Mixed text with JSON

    Args:
        content: Raw LLM response content
        max_index: Maximum valid index (exclusive)

    Returns:
        List of valid indices
    """
    # Try direct JSON parse first
    content = content.strip()

    # Remove code block markers if present
    if "```" in content:
        # Extract content from code blocks
        lines = content.split("\n")
        in_code_block = False
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                # Skip the ``` line itself
                continue
            if in_code_block:
                cleaned_lines.append(line)
        content = "\n".join(cleaned_lines).strip()

    # Try to find JSON array pattern
    import re
    json_match = re.search(r'\[[\d\s,]+\]', content)
    if json_match:
        content = json_match.group(0)

    try:
        indices = json.loads(content)
        if isinstance(indices, list):
            # Validate and filter indices
            valid_indices = []
            for idx in indices:
                if isinstance(idx, int) and 0 <= idx < max_index:
                    valid_indices.append(idx)
            return valid_indices
    except json.JSONDecodeError:
        pass

    # Fallback: try to extract numbers
    numbers = re.findall(r'\b(\d+)\b', content)
    indices = []
    for num_str in numbers:
        idx = int(num_str)
        if 0 <= idx < max_index and idx not in indices:
            indices.append(idx)
    return indices


def filter_images_by_keywords(
    images: List[Dict],
    keywords: List[str],
) -> List[Dict]:
    """
    Simple keyword-based image filter (no LLM).

    Useful as a fallback or pre-filter before LLM selection.

    Args:
        images: List of image dicts
        keywords: Keywords to match in alt text or context

    Returns:
        Filtered list of images
    """
    if not keywords:
        return images

    keywords_lower = [k.lower() for k in keywords]
    filtered = []

    for img in images:
        text = f"{img.get('alt', '')} {img.get('context', '')}".lower()
        if any(kw in text for kw in keywords_lower):
            filtered.append(img)

    return filtered
