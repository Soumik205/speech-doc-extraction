from fastapi import APIRouter, File, Form, UploadFile

from app.adapters.stt.registry import get_stt_adapter
from app.api.schemas.transcribe import Language, TranscribeResponse
from app.services import transcription

router = APIRouter(prefix="/api/v1")


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: Language = Form(...),
) -> TranscribeResponse:
    audio_bytes = await file.read()
    adapter = get_stt_adapter()
    result = transcription.transcribe(adapter, audio_bytes, language)
    return TranscribeResponse(
        transcript=result.transcript,
        detected_language=result.detected_language,
        duration_seconds=result.duration_seconds,
        provider=result.provider,
    )
