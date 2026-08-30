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

#: Indonesian land is quoted in are almost universally — a Bali listing says
#: "5 are", never "500 sqm". 1 are = 100 m2 (it is the metric are, not a local
#: unit), so getting this wrong is a clean factor-of-100 error.
SQM_PER_ARE = 100.0
SQM_PER_HECTARE = 10_000.0
#: Java/Sunda listings also use tumbak (a.k.a. ubin). Commonly quoted as 14 m2;
#: the surveyed value is 14.0625 m2 and regional variation exists. Verify
#: against the source before relying on tumbak figures.
SQM_PER_TUMBAK = 14.0625

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


def parse_number(text: str) -> float | None:
    """Parse a number written under either separator convention.

    The rule: when both separators appear, the rightmost is the decimal point.
    When only one appears, three trailing digits mean it was a thousands
    separator ("1.500" / "250,000") and one or two mean it was a decimal
    point ("3,5" / "3.5").

    "1,500" is genuinely ambiguous — 1500 under English convention, 1.5 under
    Spanish or Indonesian. It resolves to 1500 here, because a bare grouped
    thousand is far more common in listing text than a decimal with trailing
    zeroes.

    This lives with the units rather than with prices because areas have the
    same problem: a Spanish listing's "parcela 1.100 m2" is 1100 square
    metres, and English rules read it as 1.1.
    """
    text = text.strip()
    if not text:
        return None

    has_dot = "." in text
    has_comma = "," in text

    if has_dot and has_comma:
        decimal_sep = "." if text.rfind(".") > text.rfind(",") else ","
        thousands_sep = "," if decimal_sep == "." else "."
        text = text.replace(thousands_sep, "").replace(decimal_sep, ".")
    elif has_dot or has_comma:
        sep = "." if has_dot else ","
        tail = text.rsplit(sep, 1)[1]
        if len(tail) == 3 or text.count(sep) > 1:
            text = text.replace(sep, "")
        else:
            text = text.replace(sep, ".")

    try:
        return float(text)
    except ValueError:
        return None


def to_float(value: object) -> float | None:
    text = clean(value)
    if text is None:
        return None
    return parse_number(text)


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


def are_to_sqm(are: float) -> float:
    return are * SQM_PER_ARE


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
        "are": are_to_sqm,
        "a": are_to_sqm,
        "hectare": lambda n: n * SQM_PER_HECTARE,
        "ha": lambda n: n * SQM_PER_HECTARE,
        "tumbak": lambda n: n * SQM_PER_TUMBAK,
        "ubin": lambda n: n * SQM_PER_TUMBAK,
    }
    key = unit.strip().lower()
    if key not in converters:
        raise ValueError(f"unknown area unit: {unit!r}")
    return round(converters[key](number), 2)
