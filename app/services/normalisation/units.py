_MICRO_TRANSLATION = str.maketrans({"µ": "u", "μ": "u"})

# Keys are lookup forms (stripped, lowercased, µ/μ normalised to ascii "u");
# values are the canonical spelling to output.
_CANONICAL_UNITS: dict[str, str] = {
    "mg/dl": "mg/dL",
    "gm/dl": "g/dL",
    "g/dl": "g/dL",
    "mmol/l": "mmol/L",
    "10^3/ul": "10^3/µL",
    "%": "%",
    "iu/l": "IU/L",
    "mg/l": "mg/L",
    "gm/l": "g/L",
    "g/l": "g/L",
    "cells/ul": "cells/µL",
}


def _lookup_key(raw: str) -> str:
    return raw.strip().lower().translate(_MICRO_TRANSLATION)


def canonicalise_unit(raw: str) -> str:
    """Maps a unit string to one spelling/casing per physical unit.

    An unrecognised unit is returned exactly as given -- never dropped,
    never mapped to a guess.
    """
    return _CANONICAL_UNITS.get(_lookup_key(raw), raw)
