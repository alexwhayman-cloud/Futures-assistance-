"""Generic JSON-LD portal adapter.

This is the shared machinery behind portal sources, extracted from the Bali
adapter once a second portal market showed which parts were actually generic.
It was not designed up front on purpose: guessing the abstraction before
having two implementations produces a framework shaped like whichever site
was written first.

What turned out to be common across markets:

* finding structured data in a page (ld+json, then embedded state)
* walking a decoded tree for listing-shaped nodes, `@graph` included
* flattening `additionalProperty` into a name -> value map
* the schema.org field mapping: name, description, offers, floorSize, geo,
  bedrooms, images
* the failure modes — an unusable area unit, a rental rate posing as a sale
  price, an area ratio that implies a unit mix-up

What turned out to be country-specific, and therefore hooks:

* which words denote a property type, and in which language
* how a location string resolves to an administrative area
* what a tenure or title reference looks like, and what it implies
* the default currency and the unit a bare land figure is quoted in

Subclasses set the class attributes, implement `localise`, and get
fetch/parse/normalise for free.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from propdata import money, units
from propdata.schema import Address, Property, PropertyType, make_property_id
from propdata.sources.base import RawDocument, RawRecord, Source

LISTING_TYPES = {
    "realestatelisting",
    "residence",
    "house",
    "singlefamilyresidence",
    "apartment",
    "accommodation",
    "product",
    "offer",
}

#: UN/CEFACT codes as they appear in schema.org floorSize, plus the free-text
#: spellings portals actually use, across the markets seen so far.
UNIT_CODES = {
    "mtk": "sqm", "m2": "sqm", "m²": "sqm", "sqm": "sqm", "sq m": "sqm",
    "square meter": "sqm", "square metre": "sqm", "meter persegi": "sqm",
    "metros cuadrados": "sqm", "metros": "sqm",
    "ftk": "sqft", "sqft": "sqft", "sq ft": "sqft", "square foot": "sqft",
    "are": "are", "a": "are",
    "ha": "hectare", "hectare": "hectare", "hektar": "hectare",
    "hectarea": "hectare", "hectárea": "hectare",
    "tumbak": "tumbak", "ubin": "ubin",
}


class _StructuredDataExtractor(HTMLParser):
    """Pull ld+json and embedded-state script bodies out of a page.

    stdlib parser rather than a dependency: this only needs script contents,
    not a DOM.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.state_blocks: list[str] = []
        self._capture: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "script":
            return
        attributes = {k.lower(): (v or "") for k, v in attrs}
        if "ld+json" in attributes.get("type", "").lower():
            self._capture = "ld"
        elif attributes.get("id", "") in {"__NEXT_DATA__", "__NUXT_DATA__"}:
            self._capture = "state"

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture == "ld":
            self.blocks.append(data)
        elif self._capture == "state":
            self.state_blocks.append(data)


