from typing import Protocol

from app.services.domain import TranscriptionResult


class STTAdapter(Protocol):
    @property
    def name(self) -> str: ...

    def transcribe(self, audio_bytes: bytes, language: str) -> TranscriptionResult: ...
