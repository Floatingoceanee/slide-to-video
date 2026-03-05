import typer
from typing import Optional
import yaml
import click
from slide_to_video.lib import slide_to_video
from slide_to_video.project import ProjectConfig
from slide_to_video.tts_engine.registery import get_all_engine_names


app = typer.Typer()


@app.command()
def generate(
    model: Optional[str] = typer.Option(
        None,
        help="Model to use. Use 'local' for local TTS engine or 'playht' for PlayHT TTS engine",
        case_sensitive=False,
        click_type=click.Choice(get_all_engine_names()),
    ),
    slide: Optional[str] = typer.Option(None, help="Slide PDF file path"),
    script: Optional[str] = typer.Option(None, help="Script file path"),
    output_dir: Optional[str] = typer.Option(None, help="Output directory"),
    voice: Optional[str] = typer.Option(
        None, help="Voice sample path or ID. Depends on the model."
    ),
    speech_speed: Optional[float] = typer.Option(
        None, help="Speed of the speech. Default value: 1.0."
    ),
    delay: Optional[float] = typer.Option(
        None, help="Delay between each slide in seconds. Default value: 2.0."
    ),
    script_dict: Optional[str] = typer.Option(
        None,
        help='Dictionary to replace the script. Each line should follow the format "original_text: new_text"',
    ),
    language: Optional[str] = typer.Option(
        None,
        case_sensitive=False,
        click_type=click.Choice(
            [
                "en",
                "es",
                "fr",
                "de",
                "it",
                "pt",
                "pl",
                "tr",
                "ru",
                "nl",
                "cs",
                "ar",
                "zh-cn",
                "hu",
                "ko",
                "ja",
                "hi",
            ]
        ),
        help="Language of the text. Default value: en.",
    ),
    enable_subtitle: Optional[bool] = typer.Option(
        None,
        help="Enable subtitle generation. Default: True.",
    ),
    subtitle_mode: Optional[str] = typer.Option(
        None,
        help="Subtitle mode: 'soft' (muxed, fast) or 'hard' (burned into video). Default: soft.",
        click_type=click.Choice(["soft", "hard"]),
    ),
    whisper_model_size: Optional[str] = typer.Option(
        None,
        help="Whisper model size for subtitle generation. Options: tiny, base, small, medium, large. Default: base.",
        click_type=click.Choice(["tiny", "base", "small", "medium", "large"]),
    ),
    no_interactive: Optional[bool] = typer.Option(
        None,
        "--no-interactive",
        help="Skip all interactive prompts. Uses defaults for missing values.",
    ),
    config: Optional[str] = typer.Option(None, help="Path to yaml config file"),
    ctx: typer.Context = typer.Option(None),
):
    # Load the project config from file first (if provided)
    if config:
        with open(config, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f) or {}
    else:
        raw_config = {}

    # Command-line arguments override config file values
    for key, value in ctx.params.items():
        if value is not None:
            raw_config[key] = value

    # Set default values for optional parameters if not provided
    if "speech_speed" not in raw_config or raw_config["speech_speed"] is None:
        raw_config["speech_speed"] = 1.0
    if "delay" not in raw_config or raw_config["delay"] is None:
        raw_config["delay"] = 2.0
    if "language" not in raw_config or raw_config["language"] is None:
        raw_config["language"] = "en"
    if "enable_subtitle" not in raw_config or raw_config["enable_subtitle"] is None:
        raw_config["enable_subtitle"] = True
    if "subtitle_mode" not in raw_config or raw_config["subtitle_mode"] is None:
        raw_config["subtitle_mode"] = "soft"
    if "whisper_model_size" not in raw_config or raw_config["whisper_model_size"] is None:
        raw_config["whisper_model_size"] = "base"
    if "no_interactive" not in raw_config or raw_config["no_interactive"] is None:
        raw_config["no_interactive"] = False
    if "enable_interactive" not in raw_config or raw_config["enable_interactive"] is None:
        # enable_interactive defaults to True unless no_interactive is set
        raw_config["enable_interactive"] = not raw_config.get("no_interactive", False)

    # ProjectConfig will validate required fields (model, slide, script, output_dir)
    project_config = ProjectConfig(raw_config)
    slide_to_video(project_config=project_config)


def main():
    app()
