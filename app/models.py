from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum


class AspectRatio(str, Enum):
    VERTICAL = "9:16"
    HORIZONTAL = "16:9"


class SubtitleLanguage(str, Enum):
    ENGLISH = "en"
    INDONESIAN = "id"


class ClipRequest(BaseModel):
    youtube_url: str
    aspect_ratio: AspectRatio = AspectRatio.VERTICAL
    subtitle_language: SubtitleLanguage = SubtitleLanguage.INDONESIAN
    max_clips: int = 5
    min_clip_duration: int = 30
    max_clip_duration: int = 180


class ClipSegment(BaseModel):
    start_time: float
    end_time: float
    text: str
    score: float


class ClipResult(BaseModel):
    clip_id: str
    original_url: str
    start_time: float
    end_time: float
    duration: float
    aspect_ratio: str
    subtitle_language: str
    download_url: str
    preview_url: Optional[str] = None


class ClipJobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    clips: Optional[List[ClipResult]] = None
    error: Optional[str] = None


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_admin: bool


class CreateUserRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    username: str
    is_admin: bool