import calendar
import datetime
import re
from dataclasses import dataclass

# 12/05/2024 could be 12 May or 5 December -- genuinely ambiguous whenever
# both the day- and month-candidate numbers are <= 12. This module never
# guesses a locale convention (DD/MM vs MM/DD) to break that tie; the
# ambiguous case returns None with raw preserved, same as an unparseable
# date. A numeric date is only resolved when the numbers themselves force
# a unique reading -- one component is > 12, so it can only be the day.
_ISO_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_NUMERIC_RE = re.compile(r"^(\d{1,2})([/.-])(\d{1,2})\2(\d{4})$")
# A two-digit year (12/05/24) adds a second assumption -- which century? --
# on top of the day/month ambiguity, so it's rejected explicitly here
# rather than left to fall through _NUMERIC_RE's 4-digit year requirement
# incidentally.
_TWO_DIGIT_YEAR_RE = re.compile(r"^(\d{1,2})([/.-])(\d{1,2})\2(\d{2})$")
_DAY_MONTH_YEAR_RE = re.compile(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$")
_MONTH_DAY_YEAR_RE = re.compile(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$")

_MONTHS: dict[str, int] = {}
for _i in range(1, 13):
    _MONTHS[calendar.month_name[_i].lower()] = _i
    _MONTHS[calendar.month_abbr[_i].lower()] = _i


@dataclass
class NormalisedDate:
    iso_date: str | None
    raw: str


def _to_iso(year: int, month: int, day: int) -> str | None:
    if not (1 <= month <= 12):
        return None
    try:
        datetime.date(year, month, day)
    except ValueError:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def _month_from_name(name: str) -> int | None:
    return _MONTHS.get(name.lower())


def parse_date(raw: str) -> NormalisedDate:
    stripped = raw.strip()

    match = _ISO_RE.match(stripped)
    if match:
        year, month, day = (int(g) for g in match.groups())
        return NormalisedDate(iso_date=_to_iso(year, month, day), raw=raw)

    match = _NUMERIC_RE.match(stripped)
    if match:
        a, b, year = int(match.group(1)), int(match.group(3)), int(match.group(4))
        a_valid_month = 1 <= a <= 12
        b_valid_month = 1 <= b <= 12
        if a_valid_month and b_valid_month:
            return NormalisedDate(iso_date=None, raw=raw)  # genuinely ambiguous
        if b_valid_month:  # a > 12, so a can only be the day
            return NormalisedDate(iso_date=_to_iso(year, b, a), raw=raw)
        if a_valid_month:  # b > 12, so b can only be the day
            return NormalisedDate(iso_date=_to_iso(year, a, b), raw=raw)
        return NormalisedDate(iso_date=None, raw=raw)  # neither can be a month

    match = _TWO_DIGIT_YEAR_RE.match(stripped)
    if match:
        return NormalisedDate(iso_date=None, raw=raw)  # century not inferred

    match = _DAY_MONTH_YEAR_RE.match(stripped)
    if match:
        day, month_name, year = match.group(1), match.group(2), match.group(3)
        month = _month_from_name(month_name)
        if month is None:
            return NormalisedDate(iso_date=None, raw=raw)
        return NormalisedDate(iso_date=_to_iso(int(year), month, int(day)), raw=raw)

    match = _MONTH_DAY_YEAR_RE.match(stripped)
    if match:
        month_name, day, year = match.group(1), match.group(2), match.group(3)
        month = _month_from_name(month_name)
        if month is None:
            return NormalisedDate(iso_date=None, raw=raw)
        return NormalisedDate(iso_date=_to_iso(int(year), month, int(day)), raw=raw)

    return NormalisedDate(iso_date=None, raw=raw)
