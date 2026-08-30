"""Spanish cadastral references, rights, and province lookup.

Spain is the counterweight to Bali. Where Indonesian listings carry no
authoritative key at all, Spanish ones routinely quote a **referencia
catastral** — a 20-character cadastral reference identifying the property in
the Catastro. When a listing includes it, a portal record arrives with
`identity_confidence == "authoritative"`, and two portals advertising the same
flat collide on purpose instead of being guessed at.

The rights vocabulary breaks differently from Indonesia's too. Indonesia's
distinctions are about *who may hold* a right; Spain's headline distinction is
about *what is being sold*:

* **Pleno dominio** is full ownership.
* **Nuda propiedad** is ownership stripped of the right to use it, because
  someone — typically an elderly seller — holds a lifetime usufruct. These
  sell at a deep discount and, to anything that treats them as freehold, look
  like the cheapest properties on the street. The discount is the whole point
  and it is not a bargain.
* **VPO** (vivienda de protección oficial) is not a tenure at all: it is
  ordinary ownership with a statutory price ceiling and buyer eligibility
  rules. It belongs in `transfer_restriction`, not `family`.

Nothing here is legal advice. Autonomous communities vary, VPO regimes differ
by region and vintage, and the Catastro is a fiscal register whose boundaries
are not conclusive as to title — the Registro de la Propiedad governs that.
"""

from __future__ import annotations

import re
from dataclasses import replace

from propdata.schema import Tenure, TenureFamily

#: INE province codes.
PROVINCES: dict[str, str] = {
    "01": "Araba/Álava", "02": "Albacete", "03": "Alicante", "04": "Almería",
    "05": "Ávila", "06": "Badajoz", "07": "Illes Balears", "08": "Barcelona",
    "09": "Burgos", "10": "Cáceres", "11": "Cádiz", "12": "Castellón",
    "13": "Ciudad Real", "14": "Córdoba", "15": "A Coruña", "16": "Cuenca",
    "17": "Girona", "18": "Granada", "19": "Guadalajara", "20": "Gipuzkoa",
    "21": "Huelva", "22": "Huesca", "23": "Jaén", "24": "León", "25": "Lleida",
    "26": "La Rioja", "27": "Lugo", "28": "Madrid", "29": "Málaga",
    "30": "Murcia", "31": "Navarra", "32": "Ourense", "33": "Asturias",
    "34": "Palencia", "35": "Las Palmas", "36": "Pontevedra",
    "37": "Salamanca", "38": "Santa Cruz de Tenerife", "39": "Cantabria",
    "40": "Segovia", "41": "Sevilla", "42": "Soria", "43": "Tarragona",
    "44": "Teruel", "45": "Toledo", "46": "Valencia", "47": "Valladolid",
    "48": "Bizkaia", "49": "Zamora", "50": "Zaragoza", "51": "Ceuta",
    "52": "Melilla",
}

#: Locality -> province code, weighted towards the coastal markets where
#: foreign-facing listings cluster. Province names themselves are matched
#: separately, so this only needs the towns that do not name their province.
LOCALITIES: dict[str, str] = {
    # Málaga / Costa del Sol
    "marbella": "29", "estepona": "29", "mijas": "29", "benalmadena": "29",
    "benalmádena": "29", "fuengirola": "29", "torremolinos": "29",
    "nerja": "29", "ronda": "29", "manilva": "29", "casares": "29",
    "puerto banus": "29", "puerto banús": "29", "san pedro alcantara": "29",
    # Illes Balears
    "ibiza": "07", "eivissa": "07", "mallorca": "07", "palma": "07",
    "menorca": "07", "formentera": "07", "santa eulalia": "07",
    "pollensa": "07", "andratx": "07", "soller": "07", "sóller": "07",
    # Alicante / Costa Blanca
    "javea": "03", "jávea": "03", "xabia": "03", "denia": "03", "dénia": "03",
    "altea": "03", "calpe": "03", "moraira": "03", "benidorm": "03",
    "torrevieja": "03", "orihuela": "03", "alfaz del pi": "03",
    # Cádiz
    "sotogrande": "11", "tarifa": "11", "jerez": "11", "chiclana": "11",
    "conil": "11", "zahara": "11",
    # Girona / Costa Brava
    "cadaques": "17", "cadaqués": "17", "begur": "17", "roses": "17",
    "lloret de mar": "17", "platja d aro": "17",
    # Barcelona
    "sitges": "08", "castelldefels": "08", "badalona": "08",
    # Las Palmas / Santa Cruz
    "las palmas": "35", "maspalomas": "35", "lanzarote": "35",
    "fuerteventura": "35", "tenerife": "38", "adeje": "38",
    "la palma": "38", "la gomera": "38",
    # Murcia
    "la manga": "30", "cartagena": "30", "mazarron": "30", "mazarrón": "30",
}

