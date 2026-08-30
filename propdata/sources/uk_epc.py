"""UK EPC register (England & Wales) — Tier 1 structural attributes.

Why this source first: it is the largest openly-licensed source of property
*attributes* in the UK. Roughly 25M domestic certificates carrying floor area,
property type, built form, habitable rooms, construction age band and, on
newer records, a UPRN. Transaction datasets tell you what a property sold for;
this tells you what the property actually is.

Licence: Open Government Licence v3.0, subject to the register's terms of use.
Bulk download and API both require free registration at
https://epc.opendatacommunities.org/.

Two things to know before trusting the output:

1. A row is a *certificate*, not a property. Properties are re-assessed, so
   the same dwelling appears repeatedly with different LMK keys. `storage`
   upserts on (property_id, source_id) keeping the newest assessment; do not
   count rows and call it a dwelling count.
2. EPC "TENURE" is occupancy, not legal tenure — "Owner-occupied" says nothing
   about freehold vs leasehold. It maps to `occupancy`; `legal_tenure` stays
   UNKNOWN and must come from a different source (HM Land Registry).
"""

from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from propdata import units
from propdata.schema import (
    Address,
    BuiltForm,
    EnergyRating,
    Occupancy,
    Property,
    PropertyType,
    Tier,
    make_property_id,
)
from propdata.sources.base import RawDocument, RawRecord, Source

PROPERTY_TYPES = {
    "house": PropertyType.HOUSE,
    "flat": PropertyType.FLAT,
    "maisonette": PropertyType.MAISONETTE,
    "bungalow": PropertyType.BUNGALOW,
    "park home": PropertyType.PARK_HOME,
}

BUILT_FORMS = {
    "detached": BuiltForm.DETACHED,
    "semi-detached": BuiltForm.SEMI_DETACHED,
    "mid-terrace": BuiltForm.MID_TERRACE,
    "end-terrace": BuiltForm.END_TERRACE,
    "enclosed mid-terrace": BuiltForm.MID_TERRACE,
    "enclosed end-terrace": BuiltForm.END_TERRACE,
}

OCCUPANCY = {
    "owner-occupied": Occupancy.OWNER_OCCUPIED,
    "rental (private)": Occupancy.RENTED_PRIVATE,
    "rental (social)": Occupancy.RENTED_SOCIAL,
    "rented (private)": Occupancy.RENTED_PRIVATE,
    "rented (social)": Occupancy.RENTED_SOCIAL,
}


def _key(name: str) -> str:
    """Normalise a header cell.

    The bulk CSVs ship UPPER-HYPHENATED headers and the API returns
    lower-hyphenated keys for the same fields. Normalising both to
    lower-hyphen means one mapping table instead of two.
    """
    return name.strip().lower().replace("_", "-").lstrip("﻿")


class UkEpcSource(Source):
    id = "uk-epc"
    country = "GB"
    tier = Tier.REGISTER
    licence = "OGL-3.0 (EPC Register terms of use)"
    notes = (
        "Structural attributes for England & Wales. No price, no photos, "
        "no legal tenure. Scotland has a separate register."
    )

    def fetch(
        self,
        *,
        path: str | Path | None = None,
        **_: Any,
    ) -> Iterator[RawDocument]:
        """Read the bulk download from disk.

        Accepts the distribution as it actually arrives: the downloaded .zip,
        a single certificates.csv, or the unpacked directory tree (which nests
        one certificates.csv per local authority).
        """
        if path is None:
            raise ValueError("uk-epc fetch requires path= to the bulk download")

        # Resolved, because source_url is recorded as a file:// URI and
        # Path.as_uri() rejects relative paths.
        target = Path(path).expanduser().resolve()
        if not target.exists():
            raise FileNotFoundError(target)

        if target.is_dir():
            files = sorted(target.rglob("certificates.csv"))
            if not files:
                raise FileNotFoundError(f"no certificates.csv under {target}")
            for csv_path in files:
                yield RawDocument(
                    source_id=self.id,
                    content=csv_path.read_bytes(),
                    url=csv_path.as_uri(),
                )
        elif target.suffix.lower() == ".zip":
            with zipfile.ZipFile(target) as archive:
                for name in archive.namelist():
                    if name.endswith("certificates.csv"):
                        yield RawDocument(
                            source_id=self.id,
                            content=archive.read(name),
                            url=f"{target.as_uri()}!{name}",
                        )
        else:
            yield RawDocument(
                source_id=self.id,
                content=target.read_bytes(),
                url=target.as_uri(),
            )

    def parse(self, document: RawDocument) -> Iterator[RawRecord]:
        text = document.content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            payload = {_key(k): v for k, v in row.items() if k is not None}
            record_id = units.clean(payload.get("lmk-key"))
            if record_id is None:
                # No certificate key means nothing downstream can reference
                # this row or detect it as a duplicate. Drop it.
                continue
            yield RawRecord(
                source_id=self.id,
                record_id=record_id,
                payload=payload,
                retrieved_at=document.retrieved_at,
                url=document.url,
            )

    def normalise(self, record: RawRecord) -> Property | None:
        row = record.payload

        lines = [
            line
            for line in (
                units.clean(row.get("address1")),
                units.clean(row.get("address2")),
                units.clean(row.get("address3")),
            )
            if line
        ]
        postcode = units.clean(row.get("postcode"))
        if not lines and not postcode:
            return None

        address = Address(
            country=self.country,
            lines=lines,
            postcode=postcode,
            locality=units.clean(row.get("posttown")),
            region=units.clean(row.get("county")),
            uprn=units.clean(row.get("uprn")),
        )

        age_band = units.clean(row.get("construction-age-band"))
        if age_band:
            # Stored as "England and Wales: 1983-1990"; the jurisdiction
            # prefix is already implied by the source.
            age_band = age_band.split(":", 1)[-1].strip()

        energy = EnergyRating(
            scheme="EPC-EnglandWales",
            current_band=units.clean(row.get("current-energy-rating")),
            potential_band=units.clean(row.get("potential-energy-rating")),
            current_score=units.to_int(row.get("current-energy-efficiency")),
            assessed_on=units.to_date(row.get("inspection-date")),
        )

        return Property(
            property_id=make_property_id(address),
            address=address,
            provenance=self.provenance_for(record),
            property_type=self._lookup(
                PROPERTY_TYPES, row.get("property-type"), PropertyType.UNKNOWN
            ),
            built_form=self._lookup(
                BUILT_FORMS, row.get("built-form"), BuiltForm.UNKNOWN
            ),
            # legal_tenure stays None: EPC has no tenure certificate field,
            # and its TENURE column is occupancy. See module docstring.
            occupancy=self._lookup(OCCUPANCY, row.get("tenure"), Occupancy.UNKNOWN),
            floor_area_sqm=units.normalise_area(
                row.get("total-floor-area"), "sqm"
            ),
            habitable_rooms=units.to_int(row.get("number-habitable-rooms")),
            construction_age_band=age_band,
            energy=energy,
            raw=row,
        )

    @staticmethod
    def _lookup(table: dict[str, Any], value: object, default: Any) -> Any:
        text = units.clean(value)
        if text is None:
            return default
        return table.get(text.lower(), default)
