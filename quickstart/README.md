# Quick Start Guide

This folder contains example configurations to help you get started quickly.

## Files

| File | Description |
|------|-------------|
| `config-minimal.yaml` | Minimal configuration with only required fields |
| `config-full.yaml` | Full configuration with all options and style presets |
| `script-template.txt` | Template for narration scripts |

## Quick Start Steps

### Step 1: Prepare Your Files

1. **PDF Slides**: Create a PDF file with your slides (e.g., `my_slides.pdf`)
2. **Voice Sample**: Record 10-30 seconds of your voice (e.g., `sample.mp3`)
3. **Script**: Write your narration script (copy `script-template.txt` as a starting point)

### Step 2: Create Config

Copy `config-minimal.yaml` and edit the paths:

```yaml
model: local
slide: my_slides.pdf      # Your PDF file
script: script.txt        # Your script file
voice: sample.mp3         # Your voice sample
output_dir: output
```

### Step 3: Run

```bash
# Interactive mode (review subtitles before burning)
slide-to-video --config config-minimal.yaml

# Non-interactive mode (skip all prompts)
slide-to-video --config config-minimal.yaml --no-interactive
```

### Step 4: Check Output

Your output directory will contain:
- `output.mp4` - Final video with subtitles
- `subtitles_merged_proofread.srt` - Proofread subtitles
- `project.yaml` - Cache state (for faster rebuilds)

## Common Scenarios

### Scenario 1: Quick Test (Soft Subtitles)

Fast generation with toggleable subtitles:

```yaml
subtitle_mode: soft
no_interactive: true
```

### Scenario 2: Production Video (Hard Subtitles)

Burned-in subtitles for universal playback:

```yaml
subtitle_mode: hard
subtitle_style:
  Fontname: Arial
  FontSize: 28
  PrimaryColour: "&HFFFFFF&"
  OutlineColour: "&H000000&"
  Outline: 2
  Alignment: 2
  MarginV: 40
```

### Scenario 3: Chinese Content

Optimized for Chinese text:

```yaml
language: zh-cn
subtitle_style:
  Fontname: SimHei
  FontSize: 32
  PrimaryColour: "&HFFFFFF&"
  OutlineColour: "&H000000&"
  Outline: 2
  Alignment: 2
  MarginV: 50
```

### Scenario 4: Large Text for Presentations

Bigger text for better visibility:

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
Use hard subtitles for universal compatibility:
```yaml
subtitle_mode: hard
```
