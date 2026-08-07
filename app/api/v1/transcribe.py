from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.adapters.audio.probe import probe_audio
from app.adapters.stt.base import STTProviderError
from app.adapters.stt.registry import get_stt_adapter
from app.api.schemas.transcribe import Language, TranscribeResponse
from app.config import get_settings
from app.services import transcription

router = APIRouter(prefix="/api/v1")

_SNIFF_BYTES = 32
_CHUNK_SIZE = 64 * 1024


def _sniff_audio_format(header: bytes) -> str | None:
    if header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        return "wav"
    if header.startswith(b"ID3") or header[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "mp3"
    if header[4:8] == b"ftyp":
        return "m4a"
    if header.startswith(b"fLaC"):
        return "flac"
    if header.startswith(b"OggS"):
        return "ogg"
    if header.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    return None


def _too_large_error(max_bytes: int) -> HTTPException:
    return HTTPException(
        status_code=413,
        detail={
            "code": "file_too_large",
            "message": f"File exceeds the maximum allowed size of {max_bytes / (1024 * 1024):.1f} MB.",
        },
    )


async def _read_capped(file: UploadFile, max_bytes: int) -> bytes:
    # Starlette's multipart parser only checks max_part_size for plain form
    # fields, not file parts, so the size cap for uploads is enforced here.
    total = 0
    chunks: list[bytes] = []
    while True:
        chunk = await file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise _too_large_error(max_bytes)
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/transcribe")
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    language: Language = Form(...),
) -> TranscribeResponse:
    settings = get_settings()
    max_bytes = settings.max_audio_bytes

    # Fast path: reject an obviously oversized upload from its declared
    # Content-Length before reading any of the body.
    content_length = request.headers.get("content-length")
    if content_length is not None and content_length.isdigit() and int(content_length) > max_bytes:
        raise _too_large_error(max_bytes)

    audio_bytes = await _read_capped(file, max_bytes)

    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail={"code": "empty_file", "message": "Uploaded file is empty."},
        )

    audio_format = _sniff_audio_format(audio_bytes[:_SNIFF_BYTES])
    if audio_format is None:
        raise HTTPException(
            status_code=415,
            detail={
                "code": "unsupported_format",
                "message": "Unsupported audio format; expected one of: wav, mp3, m4a, flac, ogg, webm.",
            },
        )

    probe = await probe_audio(audio_bytes, settings.silence_threshold_dbfs)
    if probe.error is not None:
        raise HTTPException(
            status_code=422,
            detail={"code": "undecodable_audio", "message": "Audio file could not be decoded."},
        )

    adapter = get_stt_adapter()
    try:
        result = transcription.transcribe(adapter, audio_bytes, audio_format, language, probe)
    except STTProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "provider_error", "message": "The speech-to-text provider failed."},
        ) from exc
    return TranscribeResponse(
        transcript=result.transcript,
        detected_language=result.detected_language,
        duration_seconds=result.duration_seconds,
        provider=result.provider,
        reason=result.reason,
    )
