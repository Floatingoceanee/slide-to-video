"""
Markdown parser for extracting image references.

Parses markdown files to extract image references with their
surrounding context for use in slide generation.
"""

import re
import os
from typing import List, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def extract_image_references(
    md_path: str,
    image_dir: str = None,
    context_lines: int = 3,
) -> List[Dict]:
    """
    Extract all image references from a markdown file.

    Args:
        md_path: Path to the markdown file
        image_dir: Optional directory to resolve relative image paths.
                   If None, uses the directory containing the markdown file.
        context_lines: Number of lines before/after image to include as context

    Returns:
        List of dicts with keys:
            - alt: Image alt text/description
            - path: Absolute path to the image file
            - original_path: Original path as written in markdown
            - context: Surrounding text lines for context
            - line_number: Line number in the markdown file
    """
    md_path = Path(md_path).resolve()
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    # Determine base directory for resolving image paths
    if image_dir:
        base_dir = Path(image_dir).resolve()
    else:
        base_dir = md_path.parent

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Pattern to match markdown images: ![alt](path)
    # Also matches HTML img tags: <img src="path" alt="alt">
    md_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    html_pattern = re.compile(
        r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*/?>',
        re.IGNORECASE
    )

    images = []

    for line_num, line in enumerate(lines, start=1):
        # Check for markdown-style images
        for match in md_pattern.finditer(line):
            alt_text = match.group(1).strip()
            img_path = match.group(2).strip()

            # Resolve the image path
            resolved_path = _resolve_image_path(img_path, base_dir, md_path.parent)

            # Get context (surrounding lines)
            context_start = max(0, line_num - context_lines - 1)
            context_end = min(len(lines), line_num + context_lines)
            context = "".join(lines[context_start:context_end]).strip()

            images.append({
                "alt": alt_text,
                "path": str(resolved_path),
                "original_path": img_path,
                "context": context,
                "line_number": line_num,
                "exists": resolved_path.exists(),
            })

        # Check for HTML-style images
        for match in html_pattern.finditer(line):
            img_path = match.group(1).strip()
            alt_text = match.group(2).strip() if match.group(2) else ""

            # Resolve the image path
            resolved_path = _resolve_image_path(img_path, base_dir, md_path.parent)

            # Get context (surrounding lines)
            context_start = max(0, line_num - context_lines - 1)
            context_end = min(len(lines), line_num + context_lines)
            context = "".join(lines[context_start:context_end]).strip()

            images.append({
                "alt": alt_text,
                "path": str(resolved_path),
                "original_path": img_path,
                "context": context,
                "line_number": line_num,
                "exists": resolved_path.exists(),
            })

    logger.info(f"Found {len(images)} image references in {md_path}")

    # Log warnings for missing images
    missing = [img for img in images if not img["exists"]]
    if missing:
        logger.warning(
            f"{len(missing)} images not found: "
            f"{', '.join(img['original_path'] for img in missing[:5])}"
            f"{'...' if len(missing) > 5 else ''}"
        )

    return images


def _resolve_image_path(
    img_path: str,
    base_dir: Path,
    md_dir: Path,
) -> Path:
    """
    Resolve an image path from markdown to an absolute path.

    Tries multiple strategies:
    1. Absolute path (if already absolute)
    2. Relative to base_dir
    3. Relative to markdown file directory

    Args:
        img_path: Image path from markdown
        base_dir: Base directory for image resolution
        md_dir: Directory containing the markdown file

    Returns:
        Resolved Path object (may not exist)
    """
    img_path = img_path.strip()

    # Handle URL-encoded paths
    if "%" in img_path:
        from urllib.parse import unquote
        img_path = unquote(img_path)

    # Skip remote URLs
    if img_path.startswith(("http://", "https://", "//")):
        return Path(img_path)  # Will show as not existing

    # Try absolute path first
    if os.path.isabs(img_path):
        return Path(img_path)

    # Try relative to base_dir
    path_from_base = base_dir / img_path
    if path_from_base.exists():
        return path_from_base

    # Try relative to markdown file directory
    path_from_md = md_dir / img_path
    if path_from_md.exists():
        return path_from_md

    # Default to base_dir resolution (may not exist)
    return path_from_base


def read_document_content(md_path: str) -> str:
    """
    Read the full content of a markdown file.

    Args:
        md_path: Path to the markdown file

    Returns:
        Full text content of the file
    """
    md_path = Path(md_path).resolve()
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()
