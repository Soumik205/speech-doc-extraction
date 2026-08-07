from app.adapters.stt.base import STTAdapter
from app.services.domain import AudioProbeResult, TranscriptionResult

REASON_SILENT = "silent"
REASON_PROVIDER_EMPTY = "provider_returned_nothing"


def transcribe(
    adapter: STTAdapter,
    audio_bytes: bytes,
    audio_format: str,
    language: str,
    probe: AudioProbeResult,
) -> TranscriptionResult:
    if probe.error is not None or probe.duration_seconds is None or probe.is_silent is None:
        raise ValueError(f"probe must be error-free and complete before transcription: {probe!r}")

    if probe.is_silent:
        return TranscriptionResult(
            transcript="",
            detected_language=None,
            duration_seconds=probe.duration_seconds,
            provider=adapter.name,
            reason=REASON_SILENT,
        )

    result = adapter.transcribe(audio_bytes, language, audio_format)
    reason = REASON_PROVIDER_EMPTY if result.transcript == "" else None
    return TranscriptionResult(
        transcript=result.transcript,
        detected_language=result.detected_language,
        duration_seconds=probe.duration_seconds,
        provider=result.provider,
        reason=reason,
    )
