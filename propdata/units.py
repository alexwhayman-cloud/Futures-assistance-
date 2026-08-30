"""Unit and value coercion at the source boundary.

Registers are full of sentinel junk — "NO DATA!", "unknown", empty strings,
"INVALID!" — and every one of them will happily become a string field or a
ValueError deep inside a loader if not caught here.
"""

from __future__ import annotations

from datetime import date, datetime

SQFT_PER_SQM = 10.763910416709722
TSUBO_PER_SQM = 0.3025
PYEONG_PER_SQM = 0.3025

#: Values that mean "absent" across the registers seen so far. Compared
#: case-insensitively after stripping.
NULL_TOKENS = frozenset(
    {
        "",
        "na",
        "n/a",
        "nodata",
        "no data",
        "no data!",
        "unknown",
        "invalid",
        "invalid!",
        "not recorded",
        "none",
        "null",
        "-",
    }
)


def clean(value: object) -> str | None:
    """Strip a raw cell to a real string, or None if it is a null sentinel."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in NULL_TOKENS:
        return None
    return text


def to_float(value: object) -> float | None:
    text = clean(value)
    if text is None:
        return None
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def to_int(value: object) -> int | None:
    number = to_float(value)
    if number is None:
        return None
    return int(number)


def to_date(value: object, *, fmt: str = "%Y-%m-%d") -> date | None:
    text = clean(value)
    if text is None:
        return None
    try:
        return datetime.strptime(text, fmt).date()
    except ValueError:
        return None


def sqft_to_sqm(sqft: float) -> float:
    return sqft / SQFT_PER_SQM


def tsubo_to_sqm(tsubo: float) -> float:
    return tsubo / TSUBO_PER_SQM


def pyeong_to_sqm(pyeong: float) -> float:
    return pyeong / PYEONG_PER_SQM


def normalise_area(value: object, unit: str) -> float | None:
    """Convert an area in `unit` to square metres, rounded to 2dp.

    Raises on an unrecognised unit rather than guessing: a silently wrong area
    is worse than a loud failure, because nothing downstream can detect it.
    """
    number = to_float(value)
    if number is None or number <= 0:
        return None

    converters = {
        "sqm": lambda n: n,
        "m2": lambda n: n,
        "sqft": sqft_to_sqm,
        "ft2": sqft_to_sqm,
        "tsubo": tsubo_to_sqm,
        "pyeong": pyeong_to_sqm,
    }
    key = unit.strip().lower()
    if key not in converters:
        raise ValueError(f"unknown area unit: {unit!r}")
    return round(converters[key](number), 2)
