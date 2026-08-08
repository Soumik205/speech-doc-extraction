from app.adapters.ocr.base import OCRAdapter
from app.adapters.ocr.google_vision import GoogleVisionAdapter
from app.adapters.ocr.mock import MockOCRAdapter
from app.config import get_settings


def get_ocr_adapter() -> OCRAdapter:
    settings = get_settings()
    provider = settings.ocr_provider
    if provider == "mock":
        return MockOCRAdapter()
    if provider == "google_vision":
        return GoogleVisionAdapter(credentials_path=settings.google_application_credentials)
    raise ValueError(f"unknown OCR_PROVIDER {provider!r}; valid options: mock, google_vision")
