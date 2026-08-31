"""Companies House basic company data — UK incorporated estate agencies.

The strongest available source for this purpose, for a reason that is easy to
miss: **Companies House contains no sole traders at all.** They are not
registered anywhere in it. So every organisation this loader yields is an
incorporated body whose legal form is stated by the register itself, which is
exactly the evidence PECR's corporate-subscriber test needs.

The corollary matters just as much. A list built only from Companies House is
structurally incapable of containing the sole-trader agencies that make up a
large share of the market. That is a coverage gap, not a bug — and filling it
from HMRC's AML register is what `hmrc_aml.py` is for.

Source: the free monthly "Basic Company Data" snapshot published under the
Open Government Licence. Roughly 5M rows covering every company on the
register, so filtering is done during parse rather than after.

**No email addresses.** Companies House publishes a registered office address
and nothing else contactable. This loader therefore produces organisations
only; contacts have to come from somewhere else, with their own lawful basis
recorded. That separation is deliberate — this register cannot by itself
produce a send list.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from propdata.outreach.loaders.base import (
    OrganisationSource,
    pick,
    read_csv_rows,
    read_files,
)
from propdata.outreach.models import LegalForm, Organisation

#: SIC codes for the sector. 68310 is the core one; 68320 is management on a
#: fee or contract basis, which is the same businesses in practice.
DEFAULT_SIC_CODES = ("68310", "68320")

#: Companies House `CompanyCategory` -> our legal form. Categories not listed
#: map to OTHER rather than being guessed at; OTHER is not corporate for
#: PECR purposes, so an unmapped category fails safe.
COMPANY_CATEGORIES: dict[str, LegalForm] = {
    "private limited company": LegalForm.LIMITED_COMPANY,
    "priv ltd sect. 30 (private limited company, section 30 of the companies act)":
        LegalForm.LIMITED_COMPANY,
    "private unlimited company": LegalForm.LIMITED_COMPANY,
    "private unlimited": LegalForm.LIMITED_COMPANY,
    "public limited company": LegalForm.PLC,
    "old public company": LegalForm.PLC,
    "limited liability partnership": LegalForm.LLP,
    "scottish partnership": LegalForm.SCOTTISH_PARTNERSHIP,
    "limited partnership": LegalForm.PARTNERSHIP,
}

#: Only these statuses are worth contacting. A dissolved company has no one to
#: write to and its address is stale.
ACTIVE_STATUSES = frozenset({"active", "active - proposal to strike off"})


class CompaniesHouseSource(OrganisationSource):
    id = "gb-companies-house"
    country = "GB"
    licence = "Open Government Licence v3.0"
    evidences_legal_form = True
    notes = (
        "Incorporated estate agencies with legal form stated by the register. "
        "Contains no sole traders by construction. No email addresses."
    )

    def load(
        self,
        path: str | Path,
        *,
        sic_codes: tuple[str, ...] = DEFAULT_SIC_CODES,
        active_only: bool = True,
        **_: Any,
    ) -> Iterator[Organisation]:
        for content in read_files(path, (".csv", ".zip")):
            for row in read_csv_rows(content):
                org = self._normalise(row, sic_codes, active_only)
                if org is not None:
                    yield org

    def _normalise(
        self, row: dict[str, str], sic_codes: tuple[str, ...], active_only: bool
    ) -> Organisation | None:
        name = pick(row, "companyname", "company_name")
        number = pick(row, "companynumber", "company_number")
        if not name or not number:
            return None

        if active_only:
            status = (pick(row, "companystatus", "company_status") or "").lower()
            if status not in ACTIVE_STATUSES:
                return None

        sic_text = " ".join(
            pick(row, f"siccode_sictext_{index}") or "" for index in range(1, 5)
        )
        if sic_codes and not any(code in sic_text for code in sic_codes):
            return None

        category = (pick(row, "companycategory", "company_category") or "").lower()
        legal_form = COMPANY_CATEGORIES.get(category, LegalForm.OTHER)

        postcode = pick(row, "regaddress_postcode", "regaddress_post_code")
        town = pick(row, "regaddress_posttown", "regaddress_post_town")

        return Organisation(
            country=self.country,
            name=name,
            legal_form=legal_form,
            company_number=number,
            website=pick(row, "uri"),
            source=self.id,
            notes=self._note(category, legal_form, town, postcode),
        )

    @staticmethod
    def _note(
        category: str, legal_form: LegalForm, town: str | None, postcode: str | None
    ) -> str:
        parts = [f"registered office: {town or '?'} {postcode or ''}".strip()]
        if legal_form is LegalForm.OTHER and category:
            # Surfaced rather than silently swallowed: an unmapped category
            # blocks electronic marketing, so someone should look at it.
            parts.append(f"unmapped CompanyCategory {category!r}")
        return "; ".join(parts)
