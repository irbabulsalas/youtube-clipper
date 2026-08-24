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
    
    # Whisper
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    
    # Video processing
    temp_dir: str = "/tmp/youtube-clipper"
    max_video_duration: int = 3600
    clip_max_duration: int = 180
    clip_ttl: int = 600  # seconds before auto-delete
    
    # Data storage
    data_dir: str = "/app/data"
    
    class Config:
        env_file = ".env"
        env_prefix = "CLIPPER_"


settings = Settings()