#: Referencia catastral: 20 alphanumeric characters, sometimes printed in
#: groups. Format only — the two trailing control characters have a checksum
#: algorithm that is NOT verified here, so a transposed reference will pass.
#: Treat a match as "well-formed", not as "exists in the Catastro".
_REFERENCIA_CATASTRAL = re.compile(
    r"\b([0-9A-Z]{7}[\s-]?[0-9A-Z]{7}[\s-]?[0-9A-Z]{4}[\s-]?[0-9A-Z]{2})\b"
)

TENURE_TERMS: dict[str, Tenure] = {
    "pleno dominio": Tenure(
        family=TenureFamily.FREEHOLD, local_name="Pleno dominio"
    ),
    "plena propiedad": Tenure(
        family=TenureFamily.FREEHOLD, local_name="Plena propiedad"
    ),
    "nuda propiedad": Tenure(
        family=TenureFamily.BARE_OWNERSHIP,
        local_name="Nuda propiedad",
        # The seller keeps the right to live there for life. The discount in
        # the asking price is the value of that retained interest, not a
        # market opportunity.
        extendable=None,
    ),
    "usufructo": Tenure(family=TenureFamily.USUFRUCT, local_name="Usufructo"),
    "derecho de superficie": Tenure(
        family=TenureFamily.BUILD_RIGHT,
        local_name="Derecho de superficie",
        extendable=None,
    ),
    "multipropiedad": Tenure(
        family=TenureFamily.TIMESHARE, local_name="Multipropiedad"
    ),
    "aprovechamiento por turno": Tenure(
        family=TenureFamily.TIMESHARE,
        local_name="Aprovechamiento por turno",
    ),
}

#: Protected-housing markers. Not a tenure family — ordinary ownership with a
#: statutory price ceiling and buyer eligibility rules.
_PROTECTED = re.compile(
    r"\b(vpo|vpp|vivienda de protecci[oó]n oficial|protecci[oó]n p[uú]blica)\b",
    re.I,
)

_LIFETIME_INTEREST = re.compile(
    r"\b(nuda propiedad|usufructo vitalicio|con inquilino vitalicio)\b", re.I
)


def find_cadastral_reference(text: str) -> str | None:
    """Extract a well-formed referencia catastral, normalised to 20 chars."""
    if not text:
        return None
    match = _REFERENCIA_CATASTRAL.search(text.upper())
    if match is None:
        return None
    reference = re.sub(r"[\s-]", "", match.group(1))
    return reference if len(reference) == 20 else None


def resolve_locality(text: str) -> tuple[str | None, list[str]]:
    """Map free text to an INE province code and administrative path."""
    if not text:
        return None, []
    lowered = text.lower()

    best: tuple[int, str, str] | None = None
    for name, code in LOCALITIES.items():
        if re.search(rf"\b{re.escape(name)}\b", lowered) and (
            best is None or len(name) > best[0]
        ):
            best = (len(name), name, code)
    if best is not None:
        _, name, code = best
        return code, ["España", PROVINCES[code], name.title()]

    for code, province in PROVINCES.items():
        if re.search(rf"\b{re.escape(province.lower())}\b", lowered):
            return code, ["España", province]
    return None, []


def detect_tenure(text: str) -> tuple[Tenure | None, list[str]]:
    """Read a Spanish tenure off listing text.

    Returns (tenure, warnings). A listing that never states a right is
    assumed to be nothing: absence is not pleno dominio, and inferring full
    ownership from silence is how a nuda propiedad gets mispriced.
    """
    if not text:
        return None, []
    warnings: list[str] = []
    lowered = text.lower()

    matches = [
        (term, template)
        for term, template in TENURE_TERMS.items()
        if re.search(rf"\b{re.escape(term)}\b", lowered)
    ]

    tenure = None
    if matches:
        # Longest term wins: "nuda propiedad" must not lose to a bare
        # "usufructo" mentioned in the same sentence describing it.
        matches.sort(key=lambda kv: len(kv[0]), reverse=True)
        tenure = replace(matches[0][1])

    if tenure is not None and tenure.family == TenureFamily.BARE_OWNERSHIP:
        warnings.append(
            "nuda propiedad: a lifetime usufruct is retained, so the asking "
            "price reflects an occupied property and is not comparable to "
            "full-ownership listings"
        )
    elif tenure is None and _LIFETIME_INTEREST.search(text):
        warnings.append(
            "listing text mentions a lifetime interest but states no right; "
            "tenure left unset rather than assumed"
        )

    protected = _PROTECTED.search(text)
    if protected:
        if tenure is None:
            tenure = Tenure(family=TenureFamily.FREEHOLD)
        tenure.transfer_restriction = (
            f"{protected.group(1).upper()}: statutory price ceiling and buyer "
            "eligibility rules apply"
        )
        warnings.append(
            "protected housing (VPO): resale price is capped and buyers must "
            "qualify; asking price is not a market price"
        )

    return tenure, warnings
