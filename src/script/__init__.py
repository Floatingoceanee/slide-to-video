import typer
from typing import Optional
import yaml
import click
from slide_to_video.lib import slide_to_video
from slide_to_video.project import ProjectConfig
from slide_to_video.tts_engine.registery import get_all_engine_names
from slide_to_video.doc_to_video import (
    extract_image_references,
    select_important_images,
    generate_narration_script,
    create_slide_pdf,
)
from slide_to_video.doc_to_video.markdown_parser import read_document_content


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


@app.command("from-doc")
def generate_from_doc(
    doc_path: Optional[str] = typer.Option(None, help="Path to markdown document"),
    image_dir: Optional[str] = typer.Option(None, help="Path to image directory (defaults to doc directory)"),
    output_dir: Optional[str] = typer.Option(None, help="Output directory for slide.pdf and script.txt"),
    api_key: Optional[str] = typer.Option(None, help="GLM API key (or set GLM_API_KEY env var)"),
    model: Optional[str] = typer.Option(None, help="LLM model name"),
    max_slides: Optional[int] = typer.Option(None, help="Maximum number of slides to generate"),
    language: Optional[str] = typer.Option(None, help="Language for narration script"),
    page_width: Optional[int] = typer.Option(None, help="PDF page width in pixels"),
    page_height: Optional[int] = typer.Option(None, help="PDF page height in pixels"),
    last_slide_delay: Optional[float] = typer.Option(None, help="Delay after last slide in seconds"),
    skip_selection: Optional[bool] = typer.Option(
        None,
        "--skip-selection",
        help="Skip LLM image selection, use all images",
    ),
    config: Optional[str] = typer.Option(None, help="Path to yaml config file (default: config_doc.yaml)"),
    ctx: typer.Context = typer.Option(None),
):
    """Generate slide.pdf and script.txt from help documentation.

    This command converts a markdown help document with images into
    a slide PDF and narration script ready for video generation.

    Example:
        slide-to-video from-doc --config config_doc.yaml
        slide-to-video from-doc --doc-path docs/guide.md --output-dir output
    """
    import os
    from pathlib import Path

    # Default config file name
    default_config = "config_doc.yaml"

    # Load config from file
    if config:
        config_path = Path(config)
    else:
        config_path = Path(default_config)

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f) or {}
        typer.echo(f"Loaded config from: {config_path}")
    else:
        raw_config = {}
        if config:  # User specified a config file that doesn't exist
            typer.echo(f"Warning: Config file not found: {config_path}", err=True)

    # Command-line arguments override config file values
    for key, value in ctx.params.items():
        if value is not None and key != "config":
            raw_config[key] = value

    # Set default values for optional parameters if not provided
    if "model" not in raw_config or raw_config["model"] is None:
        raw_config["model"] = "glm-4-flash"
    if "max_slides" not in raw_config or raw_config["max_slides"] is None:
        raw_config["max_slides"] = 30
    if "language" not in raw_config or raw_config["language"] is None:
        raw_config["language"] = "zh-cn"
    if "page_width" not in raw_config or raw_config["page_width"] is None:
        raw_config["page_width"] = 1920
    if "page_height" not in raw_config or raw_config["page_height"] is None:
        raw_config["page_height"] = 1080
    if "last_slide_delay" not in raw_config or raw_config["last_slide_delay"] is None:
        raw_config["last_slide_delay"] = 4.0
    if "skip_selection" not in raw_config or raw_config["skip_selection"] is None:
        raw_config["skip_selection"] = False

    # Validate required fields
    if not raw_config.get("doc_path"):
        typer.echo("Error: doc_path is required (set in config or via --doc-path)", err=True)
        raise typer.Exit(1)
    if not raw_config.get("output_dir"):
        typer.echo("Error: output_dir is required (set in config or via --output-dir)", err=True)
        raise typer.Exit(1)

    # Extract values from config
    doc_path = raw_config["doc_path"]
    image_dir = raw_config.get("image_dir")
    output_dir = raw_config["output_dir"]
    api_key = raw_config.get("api_key")
    model = raw_config["model"]
    max_slides = raw_config["max_slides"]
    language = raw_config["language"]
    page_width = raw_config["page_width"]
    page_height = raw_config["page_height"]
    last_slide_delay = raw_config["last_slide_delay"]
    skip_selection = raw_config["skip_selection"]

    # Resolve paths
    doc_path = Path(doc_path).resolve()
    if not doc_path.exists():
        typer.echo(f"Error: Document not found: {doc_path}", err=True)
        raise typer.Exit(1)

    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine image directory
    if image_dir:
        image_dir = Path(image_dir).resolve()
        if not image_dir.exists():
            typer.echo(f"Error: Image directory not found: {image_dir}", err=True)
            raise typer.Exit(1)
    else:
        image_dir = doc_path.parent

    typer.echo(f"Processing document: {doc_path}")
    typer.echo(f"Image directory: {image_dir}")
    typer.echo(f"Output directory: {output_dir}")

    # Step 1: Extract image references from markdown
    typer.echo("\n[1/4] Extracting image references from document...")
    images = extract_image_references(
        md_path=str(doc_path),
        image_dir=str(image_dir),
        context_lines=3,
    )

    if not images:
        typer.echo("Error: No images found in the document", err=True)
        raise typer.Exit(1)

    typer.echo(f"Found {len(images)} image references")

    # Check for missing images
    missing = [img for img in images if not img.get("exists", False)]
    if missing:
        typer.echo(f"Warning: {len(missing)} images not found on disk")

    # Step 2: Select important images using LLM
    if skip_selection:
        typer.echo("\n[2/4] Skipping image selection (using all valid images)...")
        selected_images = [img for img in images if img.get("exists", False)]
        if len(selected_images) > max_slides:
            typer.echo(f"Limiting to first {max_slides} images")
            selected_images = selected_images[:max_slides]
    else:
        typer.echo(f"\n[2/4] Selecting important images (max {max_slides})...")
        doc_content = read_document_content(str(doc_path))
        selected_images = select_important_images(
            images=images,
            doc_content=doc_content,
            max_count=max_slides,
            api_key=api_key,
            model=model,
        )

    if not selected_images:
        typer.echo("Error: No valid images selected", err=True)
        raise typer.Exit(1)

    typer.echo(f"Selected {len(selected_images)} images for slides")

    # Step 3: Generate slide PDF
    typer.echo("\n[3/4] Generating slide PDF...")
    slide_pdf_path = output_dir / "slide.pdf"
    image_paths = [img["path"] for img in selected_images]

    try:
        create_slide_pdf(
            image_paths=image_paths,
            output_path=str(slide_pdf_path),
            page_size=(page_width, page_height),
        )
        typer.echo(f"Created: {slide_pdf_path}")
    except Exception as e:
        typer.echo(f"Error creating PDF: {e}", err=True)
        raise typer.Exit(1)

    # Step 4: Generate narration script
    typer.echo("\n[4/4] Generating narration script...")
    script_path = output_dir / "script.txt"

    try:
        # Re-read doc content if we skipped selection
        if skip_selection:
            doc_content = read_document_content(str(doc_path))

        # Progress callback to show status
        def on_progress(slide_num: int, total: int, message: str):
            typer.echo(f"  [{slide_num}/{total}] {message}")

        script_content = generate_narration_script(
            images=selected_images,
            doc_content=doc_content,
            api_key=api_key,
            model=model,
            language=language,
            last_slide_delay=last_slide_delay,
            progress_callback=on_progress,
        )

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        typer.echo(f"Created: {script_path}")
    except Exception as e:
        typer.echo(f"Error generating script: {e}", err=True)
        raise typer.Exit(1)

    # Summary
    typer.echo("\n" + "=" * 50)
    typer.echo("Generation complete!")
    typer.echo(f"  Slides: {len(selected_images)}")
    typer.echo(f"  slide.pdf: {slide_pdf_path}")
    typer.echo(f"  script.txt: {script_path}")
    typer.echo("\nNext steps:")
    typer.echo("  1. Review and edit script.txt if needed")
    typer.echo("  2. Run: slide-to-video --config <config.yaml>")
    typer.echo("=" * 50)


def main():
    app()
