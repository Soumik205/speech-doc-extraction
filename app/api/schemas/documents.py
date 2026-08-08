from pydantic import BaseModel


class DocumentMeta(BaseModel):
    patient_name: str | None
    age: str | None
    sex: str | None
    report_date: str | None
    lab_name: str | None
    reference_no: str | None


class LabResult(BaseModel):
    test_name: str | None
    value: float | None
    value_raw: str
    unit: str | None
    reference_range: str | None
    flag: str | None
    raw_line: str


class DocumentExtractResponse(BaseModel):
    meta: DocumentMeta
    results: list[LabResult]
