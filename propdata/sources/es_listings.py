"""Spanish property listings — Tier 2 portal adapter.

The counterweight to Bali. Both are portal sources reading the same schema.org
JSON-LD through the same framework, and almost everything else about them
differs:

* **Identity is often authoritative.** Spanish listings routinely quote a
  referencia catastral, which lands in `Address.parcel_id` and makes
  `property_id` a real key rather than a hash of marketing text. Where the
  reference is absent, postcodes are precise enough to give "address"
  confidence — Bali could reach neither.
* **A Tier 1 register exists.** The Catastro publishes parcel and building
  data, and the ATOM/INSPIRE services are downloadable in bulk. So unlike
  Bali, listings here are genuinely an enrichment layer over a register spine,
  and a `es-catastro` register source is the obvious next loader.
* **The tenure hazard is different in kind.** Indonesia's risk is who may
  hold a right. Spain's is what is being sold: nuda propiedad and VPO are
  ordinary-looking listings whose prices mean something other than they
  appear to. See `propdata.regions.spain`.

The area trap here is `superficie construida` versus `superficie útil`.
Built area includes walls and a share of common elements and runs perhaps
10-20% above usable area; portals quote either, sometimes both, and rarely
label which one made it into a structured field. Built area is preferred for
consistency and the substitution is recorded when only usable area was found.
"""

from __future__ import annotations

import re

from propdata.regions.spain import (
    detect_tenure,
    find_cadastral_reference,
    resolve_locality,
)
from propdata.schema import Property, PropertyType, Tier, make_property_id
from propdata.sources.jsonld import JsonLdPortalSource, ListingContext

_USABLE_AREA = re.compile(
    r"(?:superficie\s+)?[uú]til\D{0,12}?(\d[\d.,]*)\s*(m2|m²|metros)\b", re.I
)


class SpainListingsSource(JsonLdPortalSource):
    id = "es-listings"
    country = "ES"
    tier = Tier.PORTAL
    licence = "per-portal terms; not redistributable without review"
    notes = (
        "Spanish listings from saved HTML. Cadastral references give many "
        "records authoritative identity. Reads local files only — does not "
        "crawl."
    )

    default_currency = "EUR"
    default_land_unit = "sqm"
    default_region = None

    property_type_terms = {
        "villa": PropertyType.VILLA,
        "chalet": PropertyType.HOUSE,
        "casa adosada": PropertyType.HOUSE,
        "adosado": PropertyType.HOUSE,
        "casa": PropertyType.HOUSE,
        "finca": PropertyType.HOUSE,
        "cortijo": PropertyType.HOUSE,
        "piso": PropertyType.FLAT,
        "apartamento": PropertyType.FLAT,
        "atico": PropertyType.FLAT,
        "ático": PropertyType.FLAT,
        "estudio": PropertyType.FLAT,
        "duplex": PropertyType.FLAT,
        "apartment": PropertyType.FLAT,
        "solar": PropertyType.LAND,
        "parcela": PropertyType.LAND,
        "terreno": PropertyType.LAND,
        "local comercial": PropertyType.COMMERCIAL,
        "local": PropertyType.COMMERCIAL,
        "nave industrial": PropertyType.COMMERCIAL,
    }

    land_area_patterns = (
        re.compile(
            r"(?:parcela|solar|terreno|plot)\D{0,12}?"
            r"(\d[\d.,]*)\s*(m2|m²|metros|ha|hectarea|hectárea)\b",
            re.I,
        ),
    )
    build_area_patterns = (
        re.compile(
            r"(?:superficie\s+construida|construidos?|built)\D{0,12}?"
            r"(\d[\d.,]*)\s*(m2|m²|metros)\b",
            re.I,
        ),
    )

    def resolve_location(self, text: str) -> tuple[str | None, list[str]]:
        return resolve_locality(text)

    def localise(self, prop: Property, context: ListingContext) -> None:
        reference = find_cadastral_reference(
            context.extra_matching("catastral", "cadastral") or ""
        ) or find_cadastral_reference(context.blob)
        if reference:
            prop.address.parcel_id = reference
            # Identity changed, so the id derived from the old address is
            # stale. Recompute rather than leaving a text hash in place.
            prop.property_id = make_property_id(prop.address)
        else:
            context.warnings.append(
                "no referencia catastral in listing; identity falls back to "
                "postcode and address text"
            )

        tenure, warnings = detect_tenure(context.blob)
        prop.legal_tenure = tenure
        context.warnings.extend(warnings)

        if prop.floor_area_sqm is None:
            match = _USABLE_AREA.search(context.blob)
            if match:
                prop.floor_area_sqm = self.convert_area(
                    match.group(1), match.group(2), context
                )
                context.warnings.append(
                    "floor area is superficie útil, not construida; it runs "
                    "below built area and is not directly comparable"
                )
