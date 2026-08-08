import hashlib
import json
from pathlib import Path

from app.services.domain import BoundingBox, TextLine

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "testdata" / "fixtures" / "ocr"
DEFAULT_FIXTURE_KEY = "default"


class MockOCRAdapter:
    """Replays recorded OCR responses from testdata/fixtures/ocr/, no network call.

    Fixture selection keys on the SHA-256 hex digest of the image bytes, looked
    up in manifest.json. Images whose digest has no manifest entry fall back to
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

    def extract_text(self, image_bytes: bytes) -> list[TextLine]:
        digest = hashlib.sha256(image_bytes).hexdigest()
        fixture_name = self._manifest.get(digest, self._manifest[DEFAULT_FIXTURE_KEY])
        with open(self._fixtures_dir / fixture_name) as f:
            data = json.load(f)
        return [
            TextLine(text=item["text"], bounding_box=BoundingBox(**item["bounding_box"]))
            for item in data
        ]
