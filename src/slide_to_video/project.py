from __future__ import annotations
import enum
from multiprocessing import Manager

from .utils import md5sum_of_file, exists, get_audio_duration, generate_srt_with_whisper
import yaml
from .slide_engine import SlideEngine
from .script_engine import ScriptEngine
from .tts_engine import TTSEngine, create_engine
from .video_engine import VideoEngine
import concurrent.futures

import json
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class TargetVoice:
    def __init__(self, *, model=None, audio=None):
        self.model = model
        self.audio = audio


class ItemType(enum.Enum):
    SLIDE = "slide"
    SCRIPT = "script"
    VOICE = "voice"
    VIDEO = "video"


class Item:
    def __init__(
        self, *, path, type, extra=None, md5sum=None, cached=False, force_reset=False
    ):
        self.path = path
        self.type = type
        self.cached = cached
        if not md5sum:
            md5sum = md5sum_of_file(path)
        self.md5sum = md5sum
        if extra:
            extra = dict(extra)
        self.extra = extra
        self.force_reset = force_reset

    def reset(self):
        self.cached = False

    @property
    def content(self):
        with open(self.path, "r", encoding="utf-8") as f:
            return f.read()

    def __eq__(self, other: object):
        if not isinstance(other, Item):
            return False
        return self.md5sum == other.md5sum and self.extra == other.extra

    def cache(self):
        self.cached = True

    @staticmethod
    def from_yaml(data) -> Item:
        return Item(
            path=data["path"],
            type=ItemType(data["type"]),
            cached=data["cached"],
            md5sum=data["md5sum"],
            force_reset=data.get("force_reset", False),
            extra=data.get("extra", None),
        )

    def to_yaml(self):
        result = {
            "path": self.path,
            "type": self.type.value,
            "cached": self.cached,
            "md5sum": self.md5sum,
            "force_reset": self.force_reset,
        }
        if self.extra:
            result["extra"] = self.extra
        return result


class Task(object):
    def __init__(
        self,
        *,
        id,
        slide: Item,
        script: Item,
        output_dir,
        tts_engine: TTSEngine,
        delay: float,
        lock=None,
    ):
        self.id = id
        self.slide = slide
        self.script = script
        self.output_dir = output_dir
        self.tts_engine = tts_engine
        self.lock = lock
        self.delay = delay
        self.srt_path = None  # 新增：存储生成的SRT路径
    
    def build(self):
        video_file = f"{self.output_dir}/sub_paragraph_without_sound_{self.id}.mp4"
        audio_file = f"{self.output_dir}/sub_paragraph_{self.id}.wav"
        srt_file = f"{self.output_dir}/sub_paragraph_{self.id}.srt"  # 新增：SRT文件路径
        final_video_file = f"{self.output_dir}/sub_paragraph_{self.id}.mp4"

        # if self.script.cached and self.slide.cached:
        #     return

        # if not self.script.cached:
        #     if self.lock:
        #         self.lock.acquire()
        #     self.tts_engine.synthesize(self.script.content, audio_file)
        #     if self.lock:
        #         self.lock.release()
 
        if self.script.cached and self.slide.cached:
            # 如果缓存存在，检查SRT是否也存在
            if os.path.exists(srt_file):
                self.srt_path = srt_file
            return
 
        if not self.script.cached:
            if self.lock:
                self.lock.acquire()
            
            # 生成音频（使用原有逻辑）
            self.tts_engine.synthesize(self.script.content, audio_file)
            
            if self.lock:
                self.lock.release()
            
            # ✨ 新增：使用Whisper生成带时间戳的SRT
            try:
                whisper_model_size = self.tts_engine._config.get("whisper_model_size", "base")
                generate_srt_with_whisper(
                    audio_path=audio_file,
                    output_srt_path=srt_file,
                    model_size=whisper_model_size,  # 可配置
                    device="auto"
                )
                self.srt_path = srt_file
                logger.info(f"Generated SRT with Whisper for paragraph {self.id}")
            except Exception as e:
                logger.warning(f"Failed to generate SRT with Whisper: {e}")
                # 失败时不中断流程，只是没有字幕
                self.srt_path = None
                
        video_engine = VideoEngine()
        if self.id != 1:
            video_engine.add_silence(audio_file, self.delay / 2, direction="start")
        end_delay = self.delay / 2
        if self.script.extra:
            end_delay = self.script.extra.get("delay", end_delay)
        video_engine.add_silence(audio_file, end_delay, direction="end")

        duration = get_audio_duration(audio_file)

        if not self.slide.cached or self.script.cached:
            video_engine.generate_video_from_image(
                self.slide.path, video_file, duration
            )
            video_engine.add_audio_to_video(video_file, audio_file, final_video_file)


