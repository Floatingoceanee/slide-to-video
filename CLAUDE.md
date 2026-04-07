# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python tool that converts PDF slide decks into videos with voice narration. Supports multiple TTS engines (local Coqui TTS and cloud Play.ht), 17+ languages, subtitle generation via Whisper, interactive proofreading, and custom subtitle styling.

## Key Commands

### Installation
```bash
pip install .              # Install the package
slide-to-video --help      # View all CLI options
```

### Testing
```bash
pytest test                                          # Run all tests
pytest --cov=src --cov-report=term-missing test/     # Run with coverage
pytest test/test_specific_file.py                    # Run single test file
pytest test/test_specific_file.py::test_function_name  # Run single test
```

### Code Quality
```bash
ruff check                # Linting
pyright                   # Type checking
```

### Running the Tool
```bash
# Using config file (recommended)
slide-to-video --config config.yaml

# Using only command line arguments
slide-to-video --model local --slide example/slide.pdf --script example/script.txt --voice example/sample.mp3 --output-dir output

# Config file + override specific parameters
slide-to-video --config config.yaml --subtitle-mode hard --speech-speed 1.2

# Non-interactive mode (skip all prompts)
slide-to-video --config config.yaml --no-interactive
```

**Note**: All CLI parameters are optional. Required fields (`model`, `slide`, `script`, `output_dir`) can be provided via config file. Command-line arguments override config file values.

## Architecture

The codebase follows a modular engine-based architecture with these key components:

### Entry Points
- **`src/slide_to_video/lib.py`**: Library entry point - `slide_to_video()` function accepts `ProjectConfig`
- **`src/script/__init__.py`**: CLI built with Typer, parses args and calls `slide_to_video()`

### Core Processing Pipeline
1. **`project.py`**: Orchestrates the entire build process
   - `Project` class manages slide/script items and caching
   - `Task` class builds individual slide+audio segments
   - `process_subtitles()` handles subtitle generation, proofreading, and styling
   - `prompt_user_confirmation()` for interactive workflow
   - Uses MD5 hashing for incremental builds (skips unchanged content)
   - Outputs `project.yaml` to track cached state

2. **Engine System** (in `src/slide_to_video/`):
   - `slide_engine.py`: PDF → images via PyMuPDF
   - `script_engine.py`: Splits script by `NEWSLIDE` markers
   - `video_engine.py`: FFmpeg operations (concatenate, add audio, subtitles)
   - `tts_engine/`: Pluggable TTS backends

3. **Subtitle System** (in `src/slide_to_video/`):
   - `proofread.py`: Subtitle proofreading against original script
   - `subtitle_config.py`: Subtitle style configuration and validation
   - `utils.py`: Whisper-based SRT generation and merging

### TTS Engine Plugin System
- **`base_engine.py`**: Abstract `TTSEngine` class - all engines must inherit from this
- **`registery.py`**: `register_engine(name, class)` makes engines available
- **Auto-discovery**: Modules in `tts_engine/` are auto-imported via `auto_discover_engines()`
- Engines return `parallizable() -> bool` to indicate thread-safety

### Subtitle Processing Pipeline
1. **Generation**: Each `Task` uses Whisper to generate SRT from audio
2. **Merging**: `merge_srt_files()` combines all segment SRTs with time offsets
3. **Proofreading**: `proofread_srt()` corrects errors using script.txt as reference
4. **Interactive Confirmation**: User reviews and confirms proofread subtitles
5. **Application**:
   - Soft mode: `add_subtitle_to_video_soft()` muxes subtitles
   - Hard mode: `burn_subtitles_to_video()` burns with custom styles

## Adding New TTS Engines

1. Create new file in `src/slide_to_video/tts_engine/`
2. Inherit from `TTSEngine` and implement:
   - `synthesize(text, output_path, format)` - generate audio
   - `parallizable()` - return True if thread-safe
   - Set class attributes: `REQUIRED_CONFIG_KEYS`, `SUPPORTED_LANGUAGES`, `ENGINE_NAME`
3. Call `register_engine("engine_name", EngineClass)` at module level
4. Engine auto-appears in CLI choices

## Script Format
Scripts use `NEWSLIDE` markers to separate content for each slide:
```
NEWSLIDE
Narration for slide 1 goes here.

NEWSLIDE
Narration for slide 2 goes here.
```

Per-slide configuration using `===`:
```
NEWSLIDE
Narration for this slide.
===
#delay: 3.0
```

## Config File Format
```yaml
# Required
model: local                    # TTS engine (local, playht, openai-tts)
slide: path/to/slide.pdf        # PDF slide deck
script: path/to/script.txt      # Narration script
output_dir: output              # Output directory

# Optional - TTS
voice: path/to/sample.mp3       # Voice sample for cloning (local engine)
language: en                    # Language code
speech_speed: 1.0               # Speech speed multiplier
delay: 2.0                      # Delay between slides (seconds)

# Optional - Subtitles
enable_subtitle: true           # Enable subtitle generation
subtitle_mode: soft             # "soft" (muxed) or "hard" (burned)
whisper_model_size: base        # Whisper model: tiny, base, small, medium, large
no_interactive: false           # Skip all interactive prompts

# Optional - Subtitle Styling (hard mode only)
subtitle_style:
  Fontname: Arial
  FontSize: 28
  PrimaryColour: "&HFFFFFF&"    # White (BGR format)
  OutlineColour: "&H000000&"    # Black outline
  Outline: 2
  Shadow: 1
  Alignment: 2                   # Bottom center
  MarginV: 40
```

## Subtitle Style Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| Fontname | string | Font family name |
| FontSize | int | Font size in pixels |
| PrimaryColour | string | Text color (BGR: &HBBGGRR&) |
| OutlineColour | string | Outline color |
| BackColour | string | Background color |
| Outline | int | Outline width |
| Shadow | int | Shadow depth |
| Bold | int | Bold (0/1/-1) |
| Italic | int | Italic (0/1/-1) |
| Alignment | int | 1-9 (numpad layout) |
| MarginL/MarginR/MarginV | int | Margins in pixels |

## Caching System
- First run generates all content and saves `project.yaml` in output dir
- Subsequent runs compare MD5 hashes to skip unchanged content
- Set `force_reset: true` on specific items in `project.yaml` to force regeneration

## Output Files
After generation, the output directory contains:
- `output.mp4` - Final video with subtitles
- `subtitles_merged.srt` - Original merged subtitles from Whisper
- `subtitles_merged_proofread.srt` - Proofread subtitles (corrected against script)
- `sub_paragraph_*.mp4` - Individual slide video segments
- `sub_paragraph_*.wav` - Individual audio segments
- `sub_paragraph_*.srt` - Individual subtitle segments
- `project.yaml` - Cache state for incremental builds

## Language Support
Supported: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, hu, ko, ja, hi

## Dependencies
- **Core**: PyMuPDF (PDF), ffmpeg-python (video), coqui-tts (local TTS), pydub (audio), faster-whisper (subtitles), Pillow (image resize)
- **TTS runtime**: torchaudio (Coqui TTS dependency), transformers<5.1 (5.x breaks Coqui TTS)
- **System**: FFmpeg with libass (required for hard subtitles — `brew install ffmpeg-full` on macOS)
- **CLI**: Typer, Click
- **Dev**: pytest, pyright, ruff
