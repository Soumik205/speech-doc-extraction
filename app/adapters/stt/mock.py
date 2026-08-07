import hashlib
import json
from pathlib import Path

from app.services.domain import TranscriptionResult

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "testdata" / "fixtures" / "stt"
DEFAULT_FIXTURE_KEY = "default"


class MockSTTAdapter:
    """Replays recorded STT responses from testdata/fixtures/stt/, no network call.

    Fixture selection keys on the SHA-256 hex digest of the audio bytes, looked
    up in manifest.json. Audio whose digest has no manifest entry falls back to
    the fixture named under the "default" key, so replay stays deterministic
    for every input without requiring a fixture per possible upload.
    """

    def __init__(self, fixtures_dir: Path = FIXTURES_DIR) -> None:
        self._fixtures_dir = fixtures_dir
        with open(fixtures_dir / "manifest.json") as f:
            self._manifest: dict[str, str] = json.load(f)

    @property
    def name(self) -> str:
        return "mock"

    def transcribe(self, audio_bytes: bytes, language: str, audio_format: str) -> TranscriptionResult:
        digest = hashlib.sha256(audio_bytes).hexdigest()
        fixture_name = self._manifest.get(digest, self._manifest[DEFAULT_FIXTURE_KEY])
        with open(self._fixtures_dir / fixture_name) as f:
            data = json.load(f)
        return TranscriptionResult(**data)
