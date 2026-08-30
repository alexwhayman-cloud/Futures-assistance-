"""Indonesian tenure vocabulary and Bali administrative lookup.

Indonesia is where a tenure enum borrowed from English law stops working.
Land rights come from the Basic Agrarian Law (UUPA 5/1960) and are not
translations of freehold/leasehold — they differ in who may hold them, which
is the fact that decides whether a given listing is even purchasable by a
given buyer.

The `foreign_holdable` flags below are the reason this table exists. Listing
copy in Bali routinely advertises "freehold villas" to foreign buyers who
cannot lawfully hold Hak Milik; the term in the certificate governs, not the
adjective in the advert. Anything derived from marketing text rather than a
stated legal term is left as None.

Nothing here is legal advice and the flags are coarse: they describe the
ordinary case for an individual foreign natural person. Structures via a
PT PMA, a nominee arrangement, or an Indonesian spouse change the answer, as
do amendments to the underlying regulations. Verify before relying on it.
"""

from __future__ import annotations

import re
from dataclasses import replace

from propdata.schema import Tenure, TenureFamily

#: Kode Wilayah (Permendagri) for Bali province and its regencies/city.
#: Validate against the current Kepmendagri listing before treating these as
#: authoritative — codes are revised as administrative areas change.
BALI_PROVINCE_CODE = "51"

BALI_REGENCIES: dict[str, str] = {
    "51.01": "Jembrana",
    "51.02": "Tabanan",
    "51.03": "Badung",
    "51.04": "Gianyar",
    "51.05": "Klungkung",
    "51.06": "Bangli",
    "51.07": "Karangasem",
    "51.08": "Buleleng",
    "51.71": "Kota Denpasar",
}

#: Locality -> regency code. Bali listings name a village or a beach, never a
#: regency, and almost never a usable street number. This lookup is the only
#: structured location signal most listings will yield.
#:
#: The entries that matter are the counter-intuitive ones: Sanur is Denpasar
#: rather than Gianyar, Nusa Penida and Lembongan are Klungkung rather than
#: their own regency, and the whole Canggu/Pererenan strip is Badung rather
#: than Tabanan despite sitting on the border.
LOCALITIES: dict[str, str] = {
    # Badung
    "canggu": "51.03", "pererenan": "51.03", "berawa": "51.03",
    "seminyak": "51.03", "kerobokan": "51.03", "umalas": "51.03",
    "petitenget": "51.03", "batu belig": "51.03", "kuta": "51.03",
    "legian": "51.03", "tuban": "51.03", "jimbaran": "51.03",
    "uluwatu": "51.03", "pecatu": "51.03", "ungasan": "51.03",
    "bingin": "51.03", "balangan": "51.03", "nusa dua": "51.03",
    "benoa": "51.03", "munggu": "51.03", "cemagi": "51.03",
    "seseh": "51.03", "mengwi": "51.03", "abiansemal": "51.03",
    # Gianyar
    "ubud": "51.04", "tegallalang": "51.04", "payangan": "51.04",
    "sukawati": "51.04", "mas": "51.04", "keramas": "51.04",
    "sidemen gianyar": "51.04", "gianyar": "51.04", "batuan": "51.04",
    "pejeng": "51.04", "tampaksiring": "51.04", "saba": "51.04",
    # Denpasar
    "denpasar": "51.71", "sanur": "51.71", "renon": "51.71",
    "kesiman": "51.71", "ubung": "51.71",
    # Tabanan
    "tabanan": "51.02", "tanah lot": "51.02", "kedungu": "51.02",
    "nyanyi": "51.02", "beraban": "51.02", "selemadeg": "51.02",
    "soka": "51.02", "jatiluwih": "51.02", "bedugul": "51.02",
    # Buleleng
    "lovina": "51.08", "singaraja": "51.08", "buleleng": "51.08",
    "seririt": "51.08", "pemuteran": "51.08",
    # Karangasem
    "amed": "51.07", "candidasa": "51.07", "karangasem": "51.07",
    "sidemen": "51.07", "manggis": "51.07", "tulamben": "51.07",
    # Klungkung
    "nusa penida": "51.05", "nusa lembongan": "51.05", "lembongan": "51.05",
    "ceningan": "51.05", "klungkung": "51.05", "semarapura": "51.05",
    # Bangli
    "bangli": "51.06", "kintamani": "51.06", "batur": "51.06",
    # Jembrana
    "jembrana": "51.01", "negara": "51.01", "medewi": "51.01",
}

