"""Source lookup by id, so the CLI does not import every adapter by hand."""

from __future__ import annotations

from propdata.sources.base import Source
from propdata.sources.es_listings import SpainListingsSource
from propdata.sources.id_bali import BaliListingsSource
from propdata.sources.uk_epc import UkEpcSource

SOURCES: dict[str, type[Source]] = {
    UkEpcSource.id: UkEpcSource,
    BaliListingsSource.id: BaliListingsSource,
    SpainListingsSource.id: SpainListingsSource,
}


def get_source(source_id: str) -> Source:
    try:
        return SOURCES[source_id]()
    except KeyError:
        known = ", ".join(sorted(SOURCES)) or "none registered"
        raise KeyError(f"unknown source {source_id!r}; known: {known}") from None
