"""Matching register entries to each other to evidence legal form.

An HMRC AML entry names a business but not its legal form. A Companies House
entry states the form but cannot contain sole traders. Matching the first to
the second turns a guess into evidence — and, just as usefully, leaves the
unmatched ones flagged as probable sole traders.

The matcher refuses ambiguity. If a normalised name matches more than one
company, no match is recorded, because picking one of them would assign a
legal form on a coin flip and the coin landing "limited company" authorises a
marketing email. Failing to match costs an email; matching wrongly is
unlawful.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, replace

from propdata.outreach.models import LegalForm, Organisation

#: Legal suffixes stripped before comparison. Deliberately only legal forms —
#: stripping words like "group" or "properties" would merge businesses that
#: are genuinely different.
_SUFFIXES = (
    "limited", "ltd", "plc", "llp", "lp", "cyfyngedig", "cyf",
    "company", "co", "incorporated", "inc",
)
_SUFFIX_PATTERN = re.compile(
    r"\b(" + "|".join(_SUFFIXES) + r")\b\.?\s*$", re.I
)


def normalise_name(name: str) -> str:
    """Comparison key for a business name.

    Lowercases, drops punctuation and the definite article, and strips
    trailing legal suffixes — repeatedly, since "Smith Estates Co Ltd" carries
    two.
    """
    cleaned = re.sub(r"[^\w\s]", " ", (name or "").lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned.startswith("the "):
        cleaned = cleaned[4:]
    while True:
        stripped = _SUFFIX_PATTERN.sub("", cleaned).strip()
        if stripped == cleaned:
            return cleaned
        if not stripped:
            # A name made entirely of legal suffixes ("The Company Ltd").
            # Stripping to nothing would make it match every other such name,
            # so keep the last non-empty form.
            return cleaned
        cleaned = stripped


@dataclass(slots=True)
class MatchReport:
    matched: list[Organisation]
    #: Names that hit more than one company. Left unmatched on purpose.
    ambiguous: list[str]
    #: No company of that name — very likely a sole trader or partnership.
    unmatched: list[Organisation]

    def summary(self) -> str:
        return (
            f"{len(self.matched)} matched, {len(self.ambiguous)} ambiguous, "
            f"{len(self.unmatched)} unmatched (likely sole traders)"
        )


def index_by_name(companies: Iterable[Organisation]) -> dict[str, list[Organisation]]:
    index: dict[str, list[Organisation]] = {}
    for company in companies:
        index.setdefault(normalise_name(company.name), []).append(company)
    return index


def match_to_companies_house(
    unevidenced: Iterable[Organisation],
    companies: Iterable[Organisation],
) -> MatchReport:
    """Upgrade organisations whose legal form is unknown, where evidence exists.

    Returns organisations, never mutating the inputs. A matched organisation
    keeps its own identity and source but gains the company number and legal
    form from the register entry, with the evidence recorded in `notes`.
    """
    index = index_by_name(companies)
    report = MatchReport(matched=[], ambiguous=[], unmatched=[])

    for org in unevidenced:
        candidates = index.get(normalise_name(org.name), [])

        if len(candidates) == 1:
            company = candidates[0]
            report.matched.append(
                replace(
                    org,
                    legal_form=company.legal_form,
                    company_number=company.company_number,
                    notes=(
                        f"{org.notes or ''}; legal form evidenced by "
                        f"Companies House {company.company_number}"
                    ).lstrip("; "),
                )
            )
        elif len(candidates) > 1:
            # Two companies share this name once suffixes are stripped.
            # Assigning either one's legal form would be a coin flip that can
            # authorise a marketing email, so record the ambiguity instead.
            report.ambiguous.append(org.name)
            report.unmatched.append(
                replace(
                    org,
                    legal_form=LegalForm.UNKNOWN,
                    notes=(
                        f"{org.notes or ''}; {len(candidates)} Companies House "
                        "entries share this name — left unevidenced"
                    ).lstrip("; "),
                )
            )
        else:
            report.unmatched.append(
                replace(
                    org,
                    notes=(
                        f"{org.notes or ''}; no Companies House entry — likely "
                        "a sole trader or unincorporated partnership"
                    ).lstrip("; "),
                )
            )

    return report
