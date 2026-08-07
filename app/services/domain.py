from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    transcript: str
    detected_language: str
    duration_seconds: float
    provider: str
