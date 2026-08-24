from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Auth
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_USE_ENV_VAR"
    owner_password: str = "123456"
    
    # LLM Provider (primary: tokbomreplit1, fallback: opencode-free)
    llm_provider: str = "tokbomreplit1"
    llm_model: str = "glm-5"
    llm_base_url: str = "https://tokenbom.com/v1"
    llm_api_key: str = ""
    
    # Fallback LLM (opencode-free, keyless)
    llm_fallback_provider: str = "opencode-free"
    llm_fallback_model: str = "laguna-s-2.1-free"
    llm_fallback_base_url: str = "https://opencode.ai/zen/v1"
    
    # Whisper - optimized for RAM-limited environment (Railway Hobby = ~512MB RAM)
    # NOTE: 'tiny' is used instead of 'small' to avoid OOM kills
    # 'tiny' = ~256MB RAM, 'base' = ~512MB RAM, 'small' = ~1GB RAM
    whisper_model: str = "tiny"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"  # Use int8 quantization to reduce memory
    
    # Video processing - limits to prevent OOM
    temp_dir: str = "/tmp/youtube-clipper"
    max_video_duration: int = 120  # Hard limit: 2 minutes max video
    clip_max_duration: int = 60     # Max clip output duration
    clip_ttl: int = 600  # seconds before auto-delete
    
    # Subtitle
    subtitle_font: str = "DejaVu Sans"
    subtitle_fontsize: int = 24
    
    # Data storage
    data_dir: str = "/app/data"
    
    class Config:
        env_file = ".env"
        env_prefix = "CLIPPER_"


settings = Settings()