"""Turning a contact list into a validated outbox.

This produces messages and refusals. It does **not** send: no SMTP, no ESP
integration, no dialler. Same reasoning as the portal adapters not crawling —
choosing a transport means accepting its terms, its authentication, its rate
limits and its deliverability practices, and those are decisions to make
deliberately rather than inherit from a scaffold. The outbox is handed over
in a form a transport can consume.

The one rule worth stating loudly: **suppression is checked here, at build
time, against live state — and must be re-checked by whatever sends.** The
classic failure is building a list on Monday, sending on Friday, and mailing
someone who opted out on Wednesday. A list is a snapshot; permission is not.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from propdata.outreach.compliance import Decision, check_campaign, evaluate
from propdata.outreach.models import Campaign, Contact, MessageStatus
from propdata.outreach.store import OutreachStore


@dataclass(slots=True)
class OutboxEntry:
    message_id: str
    contact: Contact
    decision: Decision


@dataclass(slots=True)
class OutboxResult:
    campaign: Campaign
    queued: list[OutboxEntry] = field(default_factory=list)
    blocked: list[OutboxEntry] = field(default_factory=list)
    #: Set when the campaign itself is invalid; nothing is evaluated.
    campaign_error: Decision | None = None

    @property
    def refusal_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.blocked:
            counts[entry.decision.reason] = counts.get(entry.decision.reason, 0) + 1
        return counts

    def summary(self) -> str:
        if self.campaign_error:
            return (
                f"campaign refused: {self.campaign_error.reason} — "
                f"{self.campaign_error.detail}"
            )
        parts = [f"{len(self.queued)} queued", f"{len(self.blocked)} blocked"]
        for reason, count in sorted(self.refusal_counts.items()):
            parts.append(f"{reason}={count}")
        return ", ".join(parts)


def _message_id(campaign_id: str, contact_id: str) -> str:
    digest = hashlib.sha256(f"{campaign_id}|{contact_id}".encode()).hexdigest()
    return "msg:" + digest[:20]


def build_outbox(
    store: OutreachStore,
    campaign: Campaign,
    contacts: Iterable[Contact],
    *,
    skip_already_messaged: bool = True,
) -> OutboxResult:
    """Evaluate every contact and record the outcome, allowed or refused.

    Refusals are written to `messages` with status "blocked" and their reason.
    That is the audit trail: "we did not contact them" is a claim that needs
    evidence, and an absent row is not evidence.
    """
    result = OutboxResult(campaign=campaign)

    campaign_check = check_campaign(campaign)
    if not campaign_check.allowed:
        result.campaign_error = campaign_check
        return result

    store.save_campaign(campaign)
    now = datetime.now(timezone.utc)

    for contact in contacts:
        if skip_already_messaged and store.already_messaged(
            campaign.campaign_id, contact.contact_id
        ):
            continue

        # Live suppression check, not a snapshot taken when the list was built.
        identifier = contact.identifier_for(campaign.channel)
        suppressed = store.is_suppressed(campaign.channel, identifier)

        decision = evaluate(
            contact,
            campaign,
            organisation=store.get_organisation(contact.org_id),
            suppressed=suppressed,
        )

        message_id = _message_id(campaign.campaign_id, contact.contact_id)
        status = MessageStatus.QUEUED if decision.allowed else MessageStatus.BLOCKED
        store.record_message(
            message_id=message_id,
            campaign_id=campaign.campaign_id,
            contact_id=contact.contact_id,
            channel=campaign.channel,
            status=status.value,
            decision_basis=decision.basis.value if decision.basis else None,
            decision_reason=decision.reason,
            property_id=None,
            created_at=now,
        )

        entry = OutboxEntry(message_id, contact, decision)
        (result.queued if decision.allowed else result.blocked).append(entry)

    return result
