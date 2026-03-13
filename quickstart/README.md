# Quick Start Guide

This folder contains example configurations to help you get started quickly.

## Files

| File | Description |
|------|-------------|
| `config-minimal.yaml` | Minimal config for PDF slides → video |
| `config-full.yaml` | Full config with all options and LLM examples |
| `config-from-doc.yaml` | Config for Markdown documentation → video |
| `script-template.txt` | Template for narration scripts |

## Quick Start: Two Ways to Create Videos

### Way 1: From PDF Slides (Traditional)

Best for: Existing presentations, slide decks

**Step 1**: Prepare your files
- `my_slides.pdf` - Your PDF slide deck
- `sample.mp3` - Voice sample (10-30 seconds)
- `script.txt` - Narration script (use `script-template.txt` as starting point)

**Step 2**: Create config

```yaml
# config.yaml
model: local
slide: my_slides.pdf
script: script.txt
voice: sample.mp3
output_dir: output
```

**Step 3**: Generate video

```bash
slide-to-video --config config.yaml
```

### Way 2: From Documentation (Recommended)

Best for: Technical docs, tutorials, knowledge base articles

**Step 1**: Prepare your documentation
- Markdown file with images (e.g., `guide.md`)
- Images in the same or nearby directory

**Step 2**: Create config

```yaml
# config_doc.yaml
doc_path: "docs/guide.md"
output_dir: "output"

llm:
  provider: glm           # or claude, qwen, kimi, ollama
  model: glm-4-flash
  # api_key: xxx          # Or set GLM_API_KEY env var

# Optional: Control script length
target_word_count: 800   # Keep script concise (null = no limit)
```

**Step 3**: Generate slides and script

```bash
slide-to-video from-doc --config config_doc.yaml
```

This automatically:
- Extracts images from your Markdown
- Selects the most important images using LLM
- Generates narration script for each image
- Each slide is aware of previous content (avoids repetition)
- Respects word count budget if specified
- Creates `slide.pdf` and `script.txt`

**Step 4**: Generate video

```bash
slide-to-video --config output/config.yaml
```

## LLM Provider Setup

### Option 1: Environment Variables (Recommended)

```bash
# GLM (智谱AI) - Free tier available
export GLM_API_KEY="your_api_key"

# Claude (Anthropic)
export ANTHROPIC_API_KEY="sk-ant-xxx"

# Qwen (通义千问)
export DASHSCOPE_API_KEY="xxx"

# Kimi (月之暗面)
export MOONSHOT_API_KEY="xxx"

# Ollama (Local) - No API key needed
ollama serve  # Start Ollama server
```

### Option 2: In Config File

```yaml
llm:
  provider: glm
  model: glm-4-flash
  api_key: "your_api_key"  # Not recommended for git repos
```

## Common Scenarios

### Scenario 1: Quick Test (Fast, Soft Subtitles)

```yaml
# config.yaml
model: local
slide: slides.pdf
script: script.txt
voice: sample.mp3
output_dir: output

subtitle_mode: soft
no_interactive: true
```

```bash
slide-to-video --config config.yaml
```

### Scenario 2: Production Video (Hard Subtitles)

```yaml
# config.yaml
model: local
slide: slides.pdf
script: script.txt
voice: sample.mp3
output_dir: output

subtitle_mode: hard
subtitle_style:
  Fontname: Arial
  FontSize: 28
  PrimaryColour: "&HFFFFFF&"
  OutlineColour: "&H000000&"
  Outline: 2
  Alignment: 2
  MarginV: 40

proofread:
  method: llm
  llm:
    provider: glm
    model: glm-4-flash
```

### Scenario 3: From Chinese Documentation

```yaml
# config_doc.yaml
doc_path: "docs/指南.md"
output_dir: "output"
language: zh-cn

llm:
  provider: glm
  model: glm-4-flash
```

### Scenario 4: Using Local Ollama (No API Key)

