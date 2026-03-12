"""
Script generator using LLM.

Generates narration scripts for slide images using GLM API.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


from typing import Callable

def generate_narration_script(
    images: List[Dict],
    doc_content: str,
    api_key: Optional[str] = None,
    model: str = "glm-4-flash",
    language: str = "zh-cn",
    last_slide_delay: float = 4.0,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> str:
    """
    Generate narration script for a list of images.

    Args:
        images: List of selected image dicts with alt text and context
        doc_content: Full document content for reference
        api_key: GLM API key (or use GLM_API_KEY env var)
        model: LLM model name
        language: Output language (zh-cn, en, etc.)
        last_slide_delay: Delay in seconds to add after the last slide
        progress_callback: Optional callback function(slide_num, total, message)

    Returns:
        Script text in slide-to-video format (NEWSLIDE separated)
    """
    if not images:
        logger.warning("No images provided for script generation")
        return ""

    # Generate narration for each image
    narrations = []

    for i, img in enumerate(images):
        slide_num = i + 1
        total = len(images)
        msg = f"Generating narration for slide {slide_num}/{total}..."

        logger.info(msg)
        if progress_callback:
            progress_callback(slide_num, total, msg)

        narration = _generate_single_narration(
            image=img,
            doc_content=doc_content,
            slide_num=slide_num,
            total_slides=total,
            api_key=api_key,
            model=model,
            language=language,
        )
        narrations.append(narration)

    # Build the script in slide-to-video format
    script_lines = []

    for i, narration in enumerate(narrations):
        if i > 0:
            script_lines.append("")  # Empty line before NEWSLIDE

        script_lines.append("NEWSLIDE")
        script_lines.append(narration)

    # Add delay for the last slide
    if last_slide_delay > 0 and narrations:
        script_lines.append("")
        script_lines.append("===")
        script_lines.append(f"#delay: {last_slide_delay}")

    script_content = "\n".join(script_lines)
    logger.info(f"Generated script with {len(narrations)} slides")

    return script_content


def _generate_single_narration(
    image: Dict,
    doc_content: str,
    slide_num: int,
    total_slides: int,
    api_key: Optional[str],
    model: str,
    language: str,
) -> str:
    """
    Generate narration for a single slide image.

    Args:
        image: Image dict with alt, context, etc.
        doc_content: Full document content
        slide_num: Current slide number (1-based)
        total_slides: Total number of slides
        api_key: GLM API key
        model: LLM model name
        language: Output language

    Returns:
        Narration text for this slide
    """
    from ..llm_proofread.glm_client import GLMClient

    # Build context for this image
    image_description = image.get("alt", "")
    image_context = image.get("context", "")

    # Language-specific instructions
    if language.startswith("zh"):
        lang_instruction = "用中文撰写解说词。"
        style_note = "语言要专业但通俗易懂，适合企业培训视频。"
    else:
        lang_instruction = "Write the narration in English."
        style_note = "Use clear, professional language suitable for business training videos."

    prompt = f"""You are writing narration scripts for a corporate training video.

**Task**: Write clear, professional narration for a single slide image.

**Guidelines**:
1. The narration should take about 30-60 seconds to speak aloud
2. Explain what the screenshot/image shows in practical terms
3. Highlight key features and how users can interact with them
4. Focus on actionable information (what users can do, how to use features)
5. Avoid overly technical jargon unless it's standard terminology
6. Do not say phrases like "as you can see" or "this image shows"
7. {style_note}

**Document Context** (for reference):
{doc_content[:2500]}

**Current Slide**: {slide_num} of {total_slides}

**Image Description**: {image_description}

**Surrounding Context from Document**:
{image_context}

**Requirements**:
- {lang_instruction}
- Write narration ONLY for this single slide
- Do not include any headers, labels, or meta-commentary
- Start directly with the narration content

**Output**: The narration text for this slide."""

    # Create GLM client and call API
    client = GLMClient(api_key=api_key, model=model, temperature=0.7)

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
        "top_p": 0.8,
    }

    try:
        response = requests.post(
            client.api_url,
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Clean up the response
        content = content.strip()

        # Remove any markdown formatting
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]

        return content

    except requests.exceptions.Timeout:
        error_msg = f"Timeout (60s) for slide {slide_num}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        return f"[解说词生成超时 - {image.get('alt', 'Slide ' + str(slide_num))}]"
    except requests.exceptions.RequestException as e:
        error_msg = f"API error for slide {slide_num}: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        return f"[解说词生成失败 - {image.get('alt', 'Slide ' + str(slide_num))}]"
    except Exception as e:
        error_msg = f"Failed to generate narration for slide {slide_num}: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        return f"[解说词生成失败，请手动补充 - {image.get('alt', 'Slide ' + str(slide_num))}]"


def generate_script_batch(
    images: List[Dict],
    doc_content: str,
    api_key: Optional[str] = None,
    model: str = "glm-4-flash",
    language: str = "zh-cn",
    batch_size: int = 5,
) -> List[str]:
    """
    Generate narrations in batches for efficiency.

    This can be more efficient than single-slide generation
    but may produce less contextually aware results.

    Args:
        images: List of image dicts
        doc_content: Full document content
        api_key: GLM API key
        model: LLM model name
        language: Output language
        batch_size: Number of slides per API call

    Returns:
        List of narration strings
    """
    narrations = []

    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        batch_narrations = _generate_batch_narrations(
            batch, doc_content, i + 1, api_key, model, language
        )
        narrations.extend(batch_narrations)

    return narrations


def _generate_batch_narrations(
    images: List[Dict],
    doc_content: str,
    start_num: int,
    api_key: Optional[str],
    model: str,
    language: str,
) -> List[str]:
    """Generate narrations for a batch of images."""
    from ..llm_proofread.glm_client import GLMClient

    # Build descriptions for all images in batch
    image_descriptions = []
    for i, img in enumerate(images):
        desc = f"Slide {start_num + i}: {img.get('alt', 'No description')}"
        if img.get("context"):
            desc += f"\nContext: {img['context'][:200]}"
        image_descriptions.append(desc)

    lang_instruction = (
        "用中文撰写解说词。" if language.startswith("zh")
        else "Write narrations in English."
    )

    prompt = f"""Write narration scripts for {len(images)} slides.

**Guidelines**: Same as before - clear, professional, 30-60 seconds each.
{lang_instruction}

**Document Context**:
{doc_content[:2000]}

**Slides**:
{chr(10).join(image_descriptions)}

**Output Format**: Return a JSON array of {len(images)} narration strings.
Example: ["Narration for slide 1...", "Narration for slide 2...", ...]"""

    client = GLMClient(api_key=api_key, model=model, temperature=0.7)

    try:
        import requests
        import json

        headers = {
            "Authorization": f"Bearer {client.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": client.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": client.temperature,
        }

        response = requests.post(
            client.api_url,
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Parse JSON array
        narrations = json.loads(content)
        if isinstance(narrations, list):
            return [str(n).strip() for n in narrations[:len(images)]]

    except Exception as e:
        logger.error(f"Batch generation failed: {e}")

    # Return placeholders on failure
    return [f"[解说词生成失败 - {img.get('alt', 'Slide')}]" for img in images]
