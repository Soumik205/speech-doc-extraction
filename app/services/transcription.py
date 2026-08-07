from app.adapters.stt.base import STTAdapter
from app.services.domain import TranscriptionResult


def transcribe(adapter: STTAdapter, audio_bytes: bytes, language: str) -> TranscriptionResult:
    return adapter.transcribe(audio_bytes, language)
