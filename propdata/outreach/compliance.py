"""The gate every message passes through.

One function decides whether a contact may be approached, and it is the only
place that decision is made. Anything wanting to send has to come through
here, and it returns a `Decision` that gets written to the audit log whether
it allowed or refused — a refusal with a reason is more useful evidence than
a row that was never written.

The gate is ordered so that the cheapest and most absolute checks run first,
and so that a refusal names the first real reason rather than an incidental
one. Suppression outranks everything, including consent: someone who opted out
after giving consent has withdrawn it, and the withdrawal is what counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from propdata.outreach import rules as rules_module
from propdata.outreach.models import (
    Campaign,
    Channel,
    Contact,
    LawfulBasis,
    LegalForm,
    Organisation,
)


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    #: Short machine-readable code, stored in the audit log.
    reason: str
    #: The basis relied on, when allowed.
    basis: LawfulBasis | None = None
    #: Human explanation, for an operator reading the log later.
    detail: str = ""


def check_campaign(campaign: Campaign) -> Decision:
    """Validate the campaign itself, before any contact is considered.

    A campaign missing its sender identity or opt-out is unlawful for every
    recipient, so it fails once here rather than once per contact.
    """
    rules = rules_module.get(campaign.country)
    if not rules.implemented:
        return Decision(
            False,
            "country_not_implemented",
            detail=(
                f"no marketing rules implemented for {campaign.country} "
                f"(regime: {rules.regime}); refusing rather than applying "
                "another country's rules"
            ),
        )
    if rules.sender_identity_required and not (
        campaign.sender_name.strip() and campaign.sender_address.strip()
    ):
        return Decision(
            False, "missing_sender_identity",
            detail="sender name and postal address are required on every message",
        )
    if rules.opt_out_required and not campaign.opt_out_url.strip():
        return Decision(
            False, "missing_opt_out",
            detail="every message must carry a working opt-out",
        )
    if not campaign.purpose.strip():
        return Decision(
            False, "missing_purpose",
            detail="a lawful basis is claimed for a stated purpose, not in general",
        )
    return Decision(True, "campaign_valid")


def is_corporate_subscriber(
    organisation: Organisation | None, rules: rules_module.MarketingRules
) -> bool:
    """Whether this organisation's contacts are corporate subscribers.

    Unknown legal form is treated as *not* corporate. A sole trader wrongly
    classified as a limited company is an unlawful send; the reverse is a
    missed email.
    """
    if organisation is None:
        return False
    if organisation.legal_form is LegalForm.UNKNOWN:
        return False
    return organisation.legal_form in rules.corporate_forms


def evaluate(
    contact: Contact,
    campaign: Campaign,
    *,
    organisation: Organisation | None = None,
    suppressed: bool = False,
    today: date | None = None,
) -> Decision:
    """Decide whether `contact` may be approached for `campaign`.

    `suppressed` is passed in rather than looked up so that the caller must
    have checked it against live state at send time — see `campaign.py`.
    """
    rules = rules_module.get(campaign.country)

    if not rules.implemented:
        return Decision(
            False, "country_not_implemented",
            detail=f"no marketing rules implemented for {campaign.country}",
        )

    # Suppression first, and above consent: an opt-out recorded after consent
    # is a withdrawal of that consent.
    if suppressed:
        return Decision(
            False, "suppressed",
            detail="identifier is on the suppression list; this is permanent "
                   "and applies across all campaigns",
        )

    if contact.country.upper() != campaign.country.upper():
        return Decision(
            False, "country_mismatch",
            detail=f"contact is in {contact.country}, campaign targets "
                   f"{campaign.country}; rules differ by jurisdiction",
        )

    identifier = contact.identifier_for(campaign.channel)
    if not identifier:
        return Decision(
            False, "no_identifier",
            detail=f"contact has no {campaign.channel.value} identifier",
        )

    if contact.retain_until is not None:
        if (today or date.today()) > contact.retain_until:
            return Decision(
                False, "retention_expired",
                detail=f"retention period ended {contact.retain_until}; the "
                       "record should have been deleted",
            )

    # Consent is decisive wherever it exists, regardless of subscriber type.
    if contact.lawful_basis is LawfulBasis.CONSENT:
        return Decision(
            True, "consent", LawfulBasis.CONSENT,
            detail=f"consent recorded {contact.basis_recorded_at or 'at unknown date'}"
                   f" via {contact.basis_source or 'unrecorded source'}",
        )

    corporate = is_corporate_subscriber(organisation, rules)

    if corporate and campaign.channel in rules.corporate_channels_without_consent:
        # PECR permits the channel; UK GDPR still needs a basis for the named
        # individual's personal data, and legitimate interests is the usual
        # one. Requiring it to be recorded stops "B2B" being used as a reason
        # to record nothing at all.
        if contact.lawful_basis is LawfulBasis.LEGITIMATE_INTERESTS:
            return Decision(
                True, "corporate_subscriber", LawfulBasis.LEGITIMATE_INTERESTS,
                detail=f"{organisation.legal_form.value} is a corporate "
                       f"subscriber; {campaign.channel.value} permitted "
                       "without prior consent",
            )
        return Decision(
            False, "no_lawful_basis_recorded",
            detail="corporate subscriber, so the channel is permitted, but no "
                   "lawful basis is recorded for the individual's personal "
                   "data; record legitimate interests with an assessment",
        )

    if contact.lawful_basis is LawfulBasis.SOFT_OPT_IN:
        if campaign.channel in rules.individual_consent_channels:
            return Decision(
                True, "soft_opt_in", LawfulBasis.SOFT_OPT_IN,
                detail="existing-customer exemption; marketing must be for "
                       "similar products and carry an opt-out",
            )

    if campaign.channel in rules.individual_consent_channels:
        why = (
            "individual subscriber"
            if organisation is None or not corporate
            else "channel not permitted without consent"
        )
        return Decision(
            False, "consent_required",
            detail=f"{why}; {campaign.channel.value} to an individual "
                   "subscriber requires consent or the soft opt-in exemption",
        )

    # Channels outside the electronic-marketing rules — postal mail — still
    # need a GDPR basis, but not consent.
    if contact.lawful_basis in (
        LawfulBasis.LEGITIMATE_INTERESTS,
        LawfulBasis.SOFT_OPT_IN,
    ):
        return Decision(
            True, "non_electronic_channel", contact.lawful_basis,
            detail=f"{campaign.channel.value} is outside PECR; lawful basis "
                   "recorded for the processing",
        )

    return Decision(
        False, "no_lawful_basis_recorded",
        detail="no lawful basis recorded for this contact",
    )
