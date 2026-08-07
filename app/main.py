from typing import Literal

from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel

app = FastAPI()

Language = Literal["bn", "en", "auto"]


class TranscribeResponse(BaseModel):
    transcript: str
    detected_language: str
    duration_seconds: float
    provider: str


@app.post("/api/v1/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: Language = Form(...),
) -> TranscribeResponse:
    return TranscribeResponse(
        transcript="",
        detected_language="en",
        duration_seconds=0.0,
        provider="stub",
    )
