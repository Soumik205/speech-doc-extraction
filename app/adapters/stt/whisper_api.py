import logging

import httpx

from app.adapters.stt.base import STTProviderError
from app.services.domain import TranscriptionResult

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 60.0
_ERROR_BODY_TRUNCATE = 500

_CONTENT_TYPES = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
    "webm": "audio/webm",
}


class WhisperAPIAdapter:
    """Calls an OpenAI-compatible /audio/transcriptions endpoint. Groq and
    OpenAI both implement this surface, so the same class serves either by
    base_url alone."""

    def __init__(self, base_url: str, model: str, api_key: str | None) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "whisper"

    def transcribe(self, audio_bytes: bytes, language: str, audio_format: str) -> TranscriptionResult:
        data = {"model": self._model, "response_format": "verbose_json"}
        if language != "auto":
            data["language"] = language

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}

        # Filename and content type come from the format the route already
        # sniffed from magic bytes, not the client-supplied filename, which
        # is untrusted and may be spoofed. Groq rejects an unnamed blob with
        # no inferable type, so this has to be a real (name, type) pair.
        filename = f"audio.{audio_format}"
        content_type = _CONTENT_TYPES.get(audio_format, "application/octet-stream")

        try:
            response = httpx.post(
                f"{self._base_url}/audio/transcriptions",
                data=data,
                files={"file": (filename, audio_bytes, content_type)},
                headers=headers,
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:_ERROR_BODY_TRUNCATE]
            message = f"STT provider returned HTTP {exc.response.status_code}: {body}"
            logger.error(message)
            raise STTProviderError(message) from exc
        except httpx.HTTPError as exc:
            raise STTProviderError(
                f"STT provider request failed: {type(exc).__name__}"
            ) from exc
        except ValueError as exc:
            raise STTProviderError("STT provider returned an unreadable response") from exc

        try:
            transcript = payload["text"]
        except (KeyError, TypeError) as exc:
            raise STTProviderError("STT provider response is missing 'text'") from exc

        duration = payload.get("duration")

        return TranscriptionResult(
            transcript=transcript,
            detected_language=payload.get("language"),
            duration_seconds=float(duration) if duration is not None else 0.0,
            provider=self.name,
        )
