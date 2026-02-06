import concurrent.futures
from typing import List
import hashlib
import os
from pydub import AudioSegment
import logging

logger = logging.getLogger(__name__)


def par_execute(func, *args) -> List[concurrent.futures.Future]:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for arg in zip(*args):
            futures.append(executor.submit(func, *arg))

        concurrent.futures.wait(futures)
        for future in futures:
            future.result()

    return futures


def md5sum_of_file(filename) -> str:
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def exists(path) -> bool:
    return os.path.exists(path)


def get_audio_duration(audio_file):
    audio = AudioSegment.from_wav(audio_file)
    duration_seconds = len(audio) / 1000.0  # pydub calculates duration in milliseconds
    return duration_seconds

# ✨ 新增：Whisper对齐功能
def generate_srt_with_whisper(
    audio_path: str, 
    output_srt_path: str,
    model_size: str = "base",
    device: str = "auto"
) -> None:
    """
    使用faster-whisper生成带时间戳的SRT字幕文件
    
    Args:
        audio_path: 音频文件路径
        output_srt_path: 输出SRT文件路径
        model_size: Whisper模型大小 (tiny, base, small, medium, large)
        device: 设备类型 (cuda, cpu, auto)
    
    Note:
        - 对于TTS生成的清晰音频，base模型已经足够
        - device="auto"会自动选择GPU如果可用
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            "faster-whisper not installed. Install with: pip install faster-whisper"
        ) from e
    
    # 自动选择设备
    if device == "auto":
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
    
    logger.info(f"Initializing Whisper model (size={model_size}, device={device})...")
    model = WhisperModel(model_size, device=device, compute_type="float16" if device == "cuda" else "int8")
    
    logger.info(f"Transcribing audio: {audio_path}")
    # 启用词级时间戳
    segments, info = model.transcribe(
        audio_path, 
        word_timestamps=True,
        language=None  # 自动检测语言
    )
    
    detected_language = info.language
    logger.info(f"Detected language: {detected_language} (probability={info.language_probability:.2f})")
    
    # 生成SRT文件
    segment_count = 0
    with open(output_srt_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments):
            start_time = _format_timestamp(segment.start)
            end_time = _format_timestamp(segment.end)
            text = segment.text.strip()
            
            # 只写入非空片段
            if text:
                segment_count += 1
                srt_file.write(f"{segment_count}\n")
                srt_file.write(f"{start_time} --> {end_time}\n")
                srt_file.write(f"{text}\n\n")
    
    logger.info(f"Generated SRT with {segment_count} segments at {output_srt_path}")
 
 
def _format_timestamp(seconds: float) -> str:
    """
    将秒数转换为SRT时间格式 (HH:MM:SS,mmm)
    
    Args:
        seconds: 浮点秒数
    
    Returns:
        格式化的时间字符串，如 "00:01:23,456"
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - total_seconds) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
 
 
def merge_srt_files(
    srt_files: List[str],
    output_srt_path: str,
    time_offsets: List[float]
) -> None:
    """
    合并多个SRT文件，并调整时间轴
    
    Args:
        srt_files: SRT文件列表
        output_srt_path: 合并后的SRT文件路径
        time_offsets: 每个SRT文件的时间偏移量（秒）
    
    Note:
        time_offsets[i] 是 srt_files[i] 在总视频中的起始时间
    """
    import re
    
    def parse_srt_time(time_str):
        """解析SRT时间字符串为秒数"""
        h, m, s_ms = time_str.split(":")
        s, ms = s_ms.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    
    def format_srt_time(seconds):
        """将秒数格式化为SRT时间字符串"""
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - total_seconds) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    all_segments = []
    
    for srt_file, offset in zip(srt_files, time_offsets):
        if not os.path.exists(srt_file):
            logger.warning(f"SRT file not found: {srt_file}")
            continue
        
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析SRT片段
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([^\n]+)'
        matches = re.findall(pattern, content)
        
        for idx, start_str, end_str, text in matches:
            start = parse_srt_time(start_str) + offset
            end = parse_srt_time(end_str) + offset
            all_segments.append({
                'start': start,
                'end': end,
                'text': text.strip()
            })
    
    # 按时间排序
    all_segments.sort(key=lambda x: x['start'])
    
    # 写入合并后的SRT
    with open(output_srt_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(all_segments, 1):
            start = format_srt_time(seg['start'])
            end = format_srt_time(seg['end'])
            text = seg['text']
            
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
    
    logger.info(f"Merged {len(srt_files)} SRT files with {len(all_segments)} segments to {output_srt_path}")