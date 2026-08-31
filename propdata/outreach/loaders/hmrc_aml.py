"""HMRC anti-money-laundering supervised businesses — estate agency sector.

Estate agency businesses must register with HMRC for AML supervision, and the
register is published openly. Its value here is precisely the coverage gap
Companies House leaves: **it includes sole traders and unincorporated
partnerships**, because the obligation to register attaches to the business
activity rather than to incorporation.

Those are also, under PECR, individual subscribers who may not be sent
marketing email without consent — so this loader mostly produces contacts the
compliance gate will refuse. That is the correct outcome, and it is more
useful than not knowing they exist: a name that appears here and nowhere in
Companies House is very likely a sole trader, and the system should know that
rather than discover it after sending.

**This loader never infers legal form.** A business called "Smith Estates Ltd"
is probably a limited company, and "probably" is the wrong standard when the
consequence of being wrong in the corporate direction is an unlawful send. Any
suffix found in the name is recorded in `notes` as a hint for a human, and
`legal_form` stays UNKNOWN until `matching.match_to_companies_house` finds an
actual register entry. See `loaders/base.py`.

Column names below are alias lists because the published file's headers have
varied between releases; verify against the copy you actually downloaded.
"""

from __future__ import annotations

import re
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

#: Sector labels indicating estate agency. Matched case-insensitively as a
#: substring, since the published wording varies.
ESTATE_AGENCY_SECTORS = ("estate agen", "letting agen", "property")

#: Status values meaning the business is no longer supervised. Checked
#: before the positive markers, because "deregistered" contains "registered"
#: as a substring and a naive test lets it through.
INACTIVE_STATUS_MARKERS = (
    "deregist", "de-regist", "cancel", "revok", "suspend", "ceased",
    "inactive", "expired",
)
ACTIVE_STATUS_MARKERS = ("active", "registered", "approved")

#: Suffixes that hint at incorporation. Recorded, never acted on.
_INCORPORATION_HINTS = re.compile(
    r"\b(ltd|limited|plc|llp|cyf|cyfyngedig)\b\.?$", re.I
)


class HmrcAmlSource(OrganisationSource):
    id = "gb-hmrc-aml"
    country = "GB"
    licence = "Open Government Licence v3.0"
    #: The whole point: this register does not state legal form.
    evidences_legal_form = False
    notes = (
        "Estate agency businesses supervised for AML, including sole traders "
        "that Companies House cannot contain. Legal form is never inferred, "
        "so entries start UNKNOWN and are blocked from marketing email until "
        "matched against Companies House."
    )

    def load(
        self,
        path: str | Path,
        *,
        sectors: tuple[str, ...] = ESTATE_AGENCY_SECTORS,
        active_only: bool = True,
        **_: Any,
    ) -> Iterator[Organisation]:
        for content in read_files(path, (".csv", ".zip")):
            for row in read_csv_rows(content):
                org = self._normalise(row, sectors, active_only)
                if org is not None:
                    yield org

    def _normalise(
        self, row: dict[str, str], sectors: tuple[str, ...], active_only: bool
    ) -> Organisation | None:
        name = pick(
            row, "business_name", "businessname", "name", "organisation_name",
            "trading_name", "tradingname",
        )
        if not name:
            return None

        if sectors:
            sector = (
                pick(row, "sector", "business_sector", "supervised_sector",
                     "business_type", "regime") or ""
            ).lower()
            # An absent sector column means the file is already sector-scoped,
            # which the published estate-agency extract is.
            if sector and not any(term in sector for term in sectors):
                return None

        if active_only:
            status = (pick(row, "status", "registration_status") or "").lower()
            if status:
                if any(marker in status for marker in INACTIVE_STATUS_MARKERS):
                    return None
                if not any(marker in status for marker in ACTIVE_STATUS_MARKERS):
                    return None

        hint = _INCORPORATION_HINTS.search(name.strip())
        notes = [
            f"town: {pick(row, 'town', 'post_town', 'city') or '?'}",
            "legal form not stated by this register",
        ]
        if hint:
            notes.append(
                f"name suffix {hint.group(1)!r} suggests incorporation — "
                "not acted on; match against Companies House to evidence it"
            )

        return Organisation(
            country=self.country,
            name=name.strip(),
            # Never inferred. See module docstring.
            legal_form=LegalForm.UNKNOWN,
            company_number=None,
            redress_scheme=pick(row, "redress_scheme", "redress"),
            source=self.id,
            notes="; ".join(notes),
        )
