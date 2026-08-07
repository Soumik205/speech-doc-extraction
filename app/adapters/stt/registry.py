from app.adapters.stt.base import STTAdapter
from app.adapters.stt.mock import MockSTTAdapter
from app.adapters.stt.whisper_api import WhisperAPIAdapter
from app.config import get_settings


def get_stt_adapter() -> STTAdapter:
    settings = get_settings()
    provider = settings.stt_provider
    if provider == "mock":
        return MockSTTAdapter()
    if provider == "whisper":
        return WhisperAPIAdapter(
            base_url=settings.stt_base_url,
            model=settings.stt_model,
            api_key=settings.groq_api_key,
        )
    raise ValueError(f"unknown STT_PROVIDER {provider!r}; valid options: mock, whisper")
