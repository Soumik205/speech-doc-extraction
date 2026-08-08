import re

from app.services.domain import DocumentMeta, LabResult, TextLine
from app.services.normalisation.units import canonicalise_unit
from app.services.normalisation.values import parse_value

# OCR-reconstructed table rows separate their columns with runs of multiple
# spaces; this is a property of the line's text, not of bounding-box
# geometry, so splitting on it stays within "line-level regex only".
_FIELD_SPLIT_RE = re.compile(r"\s{2,}")

_UNIT_LIKE_RE = re.compile(r"[/%^]")
_DIGIT_RE = re.compile(r"\d")
_RANGE_LIKE_RE = re.compile(r"^\d[\d,]*\.?\d*\s*-\s*\d[\d,]*\.?\d*$")
# A trailing short alphabetic token with nothing left to classify it as is
# treated as the flag. The brief leaves the set of flag values unspecified,
# so this accepts shape (short word) rather than a fixed vocabulary.
_FLAG_RE = re.compile(r"^[A-Za-z]{1,12}$")

_PATIENT_NAME_RE = re.compile(r"patient\s*name\s*:?\s*(.+)", re.IGNORECASE)
_AGE_SEX_RE = re.compile(r"age\s*/\s*sex\s*:?\s*(\d+)\s*/\s*([A-Za-z]+)", re.IGNORECASE)
_AGE_RE = re.compile(r"\bage\s*:?\s*(\d+)", re.IGNORECASE)
_SEX_RE = re.compile(r"\bsex\s*:?\s*([A-Za-z]+)", re.IGNORECASE)
_REPORT_DATE_RE = re.compile(r"report\s*date\s*:?\s*(.+)", re.IGNORECASE)
_LAB_NAME_RE = re.compile(r"lab(?:oratory)?\s*name\s*:?\s*(.+)", re.IGNORECASE)
_REFERENCE_NO_RE = re.compile(r"reference\s*(?:no\.?|number)\s*:?\s*(.+)", re.IGNORECASE)


def parse_result_row(line: TextLine) -> LabResult | None:
    """Extracts a lab result from one OCR line, or None if the line doesn't
    look like a result row. raw_line is always line.text unmodified --
    never stripped, cleaned, or reconstructed.

    Only structural signals reject a line (too few fields, a "Label:"
    metadata line) -- never whether the value field happens to parse. A
    result row whose value can't be confidently classified must still
    produce a LabResult with raw_line preserved and value=None; dropping
    it would silently lose raw_line, which the brief says must never
    happen. parse_value is what's allowed to say "no number here", not
    row detection.
    """
    raw_line = line.text
    fields = [f.strip() for f in _FIELD_SPLIT_RE.split(raw_line.strip()) if f.strip()]

    if len(fields) < 2:
        return None

    test_name, *remainder = fields

    if ":" in test_name:
        return None  # "Label: value" lines are metadata, not a result row

    # A genuine result row carries a number, a range, or a unit somewhere
    # after the test name; a column-header line ("Test Name / Result /
    # Unit / Reference Range / Flag") has none of these anywhere. This is
    # a structural test on the line's content, not a whitelist of header
    # words, so an unlisted qualitative value in a row that still has a
    # unit or range column is unaffected.
    #
    # Tradeoff: a *bare* qualitative row -- test name plus a qualitative
    # word and nothing else, no unit or range column -- is structurally
    # identical to a header line and gets rejected too. Rejecting headers
    # is preferred: a header appears on every report, while a bare
    # qualitative row (no unit/range at all) is rarer, and the reverse
    # tradeoff would put a spurious row in every single extraction.
    has_digit = any(_DIGIT_RE.search(field) for field in remainder)
    has_unit_shape = any(_UNIT_LIKE_RE.search(field) for field in remainder)
    if not has_digit and not has_unit_shape:
        return None

    value_field = remainder[0]
    unit_field: str | None = None
    range_field: str | None = None
    flag_field: str | None = None

    for field in remainder[1:]:
        if unit_field is None and _UNIT_LIKE_RE.search(field):
            unit_field = field
        elif range_field is None and _RANGE_LIKE_RE.match(field):
            range_field = field
        elif flag_field is None and _FLAG_RE.match(field):
            flag_field = field

    normalised_value = parse_value(value_field)

    return LabResult(
        test_name=test_name or None,
        value=normalised_value.value,
        value_raw=normalised_value.raw,
        unit=canonicalise_unit(unit_field) if unit_field else None,
        reference_range=range_field,
        flag=flag_field,
        raw_line=raw_line,
    )


def extract_meta(lines: list[TextLine]) -> DocumentMeta:
    """Extracts header metadata by label matching across all lines. A field
    with no matching label is None -- never guessed from position."""
    patient_name: str | None = None
    age: str | None = None
    sex: str | None = None
    report_date: str | None = None
    lab_name: str | None = None
    reference_no: str | None = None

    for line in lines:
        text = line.text.strip()

        if patient_name is None:
            match = _PATIENT_NAME_RE.search(text)
            if match:
                patient_name = match.group(1).strip() or None

        if age is None or sex is None:
            match = _AGE_SEX_RE.search(text)
            if match:
                if age is None:
                    age = match.group(1).strip() or None
                if sex is None:
                    sex = match.group(2).strip() or None

        if age is None:
            match = _AGE_RE.search(text)
            if match:
                age = match.group(1).strip() or None

        if sex is None:
            match = _SEX_RE.search(text)
            if match:
                sex = match.group(1).strip() or None

        if report_date is None:
            match = _REPORT_DATE_RE.search(text)
            if match:
                report_date = match.group(1).strip() or None

        if lab_name is None:
            match = _LAB_NAME_RE.search(text)
            if match:
                lab_name = match.group(1).strip() or None

        if reference_no is None:
            match = _REFERENCE_NO_RE.search(text)
            if match:
                reference_no = match.group(1).strip() or None

    return DocumentMeta(
        patient_name=patient_name,
        age=age,
        sex=sex,
        report_date=report_date,
        lab_name=lab_name,
        reference_no=reference_no,
    )
