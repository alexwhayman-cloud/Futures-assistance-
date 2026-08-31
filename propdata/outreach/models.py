"""Outreach entities.

Deliberately small. The interesting logic is in `rules` and `compliance`; this
module only names things.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum


class Channel(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    #: Postal mail is outside PECR — GDPR still applies, but the consent rules
    #: for electronic mail do not. Kept distinct for that reason.
    POST = "post"


class LegalForm(str, Enum):
    """Legal form of an organisation.

    This is not bookkeeping. Under PECR a limited company is a *corporate
    subscriber* and may receive B2B marketing email without prior consent,
    while a sole trader or an unincorporated partnership is an *individual
    subscriber* and may not. The distinction turns entirely on this field.
    """

    LIMITED_COMPANY = "limited_company"
    PLC = "plc"
    LLP = "llp"
    #: Scottish partnerships have separate legal personality, unlike
    #: unincorporated partnerships elsewhere in the UK.
    SCOTTISH_PARTNERSHIP = "scottish_partnership"
    SOLE_TRADER = "sole_trader"
    PARTNERSHIP = "partnership"
    OTHER = "other"
    UNKNOWN = "unknown"


class LawfulBasis(str, Enum):
    """Why this contact may lawfully be marketed to."""

    CONSENT = "consent"
    LEGITIMATE_INTERESTS = "legitimate_interests"
    #: Existing-customer exemption: their details were obtained during a sale
    #: or negotiation, the marketing is for similar products, and an opt-out
    #: was offered at collection and in every message since.
    SOFT_OPT_IN = "soft_opt_in"
    NONE = "none"


class MessageStatus(str, Enum):
    QUEUED = "queued"
    BLOCKED = "blocked"
    SENT = "sent"
    FAILED = "failed"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalise_identifier(channel: Channel, value: str) -> str:
    """Canonical form of a contact identifier, for suppression matching.

    Suppression that misses because someone typed a capital letter is not
    suppression. Email is lowercased and trimmed; phone numbers keep only
    digits and a leading +.
    """
    value = (value or "").strip()
    if channel in (Channel.PHONE, Channel.SMS):
        digits = re.sub(r"[^\d+]", "", value)
        return "+" + digits.lstrip("+") if digits else ""
    return value.lower()


def _identity_hash(*parts: str) -> str:
    basis = "|".join(p or "" for p in parts)
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]


@dataclass(slots=True)
class Organisation:
    country: str
    name: str
    legal_form: LegalForm = LegalForm.UNKNOWN
    company_number: str | None = None
    #: UK estate agents must belong to a redress scheme (TPO or PRS). Its
    #: presence is a decent signal that a business is a real trading agency.
    redress_scheme: str | None = None
    website: str | None = None
    admin_codes: list[str] = field(default_factory=list)
    source: str | None = None
    notes: str | None = None
    org_id: str = ""
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not self.org_id:
            self.org_id = "org:" + _identity_hash(
                self.country, self.name.lower(), self.company_number or ""
            )


@dataclass(slots=True)
class Contact:
    country: str
    org_id: str | None = None
    full_name: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    lawful_basis: LawfulBasis = LawfulBasis.NONE
    basis_source: str | None = None
    basis_recorded_at: datetime | None = None
    retain_until: date | None = None
    contact_id: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not self.contact_id:
            self.contact_id = "contact:" + _identity_hash(
                self.country, (self.email or "").lower(), self.phone or "",
                self.full_name or "",
            )

    def identifier_for(self, channel: Channel) -> str | None:
        raw = self.phone if channel in (Channel.PHONE, Channel.SMS) else self.email
        if not raw:
            return None
        return normalise_identifier(channel, raw)


@dataclass(slots=True)
class Campaign:
    name: str
    country: str
    channel: Channel
    #: What this campaign is for, in one line. Recorded because a lawful basis
    #: is claimed for a stated purpose, not in general.
    purpose: str
    sender_name: str
    sender_address: str
    opt_out_url: str
    campaign_id: str = ""
    status: str = "draft"
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not self.campaign_id:
            self.campaign_id = "campaign:" + _identity_hash(
                self.country, self.name.lower(), self.channel.value
            )


@dataclass(slots=True)
class Suppression:
    channel: Channel
    identifier: str
    reason: str
    source: str | None = None
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        self.identifier = normalise_identifier(self.channel, self.identifier)
