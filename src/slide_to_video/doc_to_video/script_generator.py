"""
Script generator using LLM.

Generates narration scripts for slide images using LLM API.
"""

import json
import logging
from typing import List, Dict, Optional, Any, Callable

logger = logging.getLogger(__name__)


from typing import Callable

def generate_narration_script(
    images: List[Dict],
    doc_content: str,
    llm_config: Optional[Dict[str, Any]] = None,
    # Legacy parameters for backward compatibility
    api_key: Optional[str] = None,
    model: str = "glm-4-flash",
    language: str = "zh-cn",
    last_slide_delay: float = 4.0,
    target_word_count: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> str:
    """
    Generate narration script for a list of images.

    Args:
        images: List of selected image dicts with alt text and context
        doc_content: Full document content for reference
        llm_config: LLM configuration dict with 'provider', 'model', 'api_key', etc.
        api_key: (Legacy) GLM API key, used if llm_config not provided
        model: (Legacy) LLM model name, used if llm_config not provided
        language: Output language (zh-cn, en, etc.)
        last_slide_delay: Delay in seconds to add after the last slide
        target_word_count: Target word count for entire script (optional)
        progress_callback: Optional callback function(slide_num, total, message)

    Returns:
        Script text in slide-to-video format (NEWSLIDE separated)
    """
    if not images:
        logger.warning("No images provided for script generation")
        return ""

    # Generate narration for each image with context accumulation
    narrations = []
    previous_narrations = []  # Track previous narrations for context
    current_word_count = 0

    for i, img in enumerate(images):
        slide_num = i + 1
        total = len(images)
        msg = f"Generating narration for slide {slide_num}/{total}..."

        logger.info(msg)
        if progress_callback:
            progress_callback(slide_num, total, msg)

        # Calculate remaining word budget if target is set
        remaining_words = None
        if target_word_count is not None:
            remaining_budget = target_word_count - current_word_count
            remaining_slides = total - slide_num + 1
            if remaining_budget > 0:
                remaining_words = int(remaining_budget / remaining_slides)
            else:
                # Already over budget, set to 0 to request minimal content
                remaining_words = 0

        narration = _generate_single_narration(
            image=img,
            doc_content=doc_content,
            slide_num=slide_num,
            total_slides=total,
            llm_config=llm_config,
            api_key=api_key,
            model=model,
            language=language,
            previous_narrations=previous_narrations,
            remaining_words=remaining_words,
        )
        narrations.append(narration)

        # Update context and word count
        previous_narrations.append(narration)
        current_word_count += len(narration.split())

        if progress_callback:
            if target_word_count:
                progress_msg = f"  Word count: {current_word_count}/{target_word_count}"
                progress_callback(slide_num, total, progress_msg)

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
    if target_word_count:
        logger.info(f"Final word count: {current_word_count}/{target_word_count}")
    return script_content


def _generate_single_narration(
    image: Dict,
    doc_content: str,
    slide_num: int,
    total_slides: int,
    llm_config: Optional[Dict[str, Any]],
    api_key: Optional[str],
    model: str,
    language: str,
    previous_narrations: Optional[List[str]] = None,
    remaining_words: Optional[int] = None,
) -> str:
    """
    Generate narration for a single slide image.

    Args:
        image: Image dict with alt, context, etc.
        doc_content: Full document content
        slide_num: Current slide number (1-based)
        total_slides: Total number of slides
        llm_config: LLM configuration dict
        api_key: (Legacy) API key
        model: (Legacy) Model name
        language: Output language
        previous_narrations: List of previously generated narrations for context
        remaining_words: Target word count for this slide (optional)
    Returns:
        Narration text for this slide
    """
    from ..llm_client import create_llm_client

    # Build context for this image
    image_description = image.get("alt", "")
    image_context = image.get("context", "")

    # Build previous context to avoid repetition
    previous_context = ""
    if previous_narrations:
        # Format previous narrations with slide numbers
        formatted_prev = []
        for i, narr in enumerate(previous_narrations):
            if i == len(previous_narrations) - 1:
                # For the most recent slide (previous one), show full content
                formatted_prev.append(f"Slide {i+1}: {narr}")
            else:
                # For older slides, show first 150 chars only
                preview = narr[:150] + "..." if len(narr) > 150 else narr
                formatted_prev.append(f"Slide {i+1}: {preview}")

        # If context is too long, summarize older entries
        context_str = "\n".join(formatted_prev)
        if len(context_str) > 2500:
            # Summarize older slides if context is too long
            if len(previous_narrations) > 2:
                older_count = len(previous_narrations) - 1
                latest = formatted_prev[-1]  # Keep the most recent one
                previous_context = f"""
**Previously Generated Narrations** (for context, DO NOT repeat):
Slides 1-{older_count}: [Summarized - covered introduction and earlier content]
{latest}

**Important**: Ensure your narration is UNIQUE and does not repeat content from above.
"""
            else:
                previous_context = f"""
**Previously Generated Narrations** (for context, DO NOT repeat):
{context_str}

**Important**: Ensure your narration is UNIQUE and does not repeat content from above.
"""
        else:
            previous_context = f"""
**Previously Generated Narrations** (for context, DO NOT repeat):
{context_str}

**Important**: Ensure your narration is UNIQUE and does not repeat content from above.
"""

    # Build word count guidance
    word_count_guidance = ""
    if remaining_words is not None:
        if remaining_words == 0:
            word_count_guidance = """
**Word Count Budget**: EXCEEDED. Keep this narration EXTREMELY concise (1-2 sentences max).
"""
        else:
            word_count_guidance = f"""
**Word Count Budget**: You have approximately {remaining_words} words for this slide.
Keep your narration concise to stay within budget.
"""

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
{previous_context}
{word_count_guidance}
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

    # Create LLM client from config or legacy parameters
    if llm_config:
        client = create_llm_client(
            provider=llm_config.get("provider", "glm"),
            model=llm_config.get("model"),
            api_key=llm_config.get("api_key"),
            api_url=llm_config.get("api_url"),
            temperature=llm_config.get("temperature", 0.7),
        )
    else:
        # Legacy mode: use GLM client directly
        client = create_llm_client(
            provider="glm",
            model=model,
            api_key=api_key,
            temperature=0.7,
        )
    try:
        content = client.chat(prompt, temperature=0.7)
        # Clean up the response
        content = content.strip()
        # Remove any markdown formatting
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        return content
    except Exception as e:
        error_msg = f"Failed to generate narration for slide {slide_num}: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        return f"[解说词生成失败 - {image.get('alt', 'Slide ' + str(slide_num))}]"
def generate_script_batch(
    images: List[Dict],
    doc_content: str,
    llm_config: Optional[Dict[str, Any]] = None,
    # Legacy parameters
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
        llm_config: LLM configuration dict
        api_key: (Legacy) GLM API key
        model: (Legacy) LLM model name
        language: Output language
        batch_size: Number of slides per API call
    Returns:
        List of narration strings
    """
    from ..llm_client import create_llm_client
    # Generate narrations in batches for efficiency
    narrations = []
    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        batch_narrations = _generate_batch_narrations(
            batch, doc_content, i + 1, llm_config, api_key, model, language
        )
        narrations.extend(batch_narrations)
    return narrations
def _generate_batch_narrations(
    images: List[Dict],
    doc_content: str,
    start_num: int,
    llm_config: Optional[Dict[str, Any]],
    api_key: Optional[str],
    model: str,
    language: str,
) -> List[str]:
    """Generate narrations for a batch of images."""
    from ..llm_client import create_llm_client
    # Create LLM client
    if llm_config:
        client = create_llm_client(
            provider=llm_config.get("provider", "glm"),
            model=llm_config.get("model"),
            api_key=llm_config.get("api_key"),
            temperature=llm_config.get("temperature", 0.7),
        )
    else:
        client = create_llm_client(
            provider="glm",
            model=model,
            api_key=api_key,
            temperature=0.7,
        )
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
    try:
        content = client.chat(prompt, temperature=0.7)
        # Parse JSON array
        narrations = json.loads(content)
        if isinstance(narrations, list):
            return [str(n).strip() for n in narrations[:len(images)]]
    except Exception as e:
        logger.error(f"Batch generation failed: {e}")
    # Return placeholders on failure
    return [f"[解说词生成失败 - {img.get('alt', 'Slide')}]" for img in images]
