"""Persistence for outreach entities.

Shares the SQLite file with the property data, because the whole point is to
target outreach off the property database — a separate store would mean
keeping two things in sync for no benefit at this size.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from propdata.db.migrations import migrate
from propdata.outreach.models import (
    Campaign,
    Channel,
    Contact,
    LawfulBasis,
    LegalForm,
    Organisation,
    Suppression,
    normalise_identifier,
)


def _iso(value: Any) -> str | None:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _parse_dt(value: Any) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class OutreachStore:
    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(str(path))
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.row_factory = sqlite3.Row
        migrate(self.connection)

    def __enter__(self) -> "OutreachStore":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    # -- organisations ---------------------------------------------------

    def save_organisation(self, org: Organisation) -> str:
        self.connection.execute(
            "INSERT OR REPLACE INTO organisations VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                org.org_id, org.country, org.name, org.legal_form.value,
                org.company_number, org.redress_scheme, org.website,
                json.dumps(org.admin_codes), org.source,
                _iso(org.created_at), org.notes,
            ),
        )
        self.connection.commit()
        return org.org_id

    def get_organisation(self, org_id: str | None) -> Organisation | None:
        if not org_id:
            return None
        row = self.connection.execute(
            "SELECT * FROM organisations WHERE org_id = ?", (org_id,)
        ).fetchone()
        if row is None:
            return None
        return Organisation(
            org_id=row["org_id"], country=row["country"], name=row["name"],
            legal_form=LegalForm(row["legal_form"]),
            company_number=row["company_number"],
            redress_scheme=row["redress_scheme"], website=row["website"],
            admin_codes=json.loads(row["admin_codes"] or "[]"),
            source=row["source"], notes=row["notes"],
            created_at=_parse_dt(row["created_at"]),
        )

    # -- contacts --------------------------------------------------------

    def save_contact(self, contact: Contact) -> str:
        self.connection.execute(
            "INSERT OR REPLACE INTO contacts VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                contact.contact_id, contact.org_id, contact.country,
                contact.full_name, contact.role, contact.email, contact.phone,
                contact.lawful_basis.value, contact.basis_source,
                _iso(contact.basis_recorded_at), _iso(contact.retain_until),
                _iso(contact.created_at), _iso(contact.updated_at),
            ),
        )
        self.connection.commit()
        return contact.contact_id

    def _contact_from_row(self, row: sqlite3.Row) -> Contact:
        return Contact(
            contact_id=row["contact_id"], org_id=row["org_id"],
            country=row["country"], full_name=row["full_name"],
            role=row["role"], email=row["email"], phone=row["phone"],
            lawful_basis=LawfulBasis(row["lawful_basis"]),
            basis_source=row["basis_source"],
            basis_recorded_at=_parse_dt(row["basis_recorded_at"]),
            retain_until=(
                date.fromisoformat(row["retain_until"])
                if row["retain_until"] else None
            ),
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )

    def contacts(
        self, *, country: str | None = None, admin_codes: Iterable[str] | None = None
    ) -> list[Contact]:
        """Contacts, optionally narrowed to organisations covering an area.

        Area matching is on the organisation's declared coverage, which is how
        outreach connects to the property database: pick the districts you have
        property data for, get the agents who work them.
        """
        sql = "SELECT c.* FROM contacts c"
        params: list[Any] = []
        wheres = []
        codes = list(admin_codes or [])
        if codes:
            sql += " JOIN organisations o ON o.org_id = c.org_id"
            wheres.append(
                "(" + " OR ".join(["o.admin_codes LIKE ?"] * len(codes)) + ")"
            )
            params.extend(f'%"{code}"%' for code in codes)
        if country:
            wheres.append("c.country = ?")
            params.append(country.upper())
        if wheres:
            sql += " WHERE " + " AND ".join(wheres)
        return [
            self._contact_from_row(row)
            for row in self.connection.execute(sql, params)
        ]

    # -- suppression -----------------------------------------------------

    def suppress(self, suppression: Suppression) -> None:
        """Record an opt-out. Idempotent, and never removed by this API.

        There is deliberately no `unsuppress`. Re-permission is a new consent
        event with its own evidence, not the deletion of a refusal.
        """
        self.connection.execute(
            "INSERT OR IGNORE INTO suppressions VALUES (?, ?, ?, ?, ?)",
            (
                suppression.channel.value, suppression.identifier,
                suppression.reason, suppression.source,
                _iso(suppression.created_at),
            ),
        )
        self.connection.commit()

    def is_suppressed(self, channel: Channel, identifier: str | None) -> bool:
        if not identifier:
            return False
        row = self.connection.execute(
            "SELECT 1 FROM suppressions WHERE channel = ? AND identifier = ?",
            (channel.value, normalise_identifier(channel, identifier)),
        ).fetchone()
        return row is not None

    # -- campaigns and messages ------------------------------------------

    def save_campaign(self, campaign: Campaign) -> str:
        self.connection.execute(
            "INSERT OR REPLACE INTO campaigns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                campaign.campaign_id, campaign.name, campaign.country,
                campaign.channel.value, campaign.purpose, campaign.sender_name,
                campaign.sender_address, campaign.opt_out_url,
                _iso(campaign.created_at), campaign.status,
            ),
        )
        self.connection.commit()
        return campaign.campaign_id

    def record_message(
        self, *, message_id: str, campaign_id: str, contact_id: str,
        channel: Channel, status: str, decision_basis: str | None,
        decision_reason: str, property_id: str | None, created_at: datetime,
    ) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO messages VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                message_id, campaign_id, contact_id, channel.value, status,
                decision_basis, decision_reason, property_id,
                _iso(created_at), None,
            ),
        )
        self.connection.commit()

    def messages(self, campaign_id: str, *, status: str | None = None):
        sql = "SELECT * FROM messages WHERE campaign_id = ?"
        params: list[Any] = [campaign_id]
        if status:
            sql += " AND status = ?"
            params.append(status)
        return list(self.connection.execute(sql, params))

    def already_messaged(self, campaign_id: str, contact_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM messages WHERE campaign_id = ? AND contact_id = ?",
            (campaign_id, contact_id),
        ).fetchone()
        return row is not None
