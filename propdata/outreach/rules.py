"""Per-country direct-marketing rules.

Same shape as `regions.identity`: a table of countries, with the ones that
have actually been worked through marked `implemented` and everything else
refused rather than guessed at. Guessing here is worse than guessing about
cadastral keys — the failure mode is an unlawful send, not a bad join.

The UK is specified because it is the first market. Its regime is UK GDPR for
the personal data and PECR for the electronic marketing itself, and the two
ask different questions: GDPR asks whether there is a lawful basis to process
the data, PECR asks whether this particular channel may be used to market to
this particular subscriber. A contact can pass one and fail the other.

The PECR distinction that does the real work is **corporate subscriber versus
individual subscriber**. A limited company, PLC, LLP or Scottish partnership
is a corporate subscriber and may receive B2B marketing email without prior
consent. A sole trader or an ordinary partnership is treated as an individual
and may not. Since a large share of estate agencies are sole traders, this is
not an edge case.

None of this is legal advice, and it is a simplification of a regime with real
nuance. It encodes a conservative reading so that the system's default is to
refuse. Take advice before running an actual campaign.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from propdata.outreach.models import Channel, LegalForm

#: Forms whose contacts count as corporate subscribers under PECR.
UK_CORPORATE_FORMS = frozenset(
    {
        LegalForm.LIMITED_COMPANY,
        LegalForm.PLC,
        LegalForm.LLP,
        LegalForm.SCOTTISH_PARTNERSHIP,
    }
)


@dataclass(frozen=True, slots=True)
class MarketingRules:
    country: str
    #: False means nobody has worked this jurisdiction through. The gate
    #: refuses everything for such a country rather than applying UK rules to
    #: it, which would be both wrong and confident.
    implemented: bool
    regime: str
    #: Channels a corporate subscriber may be approached on without consent.
    corporate_channels_without_consent: frozenset[Channel] = frozenset()
    #: Legal forms that count as corporate subscribers.
    corporate_forms: frozenset[LegalForm] = frozenset()
    #: Channels always requiring consent (or soft opt-in) for an individual.
    individual_consent_channels: frozenset[Channel] = frozenset()
    opt_out_required: bool = True
    sender_identity_required: bool = True
    #: Screening register for telephone marketing, where one exists.
    phone_preference_service: str | None = None
    notes: str = ""
    #: Free-text obligations surfaced to the operator, not enforced in code.
    operator_obligations: tuple[str, ...] = field(default_factory=tuple)


REGISTRY: dict[str, MarketingRules] = {
    "GB": MarketingRules(
        country="GB",
        implemented=True,
        regime="UK GDPR + PECR",
        corporate_channels_without_consent=frozenset(
            {Channel.EMAIL, Channel.POST, Channel.PHONE}
        ),
        corporate_forms=UK_CORPORATE_FORMS,
        individual_consent_channels=frozenset(
            {Channel.EMAIL, Channel.SMS, Channel.PHONE}
        ),
        opt_out_required=True,
        sender_identity_required=True,
        phone_preference_service="CTPS (corporate) / TPS (individual)",
        notes=(
            "Sole traders and unincorporated partnerships are individual "
            "subscribers under PECR despite being businesses."
        ),
        operator_obligations=(
            "Screen phone numbers against CTPS/TPS before calling; this "
            "system does not do that for you.",
            "Every message must identify the sender and carry a working "
            "opt-out.",
            "Corporate email without consent still requires a UK GDPR lawful "
            "basis for the personal data of the named individual.",
            "Honour an opt-out across all campaigns, not just the one it "
            "came from.",
        ),
    ),
    # Declared, not implemented. Present so that the refusal names a real
    # regime instead of saying "unknown country".
    "IE": MarketingRules("IE", False, "GDPR + ePrivacy (S.I. 336/2011)"),
    "ES": MarketingRules("ES", False, "GDPR + LSSI-CE + LGT"),
    "FR": MarketingRules("FR", False, "GDPR + ePrivacy (CNIL guidance)"),
    "NZ": MarketingRules("NZ", False, "Unsolicited Electronic Messages Act"),
    "SG": MarketingRules("SG", False, "PDPA (incl. Do Not Call registry)"),
    "CZ": MarketingRules("CZ", False, "GDPR + ePrivacy"),
}

UNKNOWN_COUNTRY = MarketingRules(
    country="??", implemented=False, regime="unknown",
    notes="No rules recorded for this country.",
)


def get(country: str | None) -> MarketingRules:
    if not country:
        return UNKNOWN_COUNTRY
    return REGISTRY.get(country.upper(), UNKNOWN_COUNTRY)
