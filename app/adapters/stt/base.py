from typing import Protocol

from app.services.domain import TranscriptionResult


class STTProviderError(Exception):
    """Raised by an STTAdapter when a network or provider-side failure
    prevents producing a transcription, so callers see one clear
    exception type instead of an HTTP client's raw errors."""


class STTAdapter(Protocol):
    @property
    def name(self) -> str: ...

    def transcribe(self, audio_bytes: bytes, language: str) -> TranscriptionResult: ...
