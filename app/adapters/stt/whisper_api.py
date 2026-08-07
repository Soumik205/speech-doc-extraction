import httpx

from app.adapters.stt.base import STTProviderError
from app.services.domain import TranscriptionResult

_TIMEOUT_SECONDS = 60.0


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

    def transcribe(self, audio_bytes: bytes, language: str) -> TranscriptionResult:
        data = {"model": self._model, "response_format": "verbose_json"}
        if language != "auto":
            data["language"] = language

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}

        try:
            response = httpx.post(
                f"{self._base_url}/audio/transcriptions",
                data=data,
                files={"file": ("audio", audio_bytes)},
                headers=headers,
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise STTProviderError(
                f"STT provider returned HTTP {exc.response.status_code}"
            ) from exc
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
