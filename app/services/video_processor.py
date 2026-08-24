import subprocess
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import tempfile

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, output_dir: str = "/tmp/youtube-clipper/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_clip(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        subtitle_path: Optional[str] = None,
        aspect_ratio: str = "9:16",
        subtitle_language: str = "id",
        clip_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if clip_id is None:
            clip_id = str(uuid.uuid4())[:8]

        output_path = str(self.output_dir / f"{clip_id}.mp4")
        duration = end_time - start_time

        cmd = self._build_ffmpeg_command(
            audio_path=audio_path,
            output_path=output_path,
            start_time=start_time,
            duration=duration,
            aspect_ratio=aspect_ratio,
            subtitle_path=subtitle_path
        )

        logger.info(f"Running ffmpeg: {' '.join(cmd[:8])}...")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"ffmpeg error: {result.stderr}")
            raise RuntimeError(f"ffmpeg failed: {result.stderr[:500]}")

        size = os.path.getsize(output_path)

        return {
            "output_path": output_path,
            "duration": duration,
            "size_bytes": size
        }

    def _build_ffmpeg_command(
        self,
        audio_path: str,
        output_path: str,
        start_time: float,
        duration: float,
        aspect_ratio: str = "9:16",
        subtitle_path: Optional[str] = None
    ) -> list:
        """Build ffmpeg command: black background video + trimmed audio + burned subtitles."""

        # Parse aspect ratio - lower resolution saves RAM
        if aspect_ratio == "9:16":
            width, height = 480, 854
        elif aspect_ratio == "16:9":
            width, height = 854, 480
        else:
            width, height = 480, 854

        # -ss/-t on the audio input handle trimming (no atrim needed)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time), "-t", str(duration), "-i", audio_path,
            "-f", "lavfi", "-t", str(duration), "-i", f"color=c=black:s={width}x{height}:r=25",
            "-map", "1:v", "-map", "0:a",
        ]

        # Burn subtitles onto the black background video stream
        if subtitle_path and os.path.exists(subtitle_path):
            style = "FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,Bold=1,Alignment=2,MarginV=40"
            # Escape path for ffmpeg filter
            safe_path = subtitle_path.replace(":", "\\:")
            cmd += ["-vf", f"subtitles='{safe_path}':charenc=utf-8:force_style='{style}'"]

        cmd += [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "30",
            "-c:a", "aac",
            "-b:a", "64k",
            "-shortest",
            "-movflags", "+faststart",
            output_path,
        ]

        return cmd

    def extract_segment_srt(self, full_srt: str, start: float, end: float) -> str:
        """Extract subtitle lines within time range and re-index them."""
        import re
        
        blocks = re.split(r'\n\n+', full_srt.strip())
        result_blocks = []
        new_index = 1
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            try:
                # Parse timestamp
                time_line = lines[1]
                match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', time_line)
                if not match:
                    continue
                start_str, end_str = match.groups()
                
                def parse_ts(ts):
                    parts = ts.replace(',', '.').split(':')
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                
                block_start = parse_ts(start_str)
                block_end = parse_ts(end_str)
                
                # Include if overlaps with segment
                if block_end >= start and block_start <= end:
                    text_part = "\n".join(lines[2:])
                    result_blocks.append(f"{new_index}\n{lines[1]}\n{text_part}")
                    new_index += 1
            except Exception:
                continue
        
        return "\n\n".join(result_blocks)


video_processor = VideoProcessor()