```yaml
# config_doc.yaml
doc_path: "docs/guide.md"
output_dir: "output"

llm:
  provider: ollama
  model: llama3.2
  api_url: http://localhost:11434
```

First, install and run Ollama:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download model
ollama pull llama3.2

# Run server
ollama serve
```

### Scenario 5: Claude for High-Quality Scripts

```yaml
# config_doc.yaml
doc_path: "docs/guide.md"
output_dir: "output"

llm:
  provider: claude
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  # api_key: sk-ant-xxx  # Or set ANTHROPIC_API_KEY env var
```

### Scenario 6: Concise Script with Word Count Control

```yaml
# config_doc.yaml
doc_path: "docs/guide.md"
output_dir: "output"

# Limit script to approximately 800 words
target_word_count: 800

llm:
  provider: glm
  model: glm-4-flash
```

With word count control:
- Each slide is aware of previous content (no repetition)
- Word budget is distributed across remaining slides
- Script stays within approximately ±10% of target
- Progress shows running word count: `Word count: 345/800`

## Output Files

After generation, your output directory contains:

| File | Description |
|------|-------------|
| `output.mp4` | Final video with subtitles |
| `slide.pdf` | Generated slides (from-doc only) |
| `script.txt` | Generated script (from-doc only) |
| `subtitles_merged.srt` | Original subtitles |
| `subtitles_merged_proofread.srt` | Corrected subtitles |
| `config.yaml` | Ready-to-use config for video generation |
| `project.yaml` | Cache for incremental builds |

## Subtitle Styling Examples

### Standard White Text
```yaml
subtitle_style:
  Fontname: Arial
  FontSize: 28
  PrimaryColour: "&HFFFFFF&"
  OutlineColour: "&H000000&"
  Outline: 2
  Alignment: 2
  MarginV: 40
```

### Large Text for Presentations
```yaml
subtitle_style:
  Fontname: Arial
  FontSize: 36
  PrimaryColour: "&HFFFFFF&"
  OutlineColour: "&H000000&"
  Outline: 3
  Alignment: 2
  MarginV: 60
```

### Chinese Subtitles
```yaml
subtitle_style:
  Fontname: SimHei
  FontSize: 32
  PrimaryColour: "&HFFFFFF&"
  OutlineColour: "&H000000&"
  Outline: 2
  Alignment: 2
  MarginV: 50
```

### Yellow Classic Style
```yaml
subtitle_style:
  Fontname: Arial
  FontSize: 28
  PrimaryColour: "&H00FFFF&"    # Yellow
  OutlineColour: "&H000000&"
  Outline: 2
  Alignment: 2
  MarginV: 40
```

## Troubleshooting

### "ffmpeg not found"
Install ffmpeg:
- Ubuntu: `sudo apt-get install ffmpeg`
- Windows: Download from ffmpeg.org and add to PATH

### "Coqui license prompt"
Enter `y` to accept the non-commercial license on first run.

### "CUDA out of memory"
Use a smaller Whisper model:
```yaml
whisper_model_size: tiny
```

### Subtitles not showing in player
Use hard subtitles:
```yaml
subtitle_mode: hard
```

### "Could not connect to Ollama"
Make sure Ollama is running:
```bash
ollama serve
```

### LLM API errors
1. Check your API key is correct
2. Verify the model name matches your provider
3. Check your API credits/quota

## Advanced Features

### Context-Aware Script Generation

When using `from-doc`, the script generator is context-aware:
- Each slide's narration considers previous content
- No repetitive information across slides
- More consistent storytelling flow

### Word Count Control

Set `target_word_count` in your config:
```yaml
target_word_count: 800  # Approximately 800 words total
```

Benefits:
- Keep your narration concise
- Word budget distributed across all slides
- Progress shows running count during generation
- Stays within ±10% of target

## Next Steps

1. Try the example configs in this folder
2. Customize subtitle styles for your needs
3. Experiment with different LLM providers
4. Set up environment variables for API keys
