import pytest

from app.config import get_settings

WAV_HEADER = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 40

FORMAT_HEADERS = {
    "wav": WAV_HEADER,
    "mp3": b"ID3" + b"\x00" * 40,
    "m4a": b"\x00\x00\x00\x18ftypM4A " + b"\x00" * 40,
    "flac": b"fLaC" + b"\x00" * 40,
    "ogg": b"OggS" + b"\x00" * 40,
    "webm": b"\x1a\x45\xdf\xa3" + b"\x00" * 40,
}


def test_oversized_upload_rejected(client, monkeypatch):
    monkeypatch.setenv("MAX_AUDIO_BYTES", "1000")
    get_settings.cache_clear()

    big = WAV_HEADER + b"A" * 5000
    resp = client.post(
        "/api/v1/transcribe",
        files={"file": ("big.wav", big, "audio/wav")},
        data={"language": "en"},
    )

    assert resp.status_code == 413
    assert resp.json()["code"] == "file_too_large"


def test_empty_file_rejected(client):
    resp = client.post(
        "/api/v1/transcribe",
        files={"file": ("empty.wav", b"", "audio/wav")},
        data={"language": "en"},
    )

    assert resp.status_code == 400
    assert resp.json()["code"] == "empty_file"


def test_text_file_renamed_to_wav_rejected(client):
    resp = client.post(
        "/api/v1/transcribe",
        files={"file": ("fake.wav", b"just plain text, not audio at all", "audio/wav")},
        data={"language": "en"},
    )

    assert resp.status_code == 415
    assert resp.json()["code"] == "unsupported_format"


@pytest.mark.parametrize("fmt", sorted(FORMAT_HEADERS))
def test_accepted_format_magic_bytes_not_rejected_as_unsupported(client, fmt):
    header = FORMAT_HEADERS[fmt]
    resp = client.post(
        "/api/v1/transcribe",
        files={"file": (f"sample.{fmt}", header, "application/octet-stream")},
        data={"language": "en"},
    )

    # These headers are magic bytes only, not full decodable audio, so the
    # request may still fail later (e.g. 422 undecodable_audio) -- what this
    # test asserts is specifically that the sniff step itself accepts them.
    assert resp.status_code != 415
    assert resp.json().get("code") != "unsupported_format"


def test_invalid_language_rejected(client):
    resp = client.post(
        "/api/v1/transcribe",
        files={"file": ("a.wav", WAV_HEADER, "audio/wav")},
        data={"language": "fr"},
    )

    assert resp.status_code == 422
