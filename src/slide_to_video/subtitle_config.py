"""
Subtitle style configuration module.

Provides customizable subtitle styling options for hard-burned subtitles,
including font, color, position, and other visual parameters.
"""

from typing import Dict, Optional
import sys
import logging

logger = logging.getLogger(__name__)


DEFAULT_SUBTITLE_STYLE = {
    "Fontname": "Arial",
    "FontSize": 24,
    "PrimaryColour": "&HFFFFFF&",  # White
    "OutlineColour": "&H000000&",  # Black outline
    "Outline": 2,
    "Shadow": 1,
    "Alignment": 2,  # Bottom center
    "MarginL": 10,
    "MarginR": 10,
    "MarginV": 30,
}

SUBTITLE_STYLE_HELP = """
Available subtitle style parameters:
- Fontname: Font name (e.g., Arial, SimHei, Microsoft YaHei)
- FontSize: Font size in pixels
- PrimaryColour: Text color (format: &HBBGGRR&, e.g., &HFFFFFF&=white, &H000000&=black)
- OutlineColour: Outline/border color
- BackColour: Background color (for opaque box)
- Outline: Outline width in pixels
- Shadow: Shadow depth in pixels
- Bold: Bold text (0=off, 1=on, -1=toggle)
- Italic: Italic text (0=off, 1=on, -1=toggle)
- Underline: Underline text (0=off, 1=on, -1=toggle)
- StrikeOut: Strikethrough (0=off, 1=on)
- ScaleX: Horizontal scaling percentage (100=normal)
- ScaleY: Vertical scaling percentage (100=normal)
- Spacing: Extra spacing between characters in pixels
- Angle: Rotation angle in degrees
- BorderStyle: 1=outline+shadow, 3=opaque box
- Alignment:
  - 1=bottom-left, 2=bottom-center, 3=bottom-right
  - 4=middle-left, 5=middle-center, 6=middle-right
  - 7=top-left, 8=top-center, 9=top-right
- MarginL: Left margin in pixels
- MarginR: Right margin in pixels
- MarginV: Vertical margin in pixels (from bottom for bottom-aligned)

Color format explanation:
- Format: &HBBGGRR& (Blue, Green, Red in hex)
- Examples:
  - White: &HFFFFFF&
  - Black: &H000000&
  - Red: &H0000FF&
  - Green: &H00FF00&
  - Blue: &HFF0000&
  - Yellow: &H00FFFF&
"""


def build_force_style_string(style_config: Dict) -> str:
    """
    Convert style configuration dict to FFmpeg force_style string.

    Args:
        style_config: Dictionary of style parameters

    Returns:
        FFmpeg force_style string
    """
    if not style_config:
        style_config = DEFAULT_SUBTITLE_STYLE

    # Filter out None values and build the string
    style_parts = [f"{key}={value}" for key, value in style_config.items() if value is not None]

    return ','.join(style_parts)


def prompt_subtitle_style() -> Dict:
    """
    Interactively get user subtitle style configuration.

    - Shows available parameters
    - Accepts user input
    - Returns style config dict

    Returns:
        Dictionary of style parameters
    """
    print("\n" + "=" * 60)
    print("Subtitle Style Configuration")
    print("=" * 60)
    print(SUBTITLE_STYLE_HELP)
    print("=" * 60)
    print("\nPress Enter to use default value for each parameter.")
    print("Enter 'done' at any time to finish configuration.\n")

    style_config = {}

    # Key parameters that users commonly want to customize
    key_params = [
        ("Fontname", "Font name", DEFAULT_SUBTITLE_STYLE["Fontname"]),
        ("FontSize", "Font size (pixels)", DEFAULT_SUBTITLE_STYLE["FontSize"]),
        ("PrimaryColour", "Text color", DEFAULT_SUBTITLE_STYLE["PrimaryColour"]),
        ("OutlineColour", "Outline color", DEFAULT_SUBTITLE_STYLE["OutlineColour"]),
        ("Outline", "Outline width", DEFAULT_SUBTITLE_STYLE["Outline"]),
        ("Alignment", "Alignment (1-9)", DEFAULT_SUBTITLE_STYLE["Alignment"]),
        ("MarginV", "Vertical margin", DEFAULT_SUBTITLE_STYLE["MarginV"]),
    ]

    for param_name, param_desc, default_value in key_params:
        sys.stdout.write(f"{param_desc} [{default_value}]: ")
        sys.stdout.flush()
        try:
            line = sys.stdin.readline()
        except EOFError:
            line = ""
        # readline() returns "" on EOF (non-TTY / piped stdin)
        if not line:
            print(f"  Non-interactive mode, using default: {default_value}")
            style_config[param_name] = default_value
            continue
        user_input = line.strip()

        if user_input.lower() == 'done':
            break

        if user_input:
            # Convert to appropriate type
            if param_name in ["FontSize", "Outline", "Alignment", "MarginL", "MarginR", "MarginV", "Shadow", "Bold", "Italic"]:
                try:
                    style_config[param_name] = int(user_input)
                except ValueError:
                    print(f"  Invalid number, using default: {default_value}")
                    style_config[param_name] = default_value
            elif param_name in ["ScaleX", "ScaleY", "Spacing", "Angle"]:
                try:
                    style_config[param_name] = float(user_input)
                except ValueError:
                    print(f"  Invalid number, using default: {default_value}")
                    style_config[param_name] = default_value
            else:
                style_config[param_name] = user_input
        else:
            style_config[param_name] = default_value

    print("\nStyle configuration complete.")
    return style_config


def get_subtitle_style(config: Dict, no_interactive: bool = False) -> Dict:
    """
    Get subtitle style configuration.

    Priority:
    1. Use config.get('subtitle_style', {}) if available
    2. If no_interactive=True, fill missing with defaults
    3. Otherwise, interactively ask for missing config

    Args:
        config: Project configuration dict
        no_interactive: If True, skip interactive prompts

    Returns:
        Complete style configuration dict
    """
    # Start with any style config from file
    style_config = config.get('subtitle_style', {})

    if not style_config:
        if no_interactive:
            logger.info("No subtitle style configured, using defaults")
            return DEFAULT_SUBTITLE_STYLE.copy()
        else:
            # Interactive mode
            return prompt_subtitle_style()

    # Fill in missing values with defaults
    complete_config = DEFAULT_SUBTITLE_STYLE.copy()
    complete_config.update(style_config)

    return complete_config


def validate_style_config(style_config: Dict) -> bool:
    """
    Validate subtitle style configuration.

    Args:
        style_config: Style configuration dict to validate

    Returns:
        True if valid, False otherwise
    """
    # Check required keys
    required_keys = ["Fontname", "FontSize", "PrimaryColour", "Alignment"]
    for key in required_keys:
        if key not in style_config:
            logger.warning(f"Missing required style parameter: {key}")
            return False

    # Validate specific values
    if style_config.get("FontSize", 0) <= 0:
        logger.warning("FontSize must be positive")
        return False

    alignment = style_config.get("Alignment", 2)
    if not 1 <= alignment <= 9:
        logger.warning("Alignment must be between 1 and 9")
        return False

    # Validate color format (should start with &H and end with &)
    for color_key in ["PrimaryColour", "OutlineColour", "BackColour"]:
        if color_key in style_config:
            color = style_config[color_key]
            if not (color.startswith('&H') and color.endswith('&')):
                logger.warning(f"Invalid color format for {color_key}: {color}")
                return False

    return True