#: Local tenure term -> canonical Tenure template.
#:
#: Keys are matched case-insensitively as whole words against listing text.
#: Values are copied, never shared, so a caller can safely set years_remaining.
TENURE_TERMS: dict[str, Tenure] = {
    "hak milik": Tenure(
        family=TenureFamily.FREEHOLD,
        local_name="Hak Milik",
        local_code="SHM",
        extendable=None,
        foreign_holdable=False,
    ),
    "shm": Tenure(
        family=TenureFamily.FREEHOLD,
        local_name="Hak Milik",
        local_code="SHM",
        foreign_holdable=False,
    ),
    "hak guna bangunan": Tenure(
        family=TenureFamily.BUILD_RIGHT,
        local_name="Hak Guna Bangunan",
        local_code="HGB",
        extendable=True,
        # An individual foreigner cannot hold HGB; an Indonesian legal entity
        # (including a foreign-invested PT PMA) can. Coarse flag, see module
        # docstring.
        foreign_holdable=False,
    ),
    "hgb": Tenure(
        family=TenureFamily.BUILD_RIGHT,
        local_name="Hak Guna Bangunan",
        local_code="HGB",
        extendable=True,
        foreign_holdable=False,
    ),
    "hak pakai": Tenure(
        family=TenureFamily.USE_RIGHT,
        local_name="Hak Pakai",
        local_code="HP",
        extendable=True,
        foreign_holdable=True,
    ),
    "hak sewa": Tenure(
        family=TenureFamily.LEASEHOLD,
        local_name="Hak Sewa",
        local_code="HS",
        extendable=None,
        foreign_holdable=True,
    ),
    "sewa": Tenure(
        family=TenureFamily.LEASEHOLD,
        local_name="Hak Sewa",
        local_code="HS",
        foreign_holdable=True,
    ),
    "hak guna usaha": Tenure(
        family=TenureFamily.CULTIVATION_RIGHT,
        local_name="Hak Guna Usaha",
        local_code="HGU",
        foreign_holdable=False,
    ),
    "hgu": Tenure(
        family=TenureFamily.CULTIVATION_RIGHT,
        local_name="Hak Guna Usaha",
        local_code="HGU",
        foreign_holdable=False,
    ),
    "girik": Tenure(
        family=TenureFamily.CUSTOMARY,
        local_name="Girik",
        foreign_holdable=False,
    ),
    "letter c": Tenure(
        family=TenureFamily.CUSTOMARY,
        local_name="Letter C",
        foreign_holdable=False,
    ),
    "petok d": Tenure(
        family=TenureFamily.CUSTOMARY,
        local_name="Petok D",
        foreign_holdable=False,
    ),
    "tanah adat": Tenure(
        family=TenureFamily.CUSTOMARY,
        local_name="Tanah Adat",
        foreign_holdable=False,
    ),
    "laba pura": Tenure(
        family=TenureFamily.CUSTOMARY,
        local_name="Laba Pura",
        foreign_holdable=False,
    ),
    "shmsrs": Tenure(
        family=TenureFamily.STRATA,
        local_name="Hak Milik atas Satuan Rumah Susun",
        local_code="SHMSRS",
        foreign_holdable=False,
    ),
}

#: English marketing terms. Deliberately mapped WITHOUT foreign_holdable and
#: without a local_name: "freehold" in a Bali advert is a sales adjective, not
#: a certificate type, and treating it as Hak Milik would assert a legal fact
#: the listing never stated.
MARKETING_TERMS: dict[str, Tenure] = {
    "freehold": Tenure(family=TenureFamily.FREEHOLD),
    "leasehold": Tenure(family=TenureFamily.LEASEHOLD),
}

