import re
from dataclasses import dataclass
from typing import Literal

Qualifier = Literal["lt", "gt", "range"]

# Reference ranges and lab values are never negative in practice, so a
# leading '-' is deliberately not accepted here: it would make "-5" and a
# malformed range indistinguishable without guessing which one it is.
_RANGE_RE = re.compile(r"^(\d[\d,]*\.?\d*)\s*-\s*(\d[\d,]*\.?\d*)$")
_LT_RE = re.compile(r"^<\s*(\d[\d,]*\.?\d*)$")
_GT_RE = re.compile(r"^>\s*(\d[\d,]*\.?\d*)$")
_SCIENTIFIC_RE = re.compile(r"^(\d[\d,]*\.?\d*)\s*[xX]\s*10\^(-?\d+)$")
_NUMBER_RE = re.compile(r"^(\d[\d,]*\.?\d*)$")


@dataclass
class NormalisedValue:
    value: float | None
    qualifier: Qualifier | None
    raw: str


def _to_float(token: str) -> float:
    return float(token.replace(",", ""))


def parse_value(raw: str) -> NormalisedValue:
    stripped = raw.strip()

    match = _RANGE_RE.match(stripped)
    if match:
        return NormalisedValue(value=None, qualifier="range", raw=raw)

    match = _LT_RE.match(stripped)
    if match:
        return NormalisedValue(value=_to_float(match.group(1)), qualifier="lt", raw=raw)

    match = _GT_RE.match(stripped)
    if match:
        return NormalisedValue(value=_to_float(match.group(1)), qualifier="gt", raw=raw)

    match = _SCIENTIFIC_RE.match(stripped)
    if match:
        base = _to_float(match.group(1))
        exponent = int(match.group(2))
        return NormalisedValue(value=base * (10**exponent), qualifier=None, raw=raw)

    match = _NUMBER_RE.match(stripped)
    if match:
        return NormalisedValue(value=_to_float(match.group(1)), qualifier=None, raw=raw)

    # Qualitative results (Negative, Nil, Trace, Positive, ...), empty
    # strings, and anything else that doesn't match a known numeric shape
    # all fall through here uniformly -- never guessed at, never a
    # hardcoded whitelist of "known" qualitative words.
    return NormalisedValue(value=None, qualifier=None, raw=raw)
