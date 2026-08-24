import subprocess
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import asyncio

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, output_dir: str = "/tmp/youtube-clipper/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_clip(
        self,
        video_path: str,
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
            video_path=video_path,
            output_path=output_path,
            start_time=start_time,
            duration=duration,
            aspect_ratio=aspect_ratio,
            subtitle_path=subtitle_path
        )
        
        logger.info(f"Running ffmpeg: {' '.join(cmd[:10])}...")
        
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
        video_path: str,
        output_path: str,
        start_time: float,
        duration: float,
        aspect_ratio: str,
        subtitle_path: Optional[str]
    ) -> list:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-i", video_path,
            "-t", str(duration),
        ]
        
        filters = []
        
        if aspect_ratio == "9:16":
            filters.append("scale=1080:1920:force_original_aspect_ratio=decrease")
            filters.append("pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black")
        
        if subtitle_path and os.path.exists(subtitle_path):
            sub_path = subtitle_path.replace(":", "\\:").replace("'", "'\\''")
            subtitle_filter = f"subtitles='{sub_path}':force_style='FontName=DejaVu Sans,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'"
            filters.append(subtitle_filter)
        
        if filters:
            cmd.extend(["-vf", ",".join(filters)])
        
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ])
        
        return cmd
    
    def extract_segment_srt(self, full_srt: str, start_time: float, end_time: float) -> str:
        lines = full_srt.strip().split("\n")
        result_lines = []
        current_entry = []
        entry_start = None
        entry_end = None
        entry_num = 0
        
        for line in lines:
            current_entry.append(line)
            
            if "-->" in line:
                parts = line.split(" --> ")
                entry_start = self._parse_srt_timestamp(parts[0])
                entry_end = self._parse_srt_timestamp(parts[1].strip())
            elif line.strip() == "" and current_entry and entry_start is not None:
                if entry_start >= start_time and entry_end <= end_time:
                    entry_num += 1
                    adjusted_entry = [str(entry_num)]
                    
                    new_start = max(0, entry_start - start_time)
                    new_end = max(0, entry_end - start_time)
                    adjusted_entry.append(
                        f"{self._format_srt_timestamp(new_start)} --> {self._format_srt_timestamp(new_end)}"
                    )
                    
                    for l in current_entry[2:]:
                        if l.strip():
                            adjusted_entry.append(l)
                    
                    adjusted_entry.append("")
                    result_lines.extend(adjusted_entry)
                
                current_entry = []
                entry_start = None
                entry_end = None
        
        return "\n".join(result_lines)
    
    def _parse_srt_timestamp(self, ts: str) -> float:
        ts = ts.strip().replace(",", ":")
        parts = ts.split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        millis = int(parts[3]) if len(parts) > 3 else 0
        return hours * 3600 + minutes * 60 + seconds + millis / 1000
    
    def _format_srt_timestamp(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


video_processor = VideoProcessor()