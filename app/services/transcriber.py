from faster_whisper import WhisperModel
from typing import List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
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
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 200,
            }
        )
        
        segment_list = []
        full_text = []
        
        for seg in segments:
            segment_list.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip()
            })
            full_text.append(seg.text.strip())
        
        return {
            "segments": segment_list,
            "language": info.language,
            "language_probability": info.language_probability,
            "text": " ".join(full_text)
        }
    
    def get_srt(self, segments: List[Dict], language: str = "en") -> str:
        lines = []
        for i, seg in enumerate(segments, 1):
            start = self._format_timestamp(seg["start"])
            end = self._format_timestamp(seg["end"])
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(seg["text"])
            lines.append("")
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


transcriber = Transcriber()