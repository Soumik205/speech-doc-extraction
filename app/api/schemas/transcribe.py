from typing import Literal

from pydantic import BaseModel

Language = Literal["bn", "en", "auto"]


class TranscribeResponse(BaseModel):
    transcript: str
    detected_language: str
    duration_seconds: float
    provider: str
