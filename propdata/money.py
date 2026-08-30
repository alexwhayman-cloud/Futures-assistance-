"""Price parsing for listing text.

Registers give you numbers in columns. Portals give you "Rp 3,5 M",
"850 juta", "USD 250,000/year" and "IDR 1.500.000.000" — sometimes several
of them on the same page — and every one of those strings has a way of
becoming a wrong integer silently.

Three traps this module exists to handle:

1. **Indonesian decimal convention is inverted.** "1.500.000" is one and a
   half million; "3,5" is three point five. A naive parser that strips commas
   turns 3,5 into 35.
2. **"M" means different things by currency.** In Indonesian listings M is
   *miliar* — 10^9. In English listings M is million — 10^6. Same letter,
   1000x apart, and IDR amounts are large enough that neither reading looks
   obviously absurd.
3. **Rental prices are quoted like sale prices.** Bali leasehold is often
   advertised per year. Storing "USD 25,000/year" as an asking price makes a
   villa look 20x cheaper than it is, so `period` is returned and the caller
   must decide.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from propdata.units import parse_number

CURRENCY_SYMBOLS = {
    "rp": "IDR",
    "idr": "IDR",
    "rupiah": "IDR",
    "us$": "USD",
    "usd": "USD",
    "$": "USD",
    "£": "GBP",
    "gbp": "GBP",
    "€": "EUR",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "aud": "AUD",
    "sgd": "SGD",
}

#: Multiplier words. `m` is resolved per-currency — see MULTIPLIERS_BY_CURRENCY.
MULTIPLIERS = {
    "ribu": 1_000,
    "rb": 1_000,
    "k": 1_000,
    "thousand": 1_000,
    "juta": 1_000_000,
    "jt": 1_000_000,
    "mio": 1_000_000,
    "million": 1_000_000,
    "mil": 1_000,
    "millones": 1_000_000,
    "millon": 1_000_000,
    "mill": 1_000_000,
    "miliar": 1_000_000_000,
    "milyar": 1_000_000_000,
    "billion": 1_000_000_000,
    "bn": 1_000_000_000,
    "b": 1_000_000_000,
    "triliun": 1_000_000_000_000,
    "trillion": 1_000_000_000_000,
}

#: The ambiguous single letter, resolved by currency context.
MULTIPLIERS_BY_CURRENCY = {
    "IDR": {"m": 1_000_000_000},  # miliar
}
DEFAULT_M = 1_000_000  # million, everywhere else

#: Accent-folded before lookup, so "año" matches "ano".
PERIODS = {
    "year": "year",
    "ano": "year",
    "anual": "year",
    "anuales": "year",
    "yr": "year",
    "pa": "year",
    "annum": "year",
    "tahun": "year",
    "thn": "year",
    "month": "month",
    "bulan": "month",
    "mo": "month",
    "mes": "month",
    "mensual": "month",
    "night": "night",
    "malam": "night",
    "noche": "night",
    "semana": "week",
    "week": "week",
}

_ACCENTS = str.maketrans("áàâéèêíìîóòôúùûñç", "aaaeeeiiiooouuunc")


def _tokens(text: str) -> list[str]:
    """Word tokens, accent-folded so "año" and "ano" agree."""
    return re.findall(r"[a-z]+", text.translate(_ACCENTS))

_NUMBER = re.compile(r"\d[\d.,]*")

#: How far past the number a multiplier or period word may sit. Without a
#: window, a stray "mil" or "year" anywhere later in a long description gets
#: applied to the price.
_SUFFIX_WINDOW = 20

#: How far from the currency token a price may sit. Wide enough for
#: "Rp. 1.500.000.000" and "IDR 3,5 miliar", tight enough that a number in an
#: unrelated clause is not mistaken for the price.
_ANCHOR_WINDOW = 24


@dataclass(slots=True)
class Money:
    amount: int
    currency: str
    #: None for an outright price; "year"/"month"/"night" for a rental rate.
    #: A caller storing this as `asking_price` must check it is None.
    period: str | None = None


def _currency_span(text: str) -> tuple[int, int] | None:
    """Locate the currency token, so a price can be read next to it."""
    lowered = text.lower()
    best: tuple[int, int, int] | None = None
    for token in CURRENCY_SYMBOLS:
        pattern = (
            rf"\b{re.escape(token)}\b" if token[0].isalpha() else re.escape(token)
        )
        match = re.search(pattern, lowered)
        if match and (best is None or len(token) > best[0]):
            best = (len(token), match.start(), match.end())
    return None if best is None else (best[1], best[2])


def _anchored_number(text: str) -> re.Match[str] | None:
    """Find the number that belongs to the currency token.

    Scanning free text for the first number is how "Ocean view land, girik,
    luas tanah 10 are. Harga Rp 1.500.000.000" becomes a price of 10 — the
    land area is simply the first digit sequence on the page. So the search
    starts from the currency token and looks forward, then backward for the
    suffix convention ("3,5 miliar rupiah").
    """
    span = _currency_span(text)
    if span is None:
        # No currency token: the caller supplied a default currency and is
        # asserting the whole string is a price.
        return _NUMBER.search(text)

    start, end = span
    ahead = _NUMBER.search(text, end, end + _ANCHOR_WINDOW)
    if ahead is not None:
        return ahead

    behind = None
    for candidate in _NUMBER.finditer(text[max(0, start - _ANCHOR_WINDOW):start]):
        behind = candidate
    if behind is None:
        return None
    offset = max(0, start - _ANCHOR_WINDOW)
    return _NUMBER.search(text, offset + behind.start(), offset + behind.end())


def detect_currency(text: str) -> str | None:
    lowered = text.lower()
    # Longest token first so "us$" wins over "$".
    for token in sorted(CURRENCY_SYMBOLS, key=len, reverse=True):
        if token in lowered:
            return CURRENCY_SYMBOLS[token]
    return None


def parse_money(text: str, *, default_currency: str | None = None) -> Money | None:
    """Extract a single price from listing text.

    Returns None rather than guessing when there is no number, so a caller
    can distinguish "no price given" from "price of zero".
    """
    if not text:
        return None

    currency = detect_currency(text) or default_currency
    if currency is None:
        return None

    match = _anchored_number(text)
    if match is None:
        return None
    value = parse_number(match.group())
    if value is None:
        return None

    remainder = text[match.end():match.end() + _SUFFIX_WINDOW].lower()
    multiplier = 1
    for word in _tokens(remainder):
        if word == "m":
            multiplier = MULTIPLIERS_BY_CURRENCY.get(currency, {}).get("m", DEFAULT_M)
            break
        if word in MULTIPLIERS:
            multiplier = MULTIPLIERS[word]
            break
        if word in PERIODS:
            break  # a period word ends the amount; no multiplier applied

    period = None
    for word in _tokens(remainder):
        if word in PERIODS:
            period = PERIODS[word]
            break

    amount = value * multiplier
    if amount <= 0:
        return None
    return Money(amount=int(round(amount)), currency=currency, period=period)
