from typing import Protocol

from app.services.domain import TextLine


class OCRProviderError(Exception):
    """Raised by an OCRAdapter when a network or provider-side failure
    prevents extracting text from an image, mirroring STTProviderError."""


class OCRAdapter(Protocol):
    @property
    def name(self) -> str: ...

    def extract_text(self, image_bytes: bytes) -> list[TextLine]: ...
