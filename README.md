# slide-to-video

A powerful tool that converts slide decks and documentation into narrated videos. Supports multiple TTS engines, LLM providers, subtitle generation with proofreading, and 17+ languages.

## Features

- **Multiple Input Sources**: Convert PDF slides or Markdown documentation to video
- **Multi-LLM Support**: Choose from GLM, Claude, Qwen, Kimi, Ollama, or any OpenAI-compatible API
- **Context-Aware Script Generation**: Each slide's narration considers previous content to avoid repetition
- **Word Count Control**: Specify target word count for generated scripts
- **TTS Engines**: Local Coqui TTS, Play.ht, OpenAI TTS
- **17+ Languages**: English, Chinese, Spanish, French, German, Japanese, Korean, etc.
- **Smart Subtitles**: Whisper-based generation with LLM proofreading
- **Interactive Workflow**: Review and edit subtitles before finalizing
- **Custom Styling**: Full control over subtitle appearance

## Installation

Tested on Ubuntu 20.04, macOS, and Windows.

1. **Install FFmpeg (with libass for hard subtitles)**:

   > **Important**: The standard Homebrew/apt package may not include `libass`, which is required for the `subtitles` filter (hard subtitle mode).

   - **macOS**: `brew install ffmpeg-full` (Homebrew's `ffmpeg` lacks libass)
   - **Ubuntu**: `sudo apt-get install ffmpeg libass-dev`
   - **Windows**: Download a full build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (includes libass) and add to PATH

   Verify: `ffmpeg -filters | grep subtitles` should show `subtitles`.

2. **Install Python (>=3.9 and <=3.11)** and `pip` if you haven't already.

3. **Clone and Install**:
   ```bash
   git clone git@github.com:llm-believer/slide-to-video.git
   cd slide-to-video
   pip install .
   ```

   > **macOS 一键部署**: `bash tools/setup_mac.sh` (自动安装 ffmpeg-full、创建 venv、安装依赖)

4. **Verify Installation**:
   ```bash
   slide-to-video --help
   ```

## Quick Start

### Option 1: From PDF Slides (Traditional)

**Step 1**: Create a minimal config file (`config.yaml`):
```yaml
model: local
slide: my_slides.pdf
script: script.txt
voice: sample.mp3
output_dir: output
```

**Step 2**: Prepare your files:
- `my_slides.pdf` - Your slide deck
- `script.txt` - Narration script with `NEWSLIDE` markers
- `sample.mp3` - Voice sample for cloning (10-30 seconds)

**Step 3**: Run:
```bash
slide-to-video --config config.yaml
```

### Option 2: From Documentation (Recommended)

**Step 1**: Create a config file (`config_doc.yaml`):
```yaml
doc_path: "docs/guide.md"
output_dir: "output"

llm:
  provider: glm
  model: glm-4-flash
  # api_key: xxx  # Or set GLM_API_KEY environment variable
```

**Step 2**: Run:
```bash
slide-to-video from-doc --config config_doc.yaml
```

This will:
1. Extract images from your Markdown documentation
2. Use LLM to select the most important images
3. Generate narration script for each slide
4. Create `slide.pdf` and `script.txt` ready for video generation

**Step 3**: Generate the video:
```bash
slide-to-video --config output/config.yaml
```

## Commands Reference

### `slide-to-video` (or `slide-to-video generate`)

Convert PDF slides + script to video with narration and subtitles.

```bash
# Basic usage
slide-to-video --config config.yaml

# Override specific options
slide-to-video --config config.yaml --subtitle-mode hard --speech-speed 1.2

# Non-interactive mode
slide-to-video --config config.yaml --no-interactive
```

### `slide-to-video from-doc`

Convert Markdown documentation to slide PDF and script.

```bash
# Basic usage
slide-to-video from-doc --config config_doc.yaml

# Specify document directly
slide-to-video from-doc --doc-path docs/guide.md --output-dir output

# Skip LLM image selection (use all images)
slide-to-video from-doc --config config_doc.yaml --skip-selection

# Set target word count for script generation
slide-to-video from-doc --config config_doc.yaml --target-word-count 800
```

## LLM Provider Configuration

### Supported Providers

| Provider | Provider Name | Env Variable | Default Model |
|----------|--------------|--------------|---------------|
| GLM (智谱AI) | `glm` | `GLM_API_KEY` | `glm-4-flash` |
| Claude (Anthropic) | `claude` | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` |
| Qwen (通义千问) | `qwen` | `DASHSCOPE_API_KEY` | `qwen-turbo` |
| Kimi (月之暗面) | `kimi` | `MOONSHOT_API_KEY` | `moonshot-v1-8k` |
| Ollama (Local) | `ollama` | - | `llama3.2` |
| OpenAI-Compatible | `openai-compatible` | - | `gpt-4o` |

### Configuration Examples

#### For `from-doc` Command (Image Selection & Script Generation)

```yaml
# config_doc.yaml
doc_path: "docs/guide.md"
output_dir: "output"

llm:
  provider: glm
  model: glm-4-flash
  temperature: 0.7
```

#### For `generate` Command (Subtitle Proofreading)

```yaml
# config.yaml
model: local
slide: slide.pdf
script: script.txt
output_dir: output

proofread:
  method: llm  # or "vocabulary" for word-level matching
  llm:
    provider: glm
    model: glm-4-flash
    temperature: 0.1  # Lower for more deterministic output
```

### Provider-Specific Examples

```yaml
# GLM (智谱AI) - Free tier available
llm:
  provider: glm
  model: glm-4-flash
  # api_key: xxx  # Uses GLM_API_KEY env var

# Claude (Anthropic)
llm:
  provider: claude
  model: claude-3-5-sonnet-20241022
  # api_key: sk-ant-xxx  # Uses ANTHROPIC_API_KEY env var

# Qwen (通义千问)
llm:
  provider: qwen
  model: qwen-turbo
  # api_key: xxx  # Uses DASHSCOPE_API_KEY env var

# Kimi (月之暗面)
llm:
  provider: kimi
  model: moonshot-v1-8k
  # api_key: xxx  # Uses MOONSHOT_API_KEY env var

# Ollama (Local Models - No API Key Required)
llm:
  provider: ollama
  model: llama3.2
  api_url: http://localhost:11434  # Optional, default is localhost

# OpenAI-Compatible (Generic API)
llm:
  provider: openai-compatible
  model: gpt-4o
  api_url: https://api.example.com/v1/chat/completions
  api_key: xxx
```

## Full Configuration Reference

### generate Command (PDF → Video)

```yaml
# === REQUIRED ===
model: local                    # TTS engine: local, playht, openai-tts
slide: my_slides.pdf            # PDF slide deck
script: script.txt              # Narration script
output_dir: output              # Output directory

# === TTS SETTINGS ===
voice: sample.mp3               # Voice sample for cloning (local engine)
language: en                    # Language code
speech_speed: 1.0               # Speed multiplier (0.5-2.0)
delay: 2.0                      # Seconds between slides

# === SUBTITLE SETTINGS ===
enable_subtitle: true           # Enable subtitle generation
subtitle_mode: soft             # "soft" (muxed) or "hard" (burned in)
whisper_model_size: base        # tiny, base, small, medium, large
no_interactive: false           # Skip all interactive prompts

# === SUBTITLE PROOFREADING ===
proofread:
  method: llm                   # "vocabulary" or "llm"
  llm:
    provider: glm
    model: glm-4-flash
    temperature: 0.1

# === SUBTITLE STYLE (hard mode only) ===
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

### from-doc Command (Markdown → Slides + Script)

```yaml
# === REQUIRED ===
doc_path: "docs/guide.md"       # Markdown documentation
output_dir: "output"            # Output directory

# === IMAGE SETTINGS ===
image_dir: "docs/images"        # Image directory (defaults to doc_path directory)
max_slides: 30                  # Maximum number of slides
skip_selection: false           # Skip LLM image selection

# === LLM SETTINGS ===
llm:
  provider: glm
  model: glm-4-flash
  temperature: 0.7

# === OUTPUT SETTINGS ===
language: en                    # Script language
page_width: 1920                # PDF page width
page_height: 1080               # PDF page height
last_slide_delay: 4.0           # Delay after last slide

# === SCRIPT GENERATION ===
target_word_count: null         # Target word count (optional, null = no limit)
                              # When set, each slide is aware of previous content
                              # and the script stays within the word budget.
```

## Subtitle Features

### Subtitle Modes

| Mode | Description | Pros | Cons |
|------|-------------|------|------|
| `soft` | Subtitles as separate track | Fast, toggleable, no quality loss | Not visible on all players |
| `hard` | Burned into video | Universal compatibility | Slower, permanent |

### Subtitle Proofreading

Two methods available:

1. **Vocabulary-based** (default, no API needed):
   ```yaml
   proofread:
     method: vocabulary
   ```

2. **LLM-based** (more accurate, requires API):
   ```yaml
   proofread:
     method: llm
     llm:
       provider: glm
       model: glm-4-flash
   ```

### Custom Subtitle Styles

```yaml
subtitle_mode: hard
subtitle_style:
  Fontname: Arial
  FontSize: 28
  PrimaryColour: "&HFFFFFF&"    # White text
  OutlineColour: "&H000000&"    # Black outline
  Outline: 2
  Shadow: 1
  Alignment: 2                   # Position (1-9 numpad layout)
  MarginV: 40
```

**Color Format**: BGR - `&HBBGGRR&`
- White: `&HFFFFFF&`
- Black: `&H000000&`
- Red: `&H0000FF&`
- Green: `&H00FF00&`
- Blue: `&HFF0000&`
- Yellow: `&H00FFFF&`

## Script Format & Context-Aware Generation

Scripts use `NEWSLIDE` markers to separate content:

```
NEWSLIDE
Narration for slide 1 goes here.

NEWSLIDE
Narration for slide 2 goes here.

NEWSLIDE
Final slide narration.
===
#delay: 4.0
```

Per-slide configuration with `===`:
```
NEWSLIDE
This slide needs extra time.
===
#delay: 5.0
```

### Context-Aware Script Generation

When using the `from-doc` command, the script generator now supports:

### Word Count Control

Set a target word count to keep your narration concise:

```yaml
# config_doc.yaml
target_word_count: 800  # Target approximately 800 words total
```

The generator:
- Distributes the word budget evenly across remaining slides
- Communicates the per-slide budget to the LLM
- Stays within approximately ±10% of the target

### Context Accumulation

Each slide's narration is generated with awareness of previous content:

- Shows the full narration from the most recent slide
- Shows previews (first 150 chars) of older slides
- Instructs the LLM to avoid repetition
- Summarizes older slides if context exceeds 2500 characters

This results in:
- More consistent storytelling flow
- No repeated content across slides
- Better overall narrative coherence

Example output when word count is enabled:
```
[1/5] Generating narration for slide 1/5...
[1/5]   Word count: 45/800
[2/5] Generating narration for slide 2/5...
[2/5]   Word count: 92/800
[3/5] Generating narration for slide 3/5...
[3/5]   Word count: 138/800
...
```

```
NEWSLIDE
Narration for slide 1 goes here.

NEWSLIDE
Narration for slide 2 goes here.

NEWSLIDE
Final slide narration.
===
#delay: 4.0
```

Per-slide configuration with `===`:
```
NEWSLIDE
This slide needs extra time.
===
#delay: 5.0
```

## Output Files

After generation, your output directory contains:

| File | Description |
|------|-------------|
| `output.mp4` | Final video with subtitles |
| `slide.pdf` | Generated slides (from-doc only) |
| `script.txt` | Generated script (from-doc only) |
| `subtitles_merged.srt` | Original merged subtitles |
| `subtitles_merged_proofread.srt` | Proofread subtitles |
| `project.yaml` | Cache state for incremental builds |

## Caching & Incremental Builds

The tool caches generated content in `project.yaml`:
- Skips unchanged slides and audio
- Automatically regenerates when inputs change
- Set `force_reset: true` in `project.yaml` to force regeneration

## Supported Languages

`en`, `es`, `fr`, `de`, `it`, `pt`, `pl`, `tr`, `ru`, `nl`, `cs`, `ar`, `zh-cn`, `hu`, `ko`, `ja`, `hi`

## Supported TTS Engines

| Engine | Model Name | Description |
|--------|------------|-------------|
| Coqui TTS | `local` | Free, runs locally, voice cloning |
| Play.ht | `playht` | Cloud service, high quality |
| OpenAI TTS | `openai-tts` | OpenAI's TTS API |

## Troubleshooting

### "ffmpeg not found"
Install ffmpeg:
- macOS: `brew install ffmpeg-full`
- Ubuntu: `sudo apt-get install ffmpeg libass-dev`
- Windows: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (full build with libass)

### "No option name near" / "Error parsing filterchain" (hard subtitles)
This usually means FFmpeg was compiled **without libass**:
```bash
ffmpeg -filters | grep subtitles
# If empty, reinstall FFmpeg with libass support
```

### "CUDA out of memory"
Use a smaller Whisper model:
```yaml
whisper_model_size: tiny
```

### Subtitles not showing in player
Use hard subtitles for universal compatibility:
```yaml
subtitle_mode: hard
```

### LLM API errors
1. Check your API key is set correctly
2. Verify the model name is valid for your provider
3. For Ollama, ensure Ollama is running: `ollama serve`

## Examples

See the `example/` and `quickstart/` directories for sample configurations.

```bash
# Run example
slide-to-video --config example/config.yaml

# Quick start
slide-to-video --config quickstart/config-minimal.yaml
```

## License

This project uses Coqui TTS which requires license confirmation for commercial use. See [CPML](https://coqui.ai/cpml) for details.

## Contributing

### Adding a New TTS Engine

1. Create a new file in `src/slide_to_video/tts_engine/`
2. Inherit from `TTSEngine` base class
3. Call `register_engine("name", EngineClass)`
4. The engine will auto-appear in CLI

### Adding a New LLM Provider

1. Create a new file in `src/slide_to_video/llm_client/`
2. Inherit from `LLMClient` base class
3. Implement `chat()` method
4. Call `register_provider("name", ClientClass)`
