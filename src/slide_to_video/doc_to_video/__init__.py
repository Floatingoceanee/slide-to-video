"""
Doc to Video module.

Converts markdown help documentation to slide.pdf and script.txt
for the slide-to-video pipeline.
"""

from .markdown_parser import extract_image_references
from .image_selector import select_important_images
from .script_generator import generate_narration_script
from .pdf_generator import create_slide_pdf

__all__ = [
    "extract_image_references",
    "select_important_images",
    "generate_narration_script",
    "create_slide_pdf",
]
