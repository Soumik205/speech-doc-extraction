import json
import subprocess
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "testdata" / "fixtures" / "stt"


@pytest.fixture(scope="module")
def tone_wav_bytes(tmp_path_factory) -> bytes:
    out_path = tmp_path_factory.mktemp("audio") / "tone.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=1",
            "-ar",
            "16000",
            str(out_path),
        ],
        check=True,
    )
    return out_path.read_bytes()


def test_transcribe_endpoint_returns_mock_fixture_content(client, tone_wav_bytes):
    with open(FIXTURES_DIR / "en_sample.json") as f:
        expected = json.load(f)

    resp = client.post(
        "/api/v1/transcribe",
        files={"file": ("tone.wav", tone_wav_bytes, "audio/wav")},
        data={"language": "en"},
    )

    assert resp.status_code == 200
    body = resp.json()
    # A freshly-generated tone won't match any fixture digest in the
    # manifest, so the mock adapter falls back to its documented default --
    # asserting against that fixture's actual content, not just the status
    # code, is what proves the mock adapter is really being called here.
    assert body["transcript"] == expected["transcript"]
    assert body["detected_language"] == expected["detected_language"]
    assert body["provider"] == expected["provider"]
    assert body["reason"] is None
    # duration comes from ffprobe's real measurement of the generated tone,
    # not the fixture's hardcoded value
    assert body["duration_seconds"] == pytest.approx(1.0, abs=0.1)
