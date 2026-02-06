import os

from .base_engine import TTSEngine
from .registery import register_engine


class LocalTTSEngine(TTSEngine):
    """
    Local TTS engine using Coqui TTS (XTTS v2) for voice synthesis.

    This engine runs locally and supports voice cloning using a voice sample.
    It uses the XTTS v2 model which supports multiple languages.
    """

    # Engine metadata
    ENGINE_NAME = "Local Coqui TTS"
    ENGINE_DESCRIPTION = "Local text-to-speech using Coqui TTS with voice cloning"
    REQUIRED_CONFIG_KEYS = {"voice"}
    OPTIONAL_CONFIG_KEYS = {"model_name"}
    SUPPORTED_LANGUAGES = {
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
    }
    SUPPORTED_FORMATS = {"wav"}

    def __init__(self, config: dict):
        """
        Initialize the Local TTS engine.

        Args:
            config: Configuration dictionary containing:
                - voice: Path to voice sample file (.wav, .mp3, etc.)
                - model_name: Optional TTS model name (default: XTTS v2)
                - speech_speed: Speech speed multiplier
                - language: Language code
        """
        super().__init__(**config)
        self.validate_config(config)

        self.tts = None
        self.voice_sample_path = config["voice"]
        self.model_name = config.get(
            "model_name", "tts_models/multilingual/multi-dataset/xtts_v2"
        )

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        """Synthesize text to speech using local Coqui TTS."""
        # Call parent to validate format
        super().synthesize(text, output_path, format)

        print(f"Generating audio file for text: {text} at speed {self.speed}")
        # self.get_tts().tts_to_file(
        #     text=text.strip(),
        #     speaker_wav=self.voice_sample_path,
        #     language=self.language,
        #     file_path=output_path,
        # )
       
        # 添加调试
        print(f"DEBUG: Text = '{text.strip()}'", flush=True)
        print(f"DEBUG: Voice sample path = '{self.voice_sample_path}'", flush=True)
        print(f"DEBUG: Language = '{self.language}'", flush=True)
        print(f"DEBUG: Output path = '{output_path}'", flush=True)
        print(f"DEBUG: Voice file exists = {os.path.exists(self.voice_sample_path)}", flush=True)
        
        tts_instance = self.get_tts()
        print(f"DEBUG: TTS instance type = {type(tts_instance)}")
        print(f"DEBUG: About to call tts_to_file...", flush=True)
        
        tts_instance.tts_to_file(
            text=text.strip(),
            speaker_wav=self.voice_sample_path,
            language=self.language,
            file_path=output_path,
        )
        
        print(f"Audio file generated and saved as {output_path}")

    def parallizable(self) -> bool:
        """Local TTS engine does not support parallel processing due to GPU memory constraints."""
        return False

    def get_tts(self):
        """Initialize and return the TTS engine instance."""
        if self.tts:
            return self.tts

        try:
            import torch
            from TTS.api import TTS
        except ImportError as e:
            raise RuntimeError(
                f"Coqui TTS not installed. Install with: pip install coqui-tts"
            ) from e

        # Get device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Initializing TTS on device: {device}")
        print(f"Model name: {self.model_name}")

        # # Initialize TTS with specified model
        # tts = TTS(self.model_name).to(device)
        # self.tts = tts
        # return tts

        # 添加调试
        print("Step 1: Creating TTS instance...")
        tts = TTS(self.model_name)
        print("Step 2: TTS instance created")
        
        print("Step 3: Moving to device...")
        tts = tts.to(device)
        print("Step 4: TTS moved to device")
        
        self.tts = tts
        print("Step 5: TTS assigned to self.tts")
        return tts


    def cleanup(self) -> None:
        """Clean up TTS resources."""
        if self.tts is not None:
            # Clear GPU memory if using CUDA
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            self.tts = None


register_engine("local", LocalTTSEngine)
