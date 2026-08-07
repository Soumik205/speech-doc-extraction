import pytest

from app.services.domain import AudioProbeResult, TranscriptionResult
from app.services.transcription import REASON_PROVIDER_EMPTY, REASON_SILENT, transcribe


class RecordingAdapter:
    name = "recording"

    def __init__(self, transcript: str) -> None:
        self._transcript = transcript
        self.calls: list[tuple[bytes, str]] = []

    def transcribe(self, audio_bytes: bytes, language: str) -> TranscriptionResult:
        self.calls.append((audio_bytes, language))
        return TranscriptionResult(
            transcript=self._transcript,
            detected_language="en",
            duration_seconds=999.0,  # deliberately wrong, to prove the probe wins
            provider="recording",
        )


def test_silent_probe_short_circuits_without_calling_adapter():
    adapter = RecordingAdapter(transcript="should never be seen")
    probe = AudioProbeResult(duration_seconds=4.0, is_silent=True, error=None)

    result = transcribe(adapter, b"audio-bytes", "en", probe)

    assert result.transcript == ""
    assert result.reason == REASON_SILENT
    assert result.detected_language is None
    assert result.duration_seconds == 4.0
    assert adapter.calls == []


def test_non_silent_probe_delegates_to_adapter():
    adapter = RecordingAdapter(transcript="hello world")
    probe = AudioProbeResult(duration_seconds=7.5, is_silent=False, error=None)

    result = transcribe(adapter, b"audio-bytes", "en", probe)

    assert result.transcript == "hello world"
    assert result.reason is None
    assert result.duration_seconds == 7.5  # from the probe, not the adapter's 999.0
    assert adapter.calls == [(b"audio-bytes", "en")]


def test_adapter_returning_empty_transcript_gets_provider_empty_reason():
    adapter = RecordingAdapter(transcript="")
    probe = AudioProbeResult(duration_seconds=2.0, is_silent=False, error=None)

    result = transcribe(adapter, b"audio-bytes", "en", probe)

    assert result.transcript == ""
    assert result.reason == REASON_PROVIDER_EMPTY


def test_probe_error_raises_value_error_without_calling_adapter():
    adapter = RecordingAdapter(transcript="unused")
    probe = AudioProbeResult(duration_seconds=None, is_silent=None, error="ffprobe failed")

    with pytest.raises(ValueError):
        transcribe(adapter, b"audio-bytes", "en", probe)

    assert adapter.calls == []
