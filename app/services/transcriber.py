from faster_whisper import WhisperModel
from typing import List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
    
    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        return self._model
    
    def transcribe(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=1,
            best_of=1,
            vad_filter=False,
            word_timestamps=False,
            condition_on_previous_text=False,
        )
        
        segment_list = []
        for seg in segments:
            segment_list.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })
        
        full_text = " ".join(s["text"] for s in segment_list)
        
        return {
            "text": full_text,
            "segments": segment_list,
            "language": info.language,
            "duration": getattr(info, 'duration', 0),
        }
    
    def get_srt(self, segments: List[Dict]) -> str:
        """Convert segments to SRT format."""
        lines = []
        for i, seg in enumerate(segments):
            lines.append(str(i + 1))
            start = self._format_timestamp(seg["start"])
            end = self._format_timestamp(seg["end"])
            lines.append(f"{start} --> {end}")
            lines.append(seg["text"])
            lines.append("")
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as SRT timestamp."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        millisecs = int((secs - int(secs)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{millisecs:03d}"


transcriber = Transcriber(model_size="tiny", device="cpu", compute_type="int8")