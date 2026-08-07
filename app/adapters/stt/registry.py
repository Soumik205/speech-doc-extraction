from app.adapters.stt.base import STTAdapter
from app.adapters.stt.mock import MockSTTAdapter
from app.config import get_settings


def get_stt_adapter() -> STTAdapter:
    provider = get_settings().stt_provider
    if provider == "mock":
        return MockSTTAdapter()
    if provider == "whisper":
        raise NotImplementedError(
            "STT_PROVIDER=whisper is not implemented yet — "
            "app/adapters/stt/whisper_api.py has not been written"
        )
    raise ValueError(f"unknown STT_PROVIDER {provider!r}; valid options: mock, whisper")
