from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    transcript: str
    detected_language: str
    duration_seconds: float
    provider: str


@dataclass
class AudioProbeResult:
    duration_seconds: float | None
    is_silent: bool | None
    error: str | None = None
