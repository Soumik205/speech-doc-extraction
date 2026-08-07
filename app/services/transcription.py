from app.services.domain import TranscriptionResult


def transcribe(audio_bytes: bytes, language: str) -> TranscriptionResult:
    return TranscriptionResult(
        transcript="",
        detected_language="en",
        duration_seconds=0.0,
        provider="stub",
    )
