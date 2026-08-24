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
        
        # Audio-only download: far more reliable + avoids bot detection
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio",
            "outtmpl": str(base_path) + ".%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writesubtitles": False,
            "writeautomaticsub": False,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
        }
        
        # Spoof browser headers to reduce bot detection
        ydl_opts["http_headers"] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # Use cookies if available
        if os.path.exists(COOKIES_PATH):
            ydl_opts["cookiefile"] = COOKIES_PATH
            logger.info(f"Using cookies from {COOKIES_PATH}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            audio_path = str(base_path.with_suffix(".mp3"))
            if not os.path.exists(audio_path):
                for ext in [".mp3", ".m4a", ".webm", ".mp4"]:
                    candidate = str(base_path.with_suffix(ext))
                    if os.path.exists(candidate):
                        audio_path = candidate
                        break
            
            return {
                "video_path": None,  # Not needed for now
                "audio_path": audio_path,
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