"""SQLite sink.

SQLite because the interesting problems here are schema and provenance, not
throughput, and a single file keeps the scaffold runnable with no services.
Swapping in Postgres or Parquet later is a matter of reimplementing `Store`;
nothing above it knows the difference.

Two tables, on purpose:

* `properties`  one row per (property_id, source_id) — the normalised view.
* `raw_records` the untouched source payload, keyed the same way.

Keeping raw records means a mapping bug is a re-normalise, not a re-crawl.
For portal sources, where re-fetching is slow, rate-limited and legally
awkward, that distinction is most of the value.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from propdata.schema import Property

SCHEMA = """
CREATE TABLE IF NOT EXISTS properties (
    property_id           TEXT NOT NULL,
    source_id             TEXT NOT NULL,
    source_record_id      TEXT NOT NULL,
    tier                  TEXT NOT NULL,
    licence               TEXT NOT NULL,
    source_url            TEXT,
    retrieved_at          TEXT NOT NULL,
    country               TEXT NOT NULL,
    postcode              TEXT,
    address_lines         TEXT,
    admin_code            TEXT,
    uprn                  TEXT,
    latitude              REAL,
    longitude             REAL,
    property_type         TEXT,
    built_form            TEXT,
    tenure_family         TEXT,
    tenure_local_name     TEXT,
    tenure_local_code     TEXT,
    tenure_years_left     INTEGER,
    tenure_foreign_ok     INTEGER,
    occupancy             TEXT,
    floor_area_sqm        REAL,
    land_area_sqm         REAL,
    habitable_rooms       INTEGER,
    bedrooms              INTEGER,
    bathrooms             INTEGER,
    construction_age_band TEXT,
    energy_band           TEXT,
    energy_score          INTEGER,
    assessed_on           TEXT,
    asking_price          INTEGER,
    price_currency        TEXT,
    listed_on             TEXT,
    PRIMARY KEY (property_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_properties_postcode ON properties (postcode);
CREATE INDEX IF NOT EXISTS idx_properties_uprn ON properties (uprn);
CREATE INDEX IF NOT EXISTS idx_properties_admin ON properties (admin_code);

CREATE TABLE IF NOT EXISTS raw_records (
    property_id      TEXT NOT NULL,
    source_id        TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    retrieved_at     TEXT NOT NULL,
    payload          TEXT NOT NULL,
    PRIMARY KEY (property_id, source_id)
);
"""

#: Replace an existing row only when the incoming record is at least as recent.
#: EPC re-assessments mean the same dwelling arrives many times; without this
#: the last row physically read wins, which is arbitrary.
UPSERT = """
INSERT INTO properties VALUES (
    :property_id, :source_id, :source_record_id, :tier, :licence, :source_url,
    :retrieved_at, :country, :postcode, :address_lines, :admin_code, :uprn,
    :latitude, :longitude, :property_type, :built_form, :tenure_family,
    :tenure_local_name, :tenure_local_code, :tenure_years_left,
    :tenure_foreign_ok, :occupancy, :floor_area_sqm, :land_area_sqm,
    :habitable_rooms, :bedrooms, :bathrooms, :construction_age_band,
    :energy_band, :energy_score, :assessed_on, :asking_price,
    :price_currency, :listed_on
)
ON CONFLICT (property_id, source_id) DO UPDATE SET
    source_record_id      = excluded.source_record_id,
    source_url            = excluded.source_url,
    retrieved_at          = excluded.retrieved_at,
    postcode              = excluded.postcode,
    address_lines         = excluded.address_lines,
    admin_code            = excluded.admin_code,
    uprn                  = excluded.uprn,
    property_type         = excluded.property_type,
    built_form            = excluded.built_form,
    tenure_family         = excluded.tenure_family,
    tenure_local_name     = excluded.tenure_local_name,
    tenure_local_code     = excluded.tenure_local_code,
    tenure_years_left     = excluded.tenure_years_left,
    tenure_foreign_ok     = excluded.tenure_foreign_ok,
    occupancy             = excluded.occupancy,
    floor_area_sqm        = excluded.floor_area_sqm,
    land_area_sqm         = excluded.land_area_sqm,
    habitable_rooms       = excluded.habitable_rooms,
    bedrooms              = excluded.bedrooms,
    bathrooms             = excluded.bathrooms,
    construction_age_band = excluded.construction_age_band,
    energy_band           = excluded.energy_band,
    energy_score          = excluded.energy_score,
    assessed_on           = excluded.assessed_on,
    asking_price          = excluded.asking_price,
    price_currency        = excluded.price_currency,
    listed_on             = excluded.listed_on
WHERE COALESCE(excluded.assessed_on, '') >= COALESCE(properties.assessed_on, '')
"""


def _iso(value: Any) -> str | None:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _row(prop: Property) -> dict[str, Any]:
    energy = prop.energy
    tenure = prop.legal_tenure
    return {
        "property_id": prop.property_id,
        "source_id": prop.provenance.source_id,
        "source_record_id": prop.provenance.source_record_id,
        "tier": prop.provenance.tier.value,
        "licence": prop.provenance.licence,
        "source_url": prop.provenance.source_url,
        "retrieved_at": _iso(prop.provenance.retrieved_at),
        "country": prop.address.country,
        "postcode": prop.address.postcode,
        "address_lines": json.dumps(prop.address.lines),
        "admin_code": prop.address.admin_code,
        "uprn": prop.address.uprn,
        "latitude": prop.address.latitude,
        "longitude": prop.address.longitude,
        "property_type": prop.property_type.value,
        "built_form": prop.built_form.value,
        "tenure_family": tenure.family.value if tenure else None,
        "tenure_local_name": tenure.local_name if tenure else None,
        "tenure_local_code": tenure.local_code if tenure else None,
        "tenure_years_left": tenure.years_remaining if tenure else None,
        "tenure_foreign_ok": (
            None
            if tenure is None or tenure.foreign_holdable is None
            else int(tenure.foreign_holdable)
        ),
        "occupancy": prop.occupancy.value,
        "floor_area_sqm": prop.floor_area_sqm,
        "land_area_sqm": prop.land_area_sqm,
        "habitable_rooms": prop.habitable_rooms,
        "bedrooms": prop.bedrooms,
        "bathrooms": prop.bathrooms,
        "construction_age_band": prop.construction_age_band,
        "energy_band": energy.current_band if energy else None,
        "energy_score": energy.current_score if energy else None,
        "assessed_on": _iso(energy.assessed_on) if energy else None,
        "asking_price": prop.asking_price,
        "price_currency": prop.price_currency,
        "listed_on": _iso(prop.listed_on),
    }


class Store:
    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(str(path))
        self.connection.executescript(SCHEMA)

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def write(self, properties: Iterable[Property], *, keep_raw: bool = True) -> int:
        """Upsert properties. Returns the number of records processed."""
        count = 0
        for prop in properties:
            self.connection.execute(UPSERT, _row(prop))
            if keep_raw and prop.raw:
                self.connection.execute(
                    "INSERT OR REPLACE INTO raw_records VALUES (?, ?, ?, ?, ?)",
                    (
                        prop.property_id,
                        prop.provenance.source_id,
                        prop.provenance.source_record_id,
                        _iso(prop.provenance.retrieved_at),
                        json.dumps(prop.raw, default=str),
                    ),
                )
            count += 1
        self.connection.commit()
        return count

    def count(self) -> int:
        cursor = self.connection.execute("SELECT COUNT(*) FROM properties")
        return int(cursor.fetchone()[0])

    def close(self) -> None:
        self.connection.close()