def walk(node: Any) -> Iterator[dict[str, Any]]:
    """Yield every dict in a decoded JSON tree, including @graph members."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def types_of(node: dict[str, Any]) -> set[str]:
    raw = node.get("@type") or node.get("type") or []
    if isinstance(raw, str):
        raw = [raw]
    return {str(t).lower() for t in raw}


def text_of(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        for key in ("name", "value", "@value", "text"):
            if key in value:
                return text_of(value[key])
    if isinstance(value, list) and value:
        return text_of(value[0])
    return None


@dataclass
class ListingContext:
    """Everything a `localise` hook needs about one listing."""

    node: dict[str, Any]
    #: additionalProperty flattened to lowercase name -> verbatim value.
    extras: dict[str, str]
    #: name + description + extras, for text matching.
    blob: str
    warnings: list[str] = field(default_factory=list)

    def extra_matching(self, *needles: str) -> str | None:
        """First additionalProperty value whose key contains any needle."""
        for key, value in self.extras.items():
            if any(needle in key for needle in needles):
                return value
        return None


class JsonLdPortalSource(Source):
    """Portal source that reads schema.org JSON-LD from saved HTML.

    Fetching is local-file only by design. A live crawler needs per-portal
    terms review, robots handling, rate limiting and an identifiable user
    agent; those are decisions to make per portal, not defaults to inherit
    from a base class.
    """

    #: Currency assumed when listing text carries no symbol. None means
    #: "refuse to guess" — a price with no currency is dropped.
    default_currency: str | None = None
    #: Unit a bare land-area figure is quoted in for this market.
    default_land_unit: str = "sqm"
    #: Local words denoting a property type, longest-match wins.
    property_type_terms: dict[str, PropertyType] = {}
    #: Patterns with one numeric group and one unit group.
    land_area_patterns: tuple[re.Pattern[str], ...] = ()
    build_area_patterns: tuple[re.Pattern[str], ...] = ()
    #: Default `Address.region` when the listing does not state one.
    default_region: str | None = None
    #: Ratio above which building area implies a unit mix-up against land.
    implausible_area_ratio: float = 3.0

    # -- stages ----------------------------------------------------------

    def fetch(
        self, *, path: str | Path | None = None, **_: Any
    ) -> Iterator[RawDocument]:
        if path is None:
            raise ValueError(
                f"{self.id} fetch requires path= to saved HTML; "
                "this adapter does not crawl"
            )
        target = Path(path).expanduser().resolve()
        if not target.exists():
            raise FileNotFoundError(target)

        files = (
            sorted(f for f in target.rglob("*.htm*") if f.is_file())
            if target.is_dir()
            else [target]
        )
        if not files:
            raise FileNotFoundError(f"no .html files under {target}")
        for html_path in files:
            yield RawDocument(
                source_id=self.id,
                content=html_path.read_bytes(),
                url=html_path.as_uri(),
            )

    def parse(self, document: RawDocument) -> Iterator[RawRecord]:
        html = document.content.decode("utf-8", errors="replace")
        extractor = _StructuredDataExtractor()
        extractor.feed(html)

        seen: set[str] = set()
        for index, block in enumerate(extractor.blocks + extractor.state_blocks):
            try:
                decoded = json.loads(block)
            except json.JSONDecodeError:
                # A malformed block on one page must not lose the others.
                continue
            for node in walk(decoded):
                if not (types_of(node) & LISTING_TYPES):
                    continue
                if "name" not in node and "offers" not in node:
                    continue  # a bare Offer nested in a listing already taken
                record_id = (
                    text_of(node.get("url"))
                    or text_of(node.get("sku"))
                    or text_of(node.get("@id"))
                    or f"{document.url}#{index}"
                )
                if record_id in seen:
                    continue
                seen.add(record_id)
                yield RawRecord(
                    source_id=self.id,
                    record_id=record_id,
                    payload=node,
                    retrieved_at=document.retrieved_at,
                    url=text_of(node.get("url")) or document.url,
                )

    def normalise(self, record: RawRecord) -> Property | None:
        node = record.payload
        name = text_of(node.get("name"))
        description = text_of(node.get("description"))
        if not name and not description:
            return None

        extras = self.additional_properties(node)
        context = ListingContext(
            node=node,
            extras=extras,
            blob=" ".join(p for p in (name, description, *extras.values()) if p),
        )

        address = self.build_address(context)
        floor_area, land_area = self.build_areas(context)
        price = self.build_price(context)

        prop = Property(
            property_id=make_property_id(address),
            address=address,
            provenance=self.provenance_for(record),
            property_type=self.build_property_type(context),
            floor_area_sqm=floor_area,
            land_area_sqm=land_area,
            bedrooms=units.to_int(node.get("numberOfBedrooms")),
            bathrooms=units.to_int(
                node.get("numberOfBathroomsTotal") or node.get("numberOfBathrooms")
            ),
            asking_price=price.amount if price else None,
            price_currency=price.currency if price else None,
            description=description,
            image_urls=self.build_images(node),
        )

        self.localise(prop, context)

        verdict = prop.address.assess_identity(prop.property_type.value)
        prop.identity = verdict
        if verdict.confidence != "authoritative":
            context.warnings.append(
                f"identity {verdict.confidence} (country tier "
                f"{verdict.tier.value}): {verdict.reason}; do not auto-merge "
                "without a second signal"
            )

        prop.raw = dict(node)
        prop.raw["_normalisation_warnings"] = context.warnings
        return prop

    # -- hooks -----------------------------------------------------------

    def resolve_location(self, text: str) -> tuple[str | None, list[str]]:
        """Map free text to an administrative code and path. Default: none."""
        return None, []

    def localise(self, prop: Property, context: ListingContext) -> None:
        """Apply country-specific enrichment in place.

        Tenure, title references, and anything else that depends on a legal
        system. Append to `context.warnings` rather than raising: one odd
        listing should not lose the rest of the page.
        """

    # -- shared field mapping --------------------------------------------

    @staticmethod
    def additional_properties(node: dict[str, Any]) -> dict[str, str]:
        """Flatten schema.org additionalProperty into a name -> value map.

        Portals stash the interesting fields here: land size, tenure, title
        reference. Names are lowercased; values kept verbatim.
        """
        result: dict[str, str] = {}
        entries = node.get("additionalProperty") or []
        if isinstance(entries, dict):
            entries = [entries]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            key = text_of(entry.get("name"))
            value = text_of(entry.get("value"))
            if key and value:
                result[key.strip().lower()] = value
        return result

    def build_address(self, context: ListingContext) -> Address:
        raw_address = context.node.get("address")
        if isinstance(raw_address, list) and raw_address:
            raw_address = raw_address[0]
        if not isinstance(raw_address, dict):
            raw_address = {}

        locality = text_of(raw_address.get("addressLocality"))
        region = text_of(raw_address.get("addressRegion"))
        street = text_of(raw_address.get("streetAddress"))

        # Structured fields first, then the whole page: a listing that never
        # fills in addressLocality will still name the place in its title.
        admin_code, admin_path = self.resolve_location(
            " ".join(p for p in (locality, region, street) if p)
        )
        if admin_code is None:
            admin_code, admin_path = self.resolve_location(context.blob)

        geo = context.node.get("geo")
        if isinstance(geo, list) and geo:
            geo = geo[0]
        latitude = longitude = None
        if isinstance(geo, dict):
            latitude = units.to_float(geo.get("latitude"))
            longitude = units.to_float(geo.get("longitude"))

        return Address(
            country=self.country,
            lines=[line for line in (street,) if line],
            postcode=text_of(raw_address.get("postalCode")),
            locality=locality or (admin_path[-1] if admin_path else None),
            region=region or self.default_region,
            admin_code=admin_code,
            admin_path=admin_path,
            latitude=latitude,
            longitude=longitude,
        )

    def convert_area(
        self, value: Any, unit_text: str | None, context: ListingContext, *,
        default: str = "sqm",
    ) -> float | None:
        key = (unit_text or default).strip().lower()
        unit = UNIT_CODES.get(key)
        if unit is None:
            context.warnings.append(
                f"unrecognised area unit {unit_text!r}; area dropped"
            )
            return None
        try:
            return units.normalise_area(value, unit)
        except ValueError as exc:
            context.warnings.append(str(exc))
            return None

    def build_areas(
        self, context: ListingContext
    ) -> tuple[float | None, float | None]:
        """Resolve building and land area, in square metres.

        schema.org `floorSize` is building area. Land area has no standard
        field, so it comes from additionalProperty or the listing text.
        """
        node = context.node

        floor_area = None
        floor_size = node.get("floorSize")
        if isinstance(floor_size, dict):
            floor_area = self.convert_area(
                floor_size.get("value"),
                text_of(floor_size.get("unitText"))
                or text_of(floor_size.get("unitCode")),
                context,
            )
        elif floor_size is not None:
            floor_area = self.convert_area(text_of(floor_size), "sqm", context)

        land_area = None
        land_text = context.extra_matching("land", "tanah", "parcela", "plot")
        if land_text:
            # The unit group must reach the digit in "m2" — [a-z] alone stops at "m"
            # and the area gets dropped as an unknown unit.
            match = re.search(r"(\d[\d.,]*)\s*([a-z²]+\d?)?", land_text, re.I)
            if match:
                land_area = self.convert_area(
                    match.group(1),
                    match.group(2) or self.default_land_unit,
                    context,
                    default=self.default_land_unit,
                )

        if land_area is None:
            land_area = self._from_patterns(self.land_area_patterns, context)
        if floor_area is None:
            floor_area = self._from_patterns(self.build_area_patterns, context)

        if (
            floor_area is not None
            and land_area is not None
            and floor_area > land_area * self.implausible_area_ratio
        ):
            context.warnings.append(
                f"building area {floor_area} sqm implausible against land area "
                f"{land_area} sqm; unit confusion is the usual cause"
            )
        return floor_area, land_area

    def _from_patterns(
        self, patterns: tuple[re.Pattern[str], ...], context: ListingContext
    ) -> float | None:
        for pattern in patterns:
            match = pattern.search(context.blob)
            if match:
                return self.convert_area(
                    match.group(1), match.group(2), context
                )
        return None

    def build_price(self, context: ListingContext) -> money.Money | None:
        """Resolve an outright asking price.

        Rental rates are rejected rather than stored: a per-year or per-month
        figure in `asking_price` makes a property look an order of magnitude
        cheaper than it is.
        """
        node = context.node
        offers = node.get("offers")
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict):
            currency = text_of(offers.get("priceCurrency"))
            price_text = text_of(offers.get("price"))
            if price_text:
                parsed = money.parse_money(
                    f"{currency or ''} {price_text}",
                    default_currency=currency or self.default_currency,
                )
                if parsed and parsed.period is None:
                    return parsed
                if parsed:
                    context.warnings.append(
                        f"offer price is a rate per {parsed.period}; not stored "
                        "as an asking price"
                    )
                    return None

        price_text = context.extra_matching("price", "harga", "precio")
        if price_text:
            parsed = money.parse_money(
                price_text, default_currency=self.default_currency
            )
            if parsed and parsed.period is None:
                return parsed
            if parsed:
                context.warnings.append(
                    f"price field is a rate per {parsed.period}; not stored "
                    "as an asking price"
                )
            return None

        parsed = money.parse_money(context.blob, default_currency=None)
        if parsed and parsed.period is None:
            context.warnings.append(
                "price recovered from listing text, not a price field"
            )
            return parsed
        return None

    def build_property_type(self, context: ListingContext) -> PropertyType:
        node = context.node
        candidates = [
            text_of(node.get("additionalType")),
            text_of(node.get("category")),
            text_of(node.get("name")),
            context.blob,
        ]
        for candidate in candidates:
            if not candidate:
                continue
            lowered = candidate.lower()
            # Longest term first so "casa adosada" beats a bare "casa".
            for term in sorted(self.property_type_terms, key=len, reverse=True):
                if re.search(rf"\b{term}\b", lowered):
                    return self.property_type_terms[term]
        return PropertyType.UNKNOWN

    @staticmethod
    def build_images(node: dict[str, Any]) -> list[str]:
        """Collect image URLs only.

        URLs, never bytes. Listing photographs are separately copyrighted from
        the listing facts, usually by the agency or photographer, so this
        records where an image was without copying it.
        """
        raw = node.get("image") or []
        if isinstance(raw, (str, dict)):
            raw = [raw]
        urls = []
        for item in raw:
            url = text_of(item.get("url")) if isinstance(item, dict) else text_of(item)
            if url:
                urls.append(url)
        return urls
