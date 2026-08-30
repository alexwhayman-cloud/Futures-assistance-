"""Bali property listings — Tier 2 portal adapter.

**There is no Tier 1 register for this market.** Indonesia's land agency
(ATR/BPN) maintains the cadastre and exposes parcel lookups through Bhumi and
Sentuh Tanahku, but there is no open bulk download of parcels or property
attributes comparable to the UK EPC register, Denmark's BBR or the Dutch BAG.
So Bali inverts the sourcing order the rest of this project relies on: the
listing portals are not an enrichment layer on top of a register spine, they
are the only source, and every weakness of scraped data lands unmitigated.

Consequences worth being explicit about, because they are properties of the
market rather than of this code:

* **Identity is weak.** No UPRN equivalent, no reliable street numbering, and
  postcodes that cover whole districts. Records come out at
  `identity_confidence == "weak"` and must not be auto-merged on id alone.
* **Duplication is extreme.** Open-listing agency practice means one villa
  appears across many portals under different titles, photos and prices.
* **Tenure is frequently misstated.** See `propdata.regions.indonesia`.
* **Land area is the priced quantity**, quoted in are, and is a different
  field from building area. A villa is "5 are, 200 sqm build".

Everything generic — fetching saved HTML, JSON-LD extraction, the schema.org
field mapping, price and area plumbing — lives in `sources.jsonld`. What is
left here is what is actually Indonesian.
"""

from __future__ import annotations

import re

from propdata.regions.indonesia import detect_tenure, resolve_locality
from propdata.schema import Property, PropertyType, Tier
from propdata.sources.jsonld import JsonLdPortalSource, ListingContext


class BaliListingsSource(JsonLdPortalSource):
    id = "id-bali-listings"
    country = "ID"
    tier = Tier.PORTAL
    licence = "per-portal terms; not redistributable without review"
    notes = (
        "Bali listings from saved HTML. No Tier 1 register exists for "
        "Indonesia, so identity is weak and duplication is heavy. Reads "
        "local files only — does not crawl."
    )

    default_currency = None
    #: Bali listings quote land in are, never in square metres.
    default_land_unit = "are"
    default_region = "Bali"

    property_type_terms = {
        "villa": PropertyType.VILLA,
        "house": PropertyType.HOUSE,
        "rumah": PropertyType.HOUSE,
        "apartment": PropertyType.FLAT,
        "apartemen": PropertyType.FLAT,
        "condo": PropertyType.FLAT,
        "land": PropertyType.LAND,
        "tanah": PropertyType.LAND,
        "plot": PropertyType.LAND,
        "commercial": PropertyType.COMMERCIAL,
        "shop": PropertyType.COMMERCIAL,
        "hotel": PropertyType.COMMERCIAL,
    }

    land_area_patterns = (
        re.compile(
            r"(?:land(?:\s*(?:size|area))?|luas\s*tanah|tanah)\D{0,12}?"
            r"(\d[\d.,]*)\s*(are|m2|sqm|m²|ha|hektar|hectare)\b",
            re.I,
        ),
    )
    build_area_patterns = (
        re.compile(
            r"(?:building|built[\s-]*up|luas\s*bangunan|bangunan)\D{0,12}?"
            r"(\d[\d.,]*)\s*(are|m2|sqm|m²)\b",
            re.I,
        ),
    )

    def resolve_location(self, text: str) -> tuple[str | None, list[str]]:
        return resolve_locality(text)

    def localise(self, prop: Property, context: ListingContext) -> None:
        tenure, warnings = detect_tenure(context.blob)
        prop.legal_tenure = tenure
        context.warnings.extend(warnings)
