import yt_dlp
import os
from pathlib import Path
from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Optional cookies file for YouTube bot-detection bypass
COOKIES_PATH = os.environ.get("CLIPPER_COOKIES_FILE", "/app/data/cookies.txt")


class YouTubeDownloader:
    def __init__(self, output_dir: str = "/tmp/youtube-clipper"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, url: str, video_id: Optional[str] = None) -> Dict[str, Any]:
        if video_id is None:
            video_id = self._extract_video_id(url)
        
        base_path = self.output_dir / video_id
        
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": str(base_path),
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writesubtitles": False,
            "writeautomaticsub": False,
            "merge_output_format": "mp4",
        }
        
        # Use cookies if available (bypasses YouTube bot detection on datacenter IPs)
        if os.path.exists(COOKIES_PATH):
            ydl_opts["cookiefile"] = COOKIES_PATH
            logger.info(f"Using cookies from {COOKIES_PATH}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            video_path = str(base_path.with_suffix(".mp4"))
            if not os.path.exists(video_path):
                for ext in [".mp4", ".mkv", ".webm"]:
                    candidate = str(base_path.with_suffix(ext))
                    if os.path.exists(candidate):
                        video_path = candidate
                        break
            
            return {
                "video_path": video_path,
                "audio_path": video_path,  # Audio is embedded
                "title": info.get("title", ""),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "description": info.get("description", ""),
                "video_id": video_id,
                "chapters": info.get("chapters", []),
            }
    
    def _extract_video_id(self, url: str) -> str:
        patterns = [
            r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    def cleanup(self, video_id: str):
        import glob
        pattern = str(self.output_dir / f"{video_id}.*")
        for f in glob.glob(pattern):
            try:
                os.remove(f)
            except Exception:
                pass


downloader = YouTubeDownloader()