_YEARS_REMAINING = [
    re.compile(r"(\d{1,3})\s*(?:\+\s*\d+\s*)?year[s]?\s*(?:left|remaining|lease)", re.I),
    re.compile(r"lease(?:hold)?\s*(?:for\s*)?(\d{1,3})\s*year", re.I),
    re.compile(r"sewa\s*(\d{1,3})\s*tahun", re.I),
    re.compile(r"(\d{1,3})\s*tahun\s*(?:lagi|tersisa)", re.I),
]
_EXPIRY_YEAR = re.compile(r"(?:until|hingga|sampai|expir\w*)\s*(?:year\s*)?(20\d{2})", re.I)


#: Certificate-backed rights outrank contractual ones when a listing names
#: both. A sewa (lease) sits on top of some underlying certificate; the
#: certificate is what the property *is*.
_CONTRACT_FAMILIES = frozenset({TenureFamily.LEASEHOLD})


def _rank(tenure: Tenure) -> int:
    return 1 if tenure.family in _CONTRACT_FAMILIES else 2


def resolve_locality(text: str) -> tuple[str | None, list[str]]:
    """Map free text to a Bali regency code and administrative path.

    Returns (admin_code, path). Longest locality name wins, so "nusa penida"
    is not shadowed by a stray "nusa dua" match elsewhere in the string.
    """
    if not text:
        return None, []
    lowered = text.lower()
    best: tuple[int, str, str] | None = None
    for name, code in LOCALITIES.items():
        if re.search(rf"\b{re.escape(name)}\b", lowered) and (
            best is None or len(name) > best[0]
        ):
            best = (len(name), name, code)
    if best is None:
        return None, []
    _, name, code = best
    return code, ["Bali", BALI_REGENCIES[code], name.title()]


def detect_tenure(text: str) -> tuple[Tenure | None, list[str]]:
    """Read a tenure off listing text.

    Returns (tenure, warnings). A legal term always beats a marketing word;
    when only a marketing word is present the result is flagged, because
    "freehold" alone does not tell you which certificate exists or whether a
    foreign buyer could hold it.
    """
    if not text:
        return None, []
    lowered = text.lower()
    warnings: list[str] = []

    matches = [
        (term, template)
        for term, template in TENURE_TERMS.items()
        if re.search(rf"\b{re.escape(term)}\b", lowered)
    ]

    # A certificate outranks a contract. "HGB, sewa 22 tahun" describes land
    # held on Hak Guna Bangunan that is being sublet — the underlying right is
    # HGB, and picking the longest matching term would have reported the
    # sublease as the tenure. Both facts matter, so the loser is flagged
    # rather than dropped.
    if matches:
        matches.sort(key=lambda kv: (_rank(kv[1]), len(kv[0])), reverse=True)
        if len(matches) > 1 and _rank(matches[0][1]) > _rank(matches[1][1]):
            others = ", ".join(sorted({term for term, _ in matches[1:]}))
            warnings.append(
                f"listing states more than one tenure term; took "
                f"{matches[0][0]!r} as the underlying right, also saw: {others}"
            )
        found = (len(matches[0][0]), matches[0][1])
    else:
        found = None

    tenure = None
    if found is not None:
        tenure = replace(found[1])
    else:
        for term, template in MARKETING_TERMS.items():
            if re.search(rf"\b{term}\b", lowered):
                tenure = replace(template)
                warnings.append(
                    f"tenure inferred from marketing term {term!r}; no Indonesian "
                    "legal term stated, foreign_holdable left unknown"
                )
                break

    if tenure is None:
        return None, warnings

    for pattern in _YEARS_REMAINING:
        match = pattern.search(text)
        if match:
            tenure.years_remaining = int(match.group(1))
            break
    else:
        match = _EXPIRY_YEAR.search(text)
        if match:
            tenure.expires_on = None
            tenure.years_remaining = None
            warnings.append(f"lease expiry stated as year {match.group(1)}")

    if (
        tenure.family in (TenureFamily.FREEHOLD, TenureFamily.CUSTOMARY)
        and tenure.years_remaining is not None
    ):
        warnings.append(
            "listing states a term for a right that is not time-limited; "
            "tenure description is internally inconsistent"
        )

    return tenure, warnings
