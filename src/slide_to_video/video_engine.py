import os
import tempfile
from typing import List
import ffmpeg
from .utils import par_execute
from PIL import Image

def run_ffmpeg_command(command):
    command = command.global_args("-loglevel", "info")
    ffmpeg.run(command, overwrite_output=True)


class VideoEngine(object):
    """
    FFMPEG-based video utils.
    """

    # def generate_video_from_image(
    #     self, image_path: str, video_path: str, duration: float
    # ):
    #     print(f"Generating video from {image_path} with duration {duration}")
    #     # Load the image and set the duration
    #     input_image = ffmpeg.input(image_path, loop=1, t=duration, framerate=30)
    
    #     # 修正：scale 表达式作为一个字符串传递
    #     scaled = input_image.video.filter('scale', 'iw:-2')
    
    #     # Set the output file and parameters
    #     output = ffmpeg.output(
    #         scaled, video_path, vcodec="libx264", pix_fmt="yuv420p"
    #     )
    #     run_ffmpeg_command(output)
    

    def generate_video_from_image(
        self, image_path: str, video_path: str, duration: float
    ):
        print(f"Generating video from {image_path} with duration {duration}")
        
        # 使用 PIL 调整图片尺寸为偶数
        with Image.open(image_path) as img:
            width, height = img.size
            # 确保宽高都是偶数
            if width % 2 != 0:
                width -= 1
            if height % 2 != 0:
                height -= 1
            # 调整尺寸（使用高质量的 LANCZOS 重采样）
            img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
            # 保存到临时文件或覆盖原文件
            img_resized.save(image_path)
        
        # Load the image and set the duration
        input_image = ffmpeg.input(image_path, loop=1, t=duration, framerate=30)
    
        # Set the output file and parameters
        output = ffmpeg.output(
            input_image, video_path, vcodec="libx264", pix_fmt="yuv420p"
        )
        run_ffmpeg_command(output)

    def par_generate_video_from_image(
        self, image_paths: List[str], video_paths: List[str], durations: List[float]
    ):
        par_execute(self.generate_video_from_image, image_paths, video_paths, durations)

    # def concatenate_videos(self, video_paths: List[str], output_path: str):
    #     print(f"Concatenating videos {video_paths} into {output_path}")

    #     # Create a temporary file listing all video files
    #     with tempfile.NamedTemporaryFile(
    #         delete=False, mode="w", suffix=".txt"
    #     ) as temp_file:
    #         for video_path in video_paths:
    #             video_path = os.path.abspath(video_path)
    #             temp_file.write(f"file '{video_path}'\n")
    #         temp_file_path = temp_file.name

    #     # Concatenate videos using the concat demuxer
    #     output = ffmpeg.input(temp_file_path, format="concat", safe=0).output(
    #         output_path, c="copy"
    #     )
    #     run_ffmpeg_command(output)
    #     os.remove(temp_file_path)

    def concatenate_videos(self, video_paths: List[str], output_path: str):
        print(f"Concatenating videos {video_paths} into {output_path}")
    
        # Create a temporary file listing all video files
        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", suffix=".txt"
        ) as temp_file:
            for video_path in video_paths:
                video_path = os.path.abspath(video_path)
                temp_file.write(f"file '{video_path}'\n")
            temp_file_path = temp_file.name
    
        # Concatenate videos using the concat demuxer，重新编码以修复时间戳
        output = ffmpeg.input(temp_file_path, format="concat", safe=0).output(
            output_path, vcodec="libx264", acodec="aac"  # 改为重新编码
        )
        run_ffmpeg_command(output)
        os.remove(temp_file_path)
        # inputs = [ffmpeg.input(video_path) for video_path in video_paths]
        # output = ffmpeg.concat(*inputs, v=1, a=1).node
        # output = ffmpeg.output(output[0], output_path, vcodec="copy", acodec="copy")
        # run_ffmpeg_command(output)

        # Prepare the input streams
        # inputs = [ffmpeg.input(video_path) for video_path in video_paths]

        # Create a stream for concatenation
        # video_streams = [input.video for input in inputs]
        # audio_streams = [input.audio for input in inputs]

        # Concatenate video and audio streams
        # concatenated_video = ffmpeg.concat(*video_streams, v=1, a=0).node
        # concatenated_audio = ffmpeg.concat(*audio_streams, v=0, a=1).node

        # Combine the concatenated video and audio streams
        # output = ffmpeg.output(concatenated_video[0], concatenated_audio[1], output_path, vcodec='copy', acodec='copy')

        # Run the ffmpeg command
        # run_ffmpeg_command(output)

    def add_audio_to_video(self, video_path, audio_path, output_path):
        input_video = ffmpeg.input(video_path)
        input_audio = ffmpeg.input(audio_path)

        output = ffmpeg.output(
            input_video,
            input_audio,
            output_path,
            vcodec="copy",
            acodec="aac",
            strict="experimental",
        )

        run_ffmpeg_command(output)

    # def add_silence(self, input_file, duration: float = 2, direction="end"):
    #     # Get the suffix of the input file
    #     _, input_file_suffix = os.path.splitext(input_file)
    #     # Create a temporary file for the output
    #     with tempfile.NamedTemporaryFile(
    #         delete=False, suffix=input_file_suffix
    #     ) as temp_output_file:
    #         temp_output_file_name = temp_output_file.name

    #     try:
    #         # Generate 2 seconds of silence
    #         silence = ffmpeg.input(
    #             "anullsrc=channel_layout=5.1:sample_rate=48000", f="lavfi", t=duration
    #         )

    #         # Input audio file
    #         audio = ffmpeg.input(input_file)

    #         if direction == "end":
    #             output = ffmpeg.concat(audio, silence, v=0, a=1).output(
    #                 temp_output_file_name
    #             )
    #         elif direction == "start":
    #             output = ffmpeg.concat(silence, audio, v=0, a=1).output(
    #                 temp_output_file_name
    #             )
    #         else:
    #             raise ValueError(f"Invalid direction: {direction}")
    #         run_ffmpeg_command(output)

    #         os.replace(temp_output_file_name, input_file)
    #         print(f"Successfully added {duration} seconds of silence to {input_file}.")

    #     finally:
    #         # Clean up the temporary file if it still exists
    #         if os.path.exists(temp_output_file_name):
    #             os.remove(temp_output_file_name)

    def add_silence(self, input_file, duration: float = 2, direction="end"):
        # Get the suffix of the input file
        _, input_file_suffix = os.path.splitext(input_file)
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=input_file_suffix
        ) as temp_output_file:
            temp_output_file_name = temp_output_file.name
    
        try:
            # Input audio file（先读取，获取原始音频参数）
            audio = ffmpeg.input(input_file)
    
            # 生成单声道静音，采样率会自动匹配原始音频
            silence = ffmpeg.input("anullsrc=r=24000:cl=mono", f="lavfi", t=duration)
    
            if direction == "end":
                output = ffmpeg.concat(audio, silence, v=0, a=1).output(
                    temp_output_file_name
                )
            elif direction == "start":
                output = ffmpeg.concat(silence, audio, v=0, a=1).output(
                    temp_output_file_name
                )
            else:
                raise ValueError(f"Invalid direction: {direction}")
            run_ffmpeg_command(output)
    
            os.replace(temp_output_file_name, input_file)
            print(f"Successfully added {duration} seconds of silence to {input_file}.")
    
        finally:
            # Clean up the temporary file if it still exists
            if os.path.exists(temp_output_file_name):
                os.remove(temp_output_file_name)

    def add_subtitle_to_video_soft(
        self, 
        video_path: str, 
        srt_path: str, 
        output_path: str
    ):
        """
        添加软字幕（可切换，无画质损失）
        
        Args:
            video_path: 输入视频路径
            srt_path: SRT字幕文件路径
            output_path: 输出视频路径
        """
        print(f"Adding soft subtitle to {video_path}")
        
        input_video = ffmpeg.input(video_path)
        input_subtitle = ffmpeg.input(srt_path)
        
        # 流复制：速度极快，无画质损失
        # -c:s mov_text: MP4标准字幕格式
        output = ffmpeg.output(
            input_video,
            input_subtitle,
            output_path,
            **{
                'c:v': 'copy',      # 视频流复制
                'c:a': 'copy',      # 音频流复制
                'c:s': 'mov_text'   # 字幕流：MP4标准格式
            },
            movflags='+faststart'   # 优化网络播放
        )
        
        run_ffmpeg_command(output)
        print(f"Soft subtitle added to {output_path}")
    
    
    def burn_subtitles_to_video(
        self, 
        video_path: str, 
        srt_path: str, 
        output_path: str,
        font_size: int = 24
    ):
        """
        烧录字幕到视频（硬字幕）
        
        Args:
            video_path: 输入视频路径
            srt_path: SRT字幕文件路径
            output_path: 输出视频路径
            font_size: 字体大小
        """
        print(f"Burning subtitles to {video_path}")
        
        # 将SRT路径转换为FFmpeg可用的格式（转义路径中的特殊字符）
        import os
        # abs_srt_path = os.path.abspath(srt_path)
        rel_srt_path = os.path.relpath(srt_path)

        if os.name == 'nt':
            safe_srt_path = rel_srt_path.replace('\\', '/')
        else:
            safe_srt_path = rel_srt_path
        
        input_video = ffmpeg.input(video_path)
        
        # 使用subtitles滤镜
        subtitle_filter = input_video.filter(
            'subtitles',
            safe_srt_path,
            force_style=f'FontSize={font_size},PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Alignment=2,MarginV=30'
        )
        
        output = ffmpeg.output(
            subtitle_filter,        # 视频流（带字幕）
            input_video.audio,      # 音频流
            output_path,
            **{
                'vcodec': 'libx264',
                'acodec': 'aac',
                'crf': '23'
            }
        )
        
        run_ffmpeg_command(output)
        print(f"Subtitles burned to {output_path}")