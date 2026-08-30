"""The adapter contract every source implements.

Four stages, deliberately separate:

    fetch     -> RawDocument   bytes off disk or the wire, untouched
    parse     -> RawRecord     structured records pulled out of a document
    normalise -> Property      canonical record, or None to drop the row
    load                       handled by `propdata.storage`, not the source

Keeping `parse` distinct from `fetch` looks like ceremony for a CSV register,
where it is one `csv.DictReader`. It earns its place on portal sources: that
is where you try JSON-LD, then an embedded JSON payload (`__NEXT_DATA__` and
friends), and only then fall back to DOM selectors — against the same fetched
document, so a portal changing its markup does not mean re-crawling it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from propdata.schema import Property, Provenance, Tier


@dataclass(slots=True)
class RawDocument:
    """One fetched artefact: a CSV file, an HTML page, an API response."""

    source_id: str
    content: bytes
    url: str | None = None
    retrieved_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RawRecord:
    """One structured record extracted from a document, pre-normalisation."""

    source_id: str
    record_id: str
    payload: dict[str, Any]
    retrieved_at: datetime
    url: str | None = None


class Source(ABC):
    """Base class for every data source.

    Subclasses set the class attributes and implement the three stages.
    `run` wires them together and is rarely worth overriding.
    """

    id: str
    country: str  # ISO 3166-1 alpha-2
    tier: Tier
    licence: str
    #: Human-readable note on what this source is good for and what it lacks.
    notes: str = ""

    @abstractmethod
    def fetch(self, **options: Any) -> Iterator[RawDocument]:
        """Yield raw documents. Must not interpret their contents."""

    @abstractmethod
    def parse(self, document: RawDocument) -> Iterator[RawRecord]:
        """Extract structured records from one document."""

    @abstractmethod
    def normalise(self, record: RawRecord) -> Property | None:
        """Map one record onto the canonical schema, or None to skip it."""

    def provenance_for(self, record: RawRecord) -> Provenance:
        return Provenance(
            source_id=self.id,
            source_record_id=record.record_id,
            retrieved_at=record.retrieved_at,
            licence=self.licence,
            tier=self.tier,
            source_url=record.url,
        )

    def run(self, **options: Any) -> Iterator[Property]:
        for document in self.fetch(**options):
            for record in self.parse(document):
                prop = self.normalise(record)
                if prop is not None:
                    yield prop
