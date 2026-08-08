from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    transcript: str
    detected_language: str | None
    duration_seconds: float
    provider: str
    reason: str | None = None


@dataclass
class AudioProbeResult:
    duration_seconds: float | None
    is_silent: bool | None
    error: str | None = None


@dataclass
class DocumentMeta:
    patient_name: str | None
    age: str | None
    sex: str | None
    report_date: str | None
    lab_name: str | None
    reference_no: str | None


@dataclass
class LabResult:
    test_name: str | None
    value: float | None
    value_raw: str
    unit: str | None
    reference_range: str | None
    flag: str | None
    raw_line: str


@dataclass
class DocumentExtractionResult:
    meta: DocumentMeta
    results: list[LabResult]


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float


@dataclass
class TextLine:
    text: str
    bounding_box: BoundingBox
