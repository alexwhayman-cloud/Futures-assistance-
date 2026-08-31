"""Versioned schema migrations.

`CREATE TABLE IF NOT EXISTS` is not a migration strategy. It silently keeps an
existing table at whatever shape it already had, so a database created before
a column was added stays broken until something fails on insert — and this
schema has already changed twice, once for structured tenure and once for
per-country identity.

Migrations are append-only. To change the schema, add a new entry; never edit
an entry that has shipped, because databases in the field have already run it.
"""

from __future__ import annotations

import sqlite3

V1_PROPERTIES = """
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
    identity_confidence   TEXT,
    identity_tier         TEXT,
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
    tenure_restriction    TEXT,
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
CREATE INDEX IF NOT EXISTS idx_properties_identity
    ON properties (identity_confidence);

CREATE TABLE IF NOT EXISTS raw_records (
    property_id      TEXT NOT NULL,
    source_id        TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    retrieved_at     TEXT NOT NULL,
    payload          TEXT NOT NULL,
    PRIMARY KEY (property_id, source_id)
);
"""

V2_OUTREACH = """
-- Outreach records who may be contacted, on what legal basis, and what was
-- actually attempted. The audit trail is the point: `messages` keeps blocked
-- attempts with their reason, because "we never contacted them" is a claim
-- that needs evidence, not an absence of rows.

CREATE TABLE IF NOT EXISTS organisations (
    org_id          TEXT PRIMARY KEY,
    country         TEXT NOT NULL,
    name            TEXT NOT NULL,
    -- Drives whether PECR treats contacts here as corporate subscribers.
    legal_form      TEXT NOT NULL,
    company_number  TEXT,
    redress_scheme  TEXT,
    website         TEXT,
    admin_codes     TEXT,
    source          TEXT,
    created_at      TEXT NOT NULL,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS contacts (
    contact_id      TEXT PRIMARY KEY,
    org_id          TEXT REFERENCES organisations(org_id),
    country         TEXT NOT NULL,
    full_name       TEXT,
    role            TEXT,
    email           TEXT,
    phone           TEXT,
    lawful_basis    TEXT NOT NULL,
    basis_source    TEXT,
    basis_recorded_at TEXT,
    -- Data minimisation: a date after which this row should be deleted.
    retain_until    TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contacts_org ON contacts (org_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts (email);

-- Suppression is global and permanent, keyed on the normalised identifier
-- rather than on a contact row, so deleting and re-importing a contact cannot
-- resurrect someone who opted out.
CREATE TABLE IF NOT EXISTS suppressions (
    channel      TEXT NOT NULL,
    identifier   TEXT NOT NULL,
    reason       TEXT NOT NULL,
    source       TEXT,
    created_at   TEXT NOT NULL,
    PRIMARY KEY (channel, identifier)
);

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id     TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    country         TEXT NOT NULL,
    channel         TEXT NOT NULL,
    purpose         TEXT NOT NULL,
    sender_name     TEXT NOT NULL,
    sender_address  TEXT NOT NULL,
    opt_out_url     TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    status          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    message_id      TEXT PRIMARY KEY,
    campaign_id     TEXT NOT NULL REFERENCES campaigns(campaign_id),
    contact_id      TEXT NOT NULL REFERENCES contacts(contact_id),
    channel         TEXT NOT NULL,
    -- queued | blocked | sent | failed. "blocked" rows are kept deliberately.
    status          TEXT NOT NULL,
    decision_basis  TEXT,
    decision_reason TEXT NOT NULL,
    property_id     TEXT,
    created_at      TEXT NOT NULL,
    sent_at         TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_campaign ON messages (campaign_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_once
    ON messages (campaign_id, contact_id);
"""

#: Append-only. (version, description, sql)
MIGRATIONS: list[tuple[int, str, str]] = [
    (1, "properties and raw records", V1_PROPERTIES),
    (2, "outreach: organisations, contacts, suppressions, campaigns, messages",
     V2_OUTREACH),
]

LATEST = MIGRATIONS[-1][0]


class LegacyDatabase(RuntimeError):
    """Raised for a database written before migrations existed."""


def current_version(connection: sqlite3.Connection) -> int:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "  version    INTEGER PRIMARY KEY,"
        "  applied_at TEXT NOT NULL,"
        "  description TEXT NOT NULL)"
    )
    row = connection.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def _has_table(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def migrate(connection: sqlite3.Connection) -> int:
    """Bring a database up to `LATEST`. Returns the version it ends at.

    A database holding `properties` but no `schema_version` predates this
    module. Its column set cannot be inferred — the properties table changed
    shape twice before versioning existed — so it is refused rather than
    guessed at.
    """
    from datetime import datetime, timezone

    version = current_version(connection)
    if version == 0 and _has_table(connection, "properties"):
        raise LegacyDatabase(
            "database predates schema versioning and its shape cannot be "
            "inferred; rebuild it by re-running the ingest against a new file"
        )

    for number, description, sql in MIGRATIONS:
        if number <= version:
            continue
        connection.executescript(sql)
        connection.execute(
            "INSERT INTO schema_version VALUES (?, ?, ?)",
            (number, datetime.now(timezone.utc).isoformat(), description),
        )
        version = number
    connection.commit()
    return version
