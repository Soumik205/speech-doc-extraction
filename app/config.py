from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    stt_provider: Literal["mock", "whisper"] = "mock"
    stt_base_url: str = "https://api.groq.com/openai/v1"
    stt_model: str = "whisper-large-v3"
    groq_api_key: str | None = None
    max_audio_bytes: int = 25 * 1024 * 1024
    silence_threshold_dbfs: float = -40.0
    ocr_provider: Literal["mock", "google_vision"] = "mock"
    google_application_credentials: str | None = None
    max_image_bytes: int = 10 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
