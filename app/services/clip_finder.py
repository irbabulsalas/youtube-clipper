from openai import OpenAI
from typing import List, Dict, Any
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class ClipFinder:
    def __init__(self):
        self.primary_client = None
        self.fallback_client = None
        self.primary_model = settings.llm_model
        self.fallback_model = settings.llm_fallback_model
    
    def _get_primary(self):
        if self.primary_client is None:
            self.primary_client = OpenAI(
                api_key=settings.llm_api_key or "dummy",
                base_url=settings.llm_base_url
            )
        return self.primary_client
    
    def _get_fallback(self):
        if self.fallback_client is None:
            self.fallback_client = OpenAI(
                api_key="dummy",
                base_url=settings.llm_fallback_base_url
            )
        return self.fallback_client
    
    def find_clips(
        self,
        transcript: str,
        segments: List[Dict],
        max_clips: int = 5,
        min_duration: int = 30,
        max_duration: int = 180,
        language: str = "id"
    ) -> List[Dict[str, Any]]:
        prompt = self._build_prompt(transcript, segments, max_clips, min_duration, max_duration, language)
        
        try:
            clips = self._call_llm(prompt, use_fallback=False)
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}, trying fallback")
            try:
                clips = self._call_llm(prompt, use_fallback=True)
            except Exception as e2:
                logger.error(f"Fallback LLM also failed: {e2}")
                clips = self._heuristic_clips(segments, max_clips, min_duration, max_duration)
        
        # Final safety: ensure clips have start_time & end_time
        validated_clips = []
        for clip in clips:
            try:
                if isinstance(clip, dict) and "start_time" in clip and "end_time" in clip:
                    validated_clips.append(clip)
                elif isinstance(clip, dict):
                    validated_clips.append({
                        "start_time": clip.get("start_time", 0),
                        "end_time": clip.get("end_time", 30),
                        "reason": clip.get("reason", "Auto-generated"),
                        "score": clip.get("score", 0.5)
                    })
            except Exception:
                continue
        
        if not validated_clips:
            # Absolute fallback: grab first segment
            if segments:
                validated_clips.append({
                    "start_time": 0,
                    "end_time": min(30, segments[0].get("end", 30)),
                    "reason": "Default first segment",
                    "score": 0.5
                })
            else:
                validated_clips.append({
                    "start_time": 0,
                    "end_time": 30,
                    "reason": "Default clip",
                    "score": 0.5
                })
        
        return validated_clips[:max_clips]
    
    def _build_prompt(self, transcript, segments, max_clips, min_duration, max_duration, language) -> str:
        if language == "id":
            instructions = f"""
Anda adalah asisten yang membantu menemukan momen menarik dalam video untuk dibuat klip pendek (shorts/reels/TikTok).

Analisis transkrip video berikut dan tentukan {max_clips} momen paling menarik untuk dijadikan klip.

Kriteria momen menarik:
- Hook kuat di awal
- Informasi bernilai atau mengejutkan
- Emosi kuat (lucu, sedih, inspiring)
- Dapat berdiri sendiri tanpa konteks
- Durasi: {min_duration}-{max_duration} detik

Kembalikan HANYA JSON array dengan format:
[
  {{"start_time": <detik>, "end_time": <detik>, "reason": "<alasan>", "score": <0.0-1.0>}}
]

Transkrip (format: [start-end] text):
"""
        else:
            instructions = f"""
You are an assistant helping find interesting moments in videos for short clips (shorts/reels/TikTok).

Analyze the following video transcript and identify the {max_clips} most interesting moments to clip.

Criteria for interesting moments:
- Strong hook at the beginning
- Valuable or surprising information
- Strong emotion (funny, sad, inspiring)
- Can stand alone without context
- Duration: {min_duration}-{max_duration} seconds

Return ONLY a JSON array with format:
[
  {{"start_time": <seconds>, "end_time": <seconds>, "reason": "<why>", "score": <0.0-1.0>}}
]

Transcript (format: [start-end] text):
"""
        
        segment_texts = []
        for seg in segments:
            start = int(seg["start"])
            end = int(seg["end"])
            text = seg["text"]
            segment_texts.append(f"[{start}-{end}] {text}")
        
        return instructions + "\n".join(segment_texts)
    
    def _call_llm(self, prompt: str, use_fallback: bool = False) -> List[Dict]:
        if use_fallback:
            client = self._get_fallback()
            model = self.fallback_model
        else:
            client = self._get_primary()
            model = self.primary_model
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a video clip analysis assistant. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        
        content = response.choices[0].message.content.strip()
        
        try:
            if "[" in content and "]" in content:
                start = content.index("[")
                end = content.rindex("]") + 1
                json_str = content[start:end]
                parsed = json.loads(json_str)
                if isinstance(parsed, list):
                    # Validate each clip has required fields
                    validated = []
                    for clip in parsed:
                        if isinstance(clip, dict) and "start_time" in clip and "end_time" in clip:
                            validated.append(clip)
                    return validated if validated else [{"start_time": 0, "end_time": 30, "reason": "Default clip - LLM response incomplete", "score": 0.5}]
            # If not array format, try parsing as single object
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "start_time" in parsed and "end_time" in parsed:
                return [parsed]
            # Fallback
            return [{"start_time": 0, "end_time": 30, "reason": "Default clip - fallback", "score": 0.5}]
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse LLM response: {content[:500]}")
            return [{"start_time": 0, "end_time": 30, "reason": "Fallback clip - LLM parse error", "score": 0.5}]
    
    def _heuristic_clips(self, segments, max_clips, min_duration, max_duration) -> List[Dict]:
        clips = []
        
        if not segments:
            return clips
        
        # Merge consecutive segments into windows of min-max duration
        current_start = segments[0]["start"]
        current_end = segments[0]["end"]
        window_texts = [segments[0].get("text", "")]
        
        def flush(s, e, texts):
            duration = e - s
            if duration >= min_duration:
                words = sum(len(t.split()) for t in texts)
                density = words / duration if duration > 0 else 0
                clips.append({
                    "start_time": s,
                    "end_time": min(e, s + max_duration),
                    "reason": "Heuristic: continuous speech segment",
                    "score": min(1.0, density / 3)
                })
        
        for seg in segments[1:]:
            if seg["end"] - current_start <= max_duration:
                current_end = seg["end"]
                window_texts.append(seg.get("text", ""))
            else:
                flush(current_start, current_end, window_texts)
                current_start = seg["start"]
                current_end = seg["end"]
                window_texts = [seg.get("text", "")]
        
        flush(current_start, current_end, window_texts)
        
        clips.sort(key=lambda x: x["score"], reverse=True)
        return clips[:max_clips]


clip_finder = ClipFinder()