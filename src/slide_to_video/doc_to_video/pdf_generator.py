"""
PDF generator from images.

Creates slide PDF from selected images with uniform sizing.
"""

import logging
from typing import List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default page size: 1920x1080 (16:9 aspect ratio)
DEFAULT_PAGE_SIZE = (1920, 1080)


def create_slide_pdf(
    image_paths: List[str],
    output_path: str,
    page_size: Tuple[int, int] = DEFAULT_PAGE_SIZE,
    background_color: str = "white",
    fit_mode: str = "contain",
) -> str:
    """
    Create a PDF from a list of images with uniform page size.

    Args:
        image_paths: List of paths to image files
        output_path: Output PDF file path
        page_size: Tuple of (width, height) in pixels. Default: (1920, 1080)
        background_color: Background color for letterboxing. Default: "white"
        fit_mode: How to fit images: "contain" (fit within) or "cover" (fill page)

    Returns:
        Path to the generated PDF file

    Raises:
        ImportError: If required libraries not installed
        ValueError: If no valid images provided
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            "Pillow library required for PDF generation. "
            "Install with: pip install Pillow"
        )

    if not image_paths:
        raise ValueError("No image paths provided")

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_width, page_height = page_size

    # Validate and load images
    valid_images = []
    for img_path in image_paths:
        path = Path(img_path)
        if not path.exists():
            logger.warning(f"Image not found, skipping: {img_path}")
            continue
        try:
            img = Image.open(path)
            # Convert to RGB if necessary (PDF requires RGB)
            if img.mode in ("RGBA", "P"):
                # Create white background for transparency
                background = Image.new("RGB", img.size, background_color)
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            valid_images.append((path, img))
        except Exception as e:
            logger.warning(f"Failed to load image {img_path}: {e}")
            continue

    if not valid_images:
        raise ValueError("No valid images could be loaded")

    logger.info(f"Creating PDF with {len(valid_images)} slides at {page_size}")

    # Process each image to uniform size
    processed_images = []
    for path, img in valid_images:
        processed = _resize_image(img, page_width, page_height, background_color, fit_mode)
        processed_images.append(processed)

    # Save as PDF
    first_image = processed_images[0]
    remaining_images = processed_images[1:] if len(processed_images) > 1 else []

    first_image.save(
        output_path,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=remaining_images,
    )

    logger.info(f"PDF created: {output_path}")
    return str(output_path)


def _resize_image(
    img: "Image.Image",
    target_width: int,
    target_height: int,
    background_color: str,
    fit_mode: str,
) -> "Image.Image":
    """
    Resize an image to fit target dimensions.

    Args:
        img: PIL Image object
        target_width: Target width in pixels
        target_height: Target height in pixels
        background_color: Background color for letterboxing
        fit_mode: "contain" or "cover"

    Returns:
        Resized PIL Image in RGB mode
    """
    from PIL import Image

    orig_width, orig_height = img.size
    orig_ratio = orig_width / orig_height
    target_ratio = target_width / target_height

    if fit_mode == "contain":
        # Fit image within bounds (may have letterboxing)
        if orig_ratio > target_ratio:
            # Image is wider - fit to width
            new_width = target_width
            new_height = int(target_width / orig_ratio)
        else:
            # Image is taller - fit to height
            new_height = target_height
            new_width = int(target_height * orig_ratio)
    else:  # cover
        # Fill the page (may crop image)
        if orig_ratio > target_ratio:
            # Image is wider - fit to height
            new_height = target_height
            new_width = int(target_height * orig_ratio)
        else:
            # Image is taller - fit to width
            new_width = target_width
            new_height = int(target_width / orig_ratio)

    # Resize with high quality resampling
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create background canvas
    canvas = Image.new("RGB", (target_width, target_height), background_color)

    # Center the image on canvas
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    canvas.paste(resized, (x_offset, y_offset))

    return canvas


def get_image_info(image_path: str) -> Optional[dict]:
    """
    Get information about an image file.

    Args:
        image_path: Path to the image file

    Returns:
        Dict with image info or None if invalid
    """
    try:
        from PIL import Image
    except ImportError:
        return None

    path = Path(image_path)
    if not path.exists():
        return None

    try:
        with Image.open(path) as img:
            return {
                "path": str(path),
                "size": img.size,
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
            }
    except Exception:
        return None
