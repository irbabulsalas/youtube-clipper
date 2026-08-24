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
        """Build ffmpeg command to create vertical video clip from audio + subtitles."""
        
        # Parse aspect ratio
        if aspect_ratio == "9:16":
            width, height = 720, 1280
        elif aspect_ratio == "16:9":
            width, height = 1280, 720
        else:
            width, height = 720, 1280

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", audio_path,
            # Create a black background and overlay audio waveform
            "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:d={duration}",
            # Extract audio segment
            "-filter_complex",
            (
                f"[0:a]atrim=start={start_time}:end={end_time},asetpts=PTS-STARTPTS[a];"
                f"[1:v]scale={width}:{height}[bg];"
                f"[bg][a]overlay=shortest=1:x=0:y=0,scale={width}:{height}[v]"
            ),
            "-map", "[v]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
        ]

        if subtitle_path and os.path.exists(subtitle_path):
            cmd.extend([
                "-vf", f"subtitles={subtitle_path}:charenc=utf-8:force_style='FontName=DejaVu Sans,FontSize=20,PrimaryColour=&H00FFFFFF,Bold=1'",
            ])

        cmd.append(output_path)

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