# slide-to-video

A tool that converts a slide deck into a video, complete with your voice narration. Support multiple languages, subtitle generation, and interactive proofreading.

## Installation
Tested on Ubuntu 20.04 and Windows.

1. **Install `ffmpeg`**:
    - Ubuntu: `sudo apt-get install ffmpeg`
    - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
2. **Install Python (>=3.9 and <=3.11) and `pip`** if you haven't already.
3. **Clone and Install this Tool**:
    ```bash
    git clone git@github.com:llm-believer/slide-to-video.git
    cd slide-to-video
    pip install .
    ```
4. **Verify Installation**:
    ```bash
    slide-to-video
    ```

## Quick Start

### 1. Create a minimal config file (`config.yaml`):
```yaml
model: local
slide: my_slides.pdf
script: script.txt
voice: sample.mp3
output_dir: output
```

### 2. Prepare your files:
- `my_slides.pdf` - Your slide deck
- `script.txt` - Narration script with `NEWSLIDE` markers
- `sample.mp3` - Voice sample for cloning (10-30 seconds)

### 3. Run:
```bash
# Interactive mode (with subtitle confirmation)
slide-to-video --config config.yaml

# Non-interactive mode (skip all prompts)
slide-to-video --config config.yaml --no-interactive
```

Output: `output/output.mp4`

## Preparation
1. **Slide Deck**: Create a slide deck in PDF format.
2. **Script**: Prepare a script file in plain text format, with slides separated by the marker `NEWSLIDE`.
3. **Audio File or Model**: Record an audio file of your voice in MP3 format for voice cloning. If you use paid services like Play.ht, you should have a voice model available.

## Usage

### Configuration File (Recommended)
Create a `config.yaml` file with all required parameters:
```yaml
model: local
slide: example/slide.pdf
script: example/script.txt
voice: example/sample.mp3
output_dir: output
language: en
speech_speed: 1.0
delay: 2.0
enable_subtitle: true
subtitle_mode: soft  # "soft" or "hard"
```

Then run with:
```bash
slide-to-video --config config.yaml
```

### Command Line Usage
All CLI parameters are optional - they can be provided via config file or command line:
```bash
# Using only command line arguments
slide-to-video --model local --slide example/slide.pdf --script example/script.txt --voice example/sample.mp3 --output-dir output

# Using config file (recommended)
slide-to-video --config config.yaml

# Config file + override specific parameters
slide-to-video --config config.yaml --subtitle-mode hard --speech-speed 1.2

# Non-interactive mode (skip all prompts)
slide-to-video --config config.yaml --no-interactive
```

Command-line arguments override config file values.

## Subtitle Features

### Subtitle Modes
- **Soft subtitles** (`subtitle_mode: soft`): Subtitles are embedded as a separate track. Fast, no quality loss, can be toggled on/off in players.
- **Hard subtitles** (`subtitle_mode: hard`): Subtitles are burned into the video. Slower, but visible on all players and platforms.

### Interactive Proofreading
By default, the tool will:
1. Generate subtitles using Whisper
2. Proofread subtitles against your original script (correcting proper nouns, etc.)
3. Pause and ask you to confirm the proofread subtitles before burning

To skip the confirmation prompt:
```bash
slide-to-video --config config.yaml --no-interactive
```

Or in config:
```yaml
no_interactive: true
```

### Custom Subtitle Styles (Hard Mode Only)
Customize the appearance of burned-in subtitles:
```yaml
subtitle_mode: hard
subtitle_style:
  Fontname: Arial
  FontSize: 28
  PrimaryColour: "&HFFFFFF&"    # White text
  OutlineColour: "&H000000&"    # Black outline
  Outline: 2
  Shadow: 1
  Alignment: 2                   # Bottom center
  MarginV: 40
```

#### Available Style Parameters:
| Parameter | Description | Example |
|-----------|-------------|---------|
| Fontname | Font family | Arial, SimHei, Microsoft YaHei |
| FontSize | Font size in pixels | 24, 28, 32 |
| PrimaryColour | Text color (BGR format) | &HFFFFFF& (white), &H0000FF& (red) |
| OutlineColour | Outline color | &H000000& (black) |
| Outline | Outline width | 1, 2, 3 |
| Shadow | Shadow depth | 0, 1, 2 |
| Alignment | Position (1-9) | 2=bottom-center, 5=middle-center |
| MarginL/MarginR/MarginV | Margins in pixels | 10, 20, 30 |

#### Color Format:
Colors use BGR format: `&HBBGGRR&`
- White: `&HFFFFFF&`
- Black: `&H000000&`
- Red: `&H0000FF&`
- Green: `&H00FF00&`
- Blue: `&HFF0000&`
- Yellow: `&H00FFFF&`

### Example Usage
To use a local voice model:
```bash
slide-to-video --config example/config.yaml
```
A final video will be generated in the `output_dir` directory as `output.mp4`.

https://github.com/Changochen/slide-to-video/assets/18531282/c774367b-e585-4885-b13d-78940934a422


For more options, including adjusting speech speed, run:
```bash
slide-to-video --help
```

**Currently Supported Model**:
1. [TTS](https://github.com/coqui-ai/TTS)
2. [play.ht](https://play.ht/)

**Currently Supported Languages**:
'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'hu', 'ko', 'ja', 'hi'

## Cached Regeneration
After generating the video, the output directory will contain a `project.yaml` file, which helps skip the generation of unchanged content. If inputs remain the same, the tool skips the video generation process.

### Output Files
After generation, your output directory will contain:
- `output.mp4` - Final video with subtitles
- `subtitles_merged.srt` - Original merged subtitles
- `subtitles_merged_proofread.srt` - Proofread subtitles (corrected against script)
- `project.yaml` - Cache state for incremental builds

### To Force Regeneration
If you modify the slide, script, or settings (like speech speed), the tool regenerates the affected content. To force regeneration of specific parts, set the `force_reset` field of the corresponding item in `project.yaml` in the output directory.

### Support a new voice model
To support a new voice model, you need to implement a new class in `src/slide_to_video/tts_engine` and register the class by calling `register_engine` (See an example at [here](src/slide_to_video/tts_engine/local.py)).

## Notes
1. On the first run, you might see the following prompt:
    ```
    > You must confirm the following:
    | > "I have purchased a commercial license from Coqui: licensing@coqui.ai"
    | > "Otherwise, I agree to the terms of the non-commercial CPML: https://coqui.ai/cpml" - [y/n]
    | | >
    ```
    Simply enter `y`.