class ProjectConfig(dict):
    def __init__(self, config):
        super().__init__()
        skip_keywords = ["config"]
        for key, value in config.items():
            if key not in skip_keywords:
                self[key] = value
        self.validate()

    def as_dict(self):
        return dict(self)

    def validate(self):
        required_fields = [
            "model",
            "slide",
            "script",
            "output_dir",
            "speech_speed",
            "delay",
        ]

        for field in required_fields:
            if field not in self.keys():
                raise ValueError(f"Missing required field {field}")


class Project:
    def __init__(
        self,
        *,
        name,
        config: ProjectConfig,
        from_file=False,
    ):
        self.name = name
        self.slide = config["slide"]
        self.script = config["script"]
        self.output_dir = config["output_dir"]
        self.config = config
        self.slide_items = []
        self.script_items = []
        self.speech_speed = config["speech_speed"]

        if not from_file:
            self.calculate_items()
            project_file = f"{self.output_dir}/project.yaml"
            previous_project = self.load_project_file(project_file)
            if previous_project:
                self.sync_project(previous_project)

    def all_reset(self):
        for item in self.slide_items:
            item.reset()
        for item in self.script_items:
            item.reset()

    def sync_project(self, previous_project: Project):
        if (
            self.config.as_dict() != previous_project.config.as_dict()
            or self.speech_speed != previous_project.speech_speed
            or len(self.slide_items) != len(previous_project.slide_items)
        ):
            self.all_reset()
            return

        for i in range(len(self.slide_items)):
            self.slide_items[i].force_reset = previous_project.slide_items[
                i
            ].force_reset
            self.script_items[i].force_reset = previous_project.script_items[
                i
            ].force_reset
            if (
                self.slide_items[i] == previous_project.slide_items[i]
                and not previous_project.slide_items[i].force_reset
            ):
                self.slide_items[i].cached = True
            if (
                self.script_items[i] == previous_project.script_items[i]
                and not previous_project.script_items[i].force_reset
            ):
                self.script_items[i].cached = True

    def calculate_items(self):
        slide_engine = SlideEngine()
        images = slide_engine.slide_to_images(self.slide, self.output_dir)
        sorted_images = sorted(images)
        self.slide_items = [
            Item(path=image, type=ItemType.SLIDE) for image in sorted_images
        ]
        self.script_items = [
            Item(path=script.path, type=ItemType.SCRIPT, extra=script.config)
            for script in ScriptEngine().split_script(
                self.script,
                self.output_dir,
                script_dict=self.config.get("script_dict", None),
            )
        ]

        assert len(self.slide_items) == len(self.script_items)

    def load_project_file(self, project_file):
        if exists(project_file):
            with open(project_file, "r", encoding="utf-8") as f:
                project_data = yaml.safe_load(f)

                slide = project_data.get("slide")
                script = project_data.get("script")
                output_dir = project_data.get("output_dir")
                config = project_data.get("config")
                speech_speed = project_data.get("speech_speed")
                slide_items = []
                for slide_item in project_data.get("slide_items"):
                    slide_items.append(Item.from_yaml(slide_item))
                script_items = []
                for script_item in project_data.get("script_items"):
                    script_items.append(Item.from_yaml(script_item))

                config["slide"] = slide
                config["script"] = script
                config["output_dir"] = output_dir
                config["speech_speed"] = speech_speed
                project_config = ProjectConfig(config)

                project = Project(
                    name=self.name,
                    config=project_config,
                    from_file=True,
                )

                project.slide_items = slide_items
                project.script_items = script_items

                return project

        return None

    def to_yaml(self):
        # Create a yaml representation of the project
        return {
            "name": self.name,
            "slide": self.slide,
            "script": self.script,
            "output_dir": self.output_dir,
            "speech_speed": self.speech_speed,
            "config": self.config.as_dict(),
            "slide_items": [slide_item.to_yaml() for slide_item in self.slide_items],
            "script_items": [
                script_item.to_yaml() for script_item in self.script_items
            ],
        }

    def save(self):
        project_file = f"{self.output_dir}/project.yaml"
        with open(project_file, "w") as f:
            yaml.dump(self.to_yaml(), f, sort_keys=False)

    def get_images(self, filter_cached=False):
        if filter_cached:
            return [item.path for item in self.slide_items if not item.cached]
        return [item.path for item in self.slide_items]

    def get_scripts(self, filter_cached=False):
        if filter_cached:
            return [item.content for item in self.script_items if not item.cached]
        return [item.content for item in self.script_items]

    def prompt_user_confirmation(self, proofread_srt_path: str) -> bool:
        """
        Prompt user to check proofread subtitles.

        - Shows subtitle file path
        - Waits for user confirmation
        - Returns whether to continue

        Args:
            proofread_srt_path: Path to the proofread SRT file

        Returns:
            True if user confirms, False otherwise
        """
        print("\n" + "=" * 60)
        print("Subtitle Proofreading Complete")
        print("=" * 60)
        print(f"\nProofread subtitle file saved to:")
        print(f"  {proofread_srt_path}")
        print("\nPlease review the file to verify corrections.")
        print("You can edit the file manually if needed.")
        print("=" * 60)

        while True:
            response = input("\nContinue with video generation? [Y/n]: ").strip().lower()
            if response in ['y', 'yes', '']:
                return True
            elif response in ['n', 'no']:
                print("Aborting. You can re-run after making changes.")
                return False
            else:
                print("Please enter 'y' or 'n'.")

    def process_subtitles(
        self,
        tasks: List[Task],
        video_engine: VideoEngine,
        final_output: str
    ) -> Optional[str]:
        """
        Handle subtitle generation and proofreading workflow.

        - Generates subtitles_merged.srt
        - Calls proofread module to generate subtitles_merged_proofread.srt
        - If enable_interactive=True, waits for user confirmation
        - Returns the final SRT path to use

        Args:
            tasks: List of completed Task objects
            video_engine: VideoEngine instance
            final_output: Path to the final output video

        Returns:
            Path to the final SRT file to use, or None if no subtitles
        """
        from .utils import get_audio_duration, merge_srt_files
        from .proofread import proofread_srt
        from .subtitle_config import get_subtitle_style

        # Check if subtitles are enabled
        enable_subtitle = self.config.get("enable_subtitle", True)
        if not enable_subtitle:
            print("Subtitle generation disabled by config")
            return None

        # Collect all SRT files and time offsets
        srt_files = []
        time_offsets = []
        current_time = 0.0

        for i, task in enumerate(tasks):
            if task.srt_path and os.path.exists(task.srt_path):
                srt_files.append(task.srt_path)

                # Calculate time offset for current segment
                start_silence = 0.0
                if task.id != 1:
                    start_silence = self.config["delay"] / 2

                time_offsets.append(current_time + start_silence)

                # Calculate next segment start time
                audio_file = f"{self.output_dir}/sub_paragraph_{i + 1}.wav"
                if os.path.exists(audio_file):
                    duration = get_audio_duration(audio_file)
                    current_time += duration

        if not srt_files:
            print("No subtitle files generated, skipping subtitle processing")
            return None

        # Merge all SRT files
        merged_srt_path = f"{self.output_dir}/subtitles_merged.srt"
        merge_srt_files(srt_files, merged_srt_path, time_offsets)
        print(f"Merged subtitles saved to: {merged_srt_path}")

        # Proofread the merged SRT
        proofread_srt_path = f"{self.output_dir}/subtitles_merged_proofread.srt"
        proofread_method = self.config.get("proofread", {}).get("method", "vocabulary")

        try:
            if proofread_method == "llm":
                # LLM-based proofreading
                llm_config = self.config.get("proofread", {}).get("llm", {})
                from .proofread import proofread_srt_with_llm
                proofread_srt_with_llm(
                    srt_path=merged_srt_path,
                    script_path=self.script,
                    output_path=proofread_srt_path,
                    model=llm_config.get("model"),
                    api_key=llm_config.get("api_key"),
                    temperature=llm_config.get("temperature", 0.1),
                )
            else:
                # Vocabulary-based proofreading (default)
                proofread_srt(
                    srt_path=merged_srt_path,
                    script_path=self.script,
                    output_path=proofread_srt_path
                )
            print(f"Proofread subtitles saved to: {proofread_srt_path}")
        except Exception as e:
            logger.warning(f"Proofreading failed, using original subtitles: {e}")
            proofread_srt_path = merged_srt_path

        # Check for interactive mode
        no_interactive = self.config.get("no_interactive", False)
        enable_interactive = self.config.get("enable_interactive", True)

        if enable_interactive and not no_interactive:
            if not self.prompt_user_confirmation(proofread_srt_path):
                raise RuntimeError("User cancelled the process")

        # Get subtitle style for hard burn mode
        subtitle_mode = self.config.get("subtitle_mode", "soft")
        style_config = None

        if subtitle_mode == "hard":
            style_config = get_subtitle_style(self.config, no_interactive)
            logger.info(f"Using subtitle style: {style_config}")

        # Apply subtitles to video
        output_with_subs = f"{self.output_dir}/output_with_subs.mp4"

        if subtitle_mode == "soft":
            video_engine.add_subtitle_to_video_soft(
                final_output, proofread_srt_path, output_with_subs
            )
        else:
            video_engine.burn_subtitles_to_video(
                final_output, proofread_srt_path, output_with_subs, style_config
            )

        # Replace original output
        os.replace(output_with_subs, final_output)
        print(f"Final video with {'soft' if subtitle_mode == 'soft' else 'hard'} subtitles saved to {final_output}")

        return proofread_srt_path

    def build(self):
        model = self.config.get("model")
        assert model
        tts_engine = create_engine(model, self.config)
        lock = None
        if not tts_engine.parallizable():
            manager = Manager()
            lock = manager.Lock()
        futures = []
        print(f"DEBUG: Building {len(self.slide_items)} slides...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            tasks = []
            for i in range(len(self.slide_items)):
                task = Task(
                    id=i + 1,
                    slide=self.slide_items[i],
                    script=self.script_items[i],
                    output_dir=self.output_dir,
                    tts_engine=tts_engine,
                    lock=lock,
                    delay=self.config["delay"],
                )
                tasks.append(task)
                futures.append(executor.submit(task.build))

        for future in futures:
            future.result()

        print("DEBUG: All slide tasks completed")
        cached_script_list = [item.cached for item in self.script_items]
        cached_slide_list = [item.cached for item in self.slide_items]
        print(f"DEBUG: cached_script_list = {cached_script_list}")
        print(f"DEBUG: cached_slide_list = {cached_slide_list}")

        if not all(cached_script_list) or not all(cached_slide_list):
            print("DEBUG: Starting video concatenation...")
            video_engine = VideoEngine()
            video_paths = [
                f"{self.output_dir}/sub_paragraph_{i + 1}.mp4"
                for i in range(len(self.slide_items))
            ]
            final_output = f"{self.output_dir}/output.mp4"
            print(f"DEBUG: Video paths = {video_paths}")
            print(f"DEBUG: Final output = {final_output}")

            video_engine.concatenate_videos(video_paths, final_output)
            print("DEBUG: Video concatenation completed")

            # Process subtitles with proofreading and interactive confirmation
            self.process_subtitles(tasks, video_engine, final_output)
            print("DEBUG: Subtitle processing completed")
        else:
            print("All items are cached. No need to build the project.")

