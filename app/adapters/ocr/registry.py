from app.adapters.ocr.base import OCRAdapter
from app.adapters.ocr.mock import MockOCRAdapter
from app.config import get_settings


def get_ocr_adapter() -> OCRAdapter:
    provider = get_settings().ocr_provider
    if provider == "mock":
        return MockOCRAdapter()
    if provider == "google_vision":
        raise NotImplementedError(
            "OCR_PROVIDER=google_vision is not implemented yet — "
            "app/adapters/ocr/google_vision.py has not been written"
        )
    raise ValueError(f"unknown OCR_PROVIDER {provider!r}; valid options: mock, google_vision")
