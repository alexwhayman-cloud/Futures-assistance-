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

This adapter reads saved HTML from disk and does not crawl. Fetching is left
out deliberately: a live crawler needs per-portal terms review, robots
handling, rate limiting and an identifiable user agent, and those are
decisions to make per portal rather than defaults to inherit from a scaffold.

Parsing is generic rather than portal-specific: schema.org JSON-LD first, then
an embedded JSON payload, and only then bespoke extraction. Most property
portals emit `RealEstateListing` or `Product` JSON-LD for search engines, so
the generic path covers a lot of sites without encoding any one site's markup.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from propdata import money, units
from propdata.regions.indonesia import detect_tenure, resolve_locality
from propdata.schema import (
    Address,
    Property,
    PropertyType,
    Tier,
    make_property_id,
)
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

PROPERTY_TYPES = {
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

#: UN/CEFACT codes as they appear in schema.org floorSize, plus the free-text
#: spellings portals actually use.
UNIT_CODES = {
    "mtk": "sqm", "m2": "sqm", "sqm": "sqm", "sq m": "sqm",
    "square meter": "sqm", "square metre": "sqm", "meter persegi": "sqm",
    "ftk": "sqft", "sqft": "sqft", "sq ft": "sqft", "square foot": "sqft",
    "are": "are", "a": "are", "ha": "hectare", "hectare": "hectare",
    "hektar": "hectare", "tumbak": "tumbak", "ubin": "ubin",
}

_LAND_AREA = re.compile(
    r"(?:land(?:\s*(?:size|area))?|luas\s*tanah|tanah)\D{0,12}?"
    r"(\d[\d.,]*)\s*(are|m2|sqm|m²|ha|hektar|hectare)\b",
    re.I,
)
_BUILD_AREA = re.compile(
    r"(?:building|built[\s-]*up|luas\s*bangunan|bangunan)\D{0,12}?"
    r"(\d[\d.,]*)\s*(are|m2|sqm|m²)\b",
    re.I,
)


class _JsonLdExtractor(HTMLParser):
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
        script_type = attributes.get("type", "").lower()
        if "ld+json" in script_type:
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


def _walk(node: Any) -> Iterator[dict[str, Any]]:
    """Yield every dict in a decoded JSON tree, including @graph members."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _types_of(node: dict[str, Any]) -> set[str]:
    raw = node.get("@type") or node.get("type") or []
    if isinstance(raw, str):
        raw = [raw]
    return {str(t).lower() for t in raw}


def _text_of(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        for key in ("name", "value", "@value", "text"):
            if key in value:
                return _text_of(value[key])
    if isinstance(value, list) and value:
        return _text_of(value[0])
    return None


class BaliListingsSource(Source):
    id = "id-bali-listings"
    country = "ID"
    tier = Tier.PORTAL
    licence = "per-portal terms; not redistributable without review"
    notes = (
        "Bali listings from saved HTML. No Tier 1 register exists for "
        "Indonesia, so identity is weak and duplication is heavy. Reads "
        "local files only — does not crawl."
    )

    def fetch(
        self, *, path: str | Path | None = None, **_: Any
    ) -> Iterator[RawDocument]:
        """Read saved listing pages from disk.

        Deliberately not a crawler — see the module docstring.
        """
        if path is None:
            raise ValueError(
                "id-bali-listings fetch requires path= to saved HTML; "
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
        extractor = _JsonLdExtractor()
        extractor.feed(html)

        seen: set[str] = set()
        for index, block in enumerate(extractor.blocks + extractor.state_blocks):
            try:
                decoded = json.loads(block)
            except json.JSONDecodeError:
                # A malformed block on one page must not lose the others.
                continue
            for node in _walk(decoded):
                if not (_types_of(node) & LISTING_TYPES):
                    continue
                if "name" not in node and "offers" not in node:
                    continue  # a bare Offer nested in a listing we already took
                record_id = (
                    _text_of(node.get("url"))
                    or _text_of(node.get("sku"))
                    or _text_of(node.get("@id"))
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
                    url=_text_of(node.get("url")) or document.url,
                )

    def normalise(self, record: RawRecord) -> Property | None:
        node = record.payload
        warnings: list[str] = []

        name = _text_of(node.get("name"))
        description = _text_of(node.get("description"))
        if not name and not description:
            return None

        extras = self._additional_properties(node)
        blob = " ".join(
            part for part in (name, description, *extras.values()) if part
        )

        address = self._address(node, blob)
        tenure, tenure_warnings = detect_tenure(blob)
        warnings.extend(tenure_warnings)

        floor_area, land_area, area_warnings = self._areas(node, extras, blob)
        warnings.extend(area_warnings)

        price, price_warnings = self._price(node, extras, blob)
        warnings.extend(price_warnings)

        if address.identity_confidence == "weak":
            warnings.append(
                "no cadastral key or postcode; property_id is a text hash and "
                "must not be auto-merged without a second signal"
            )

        raw = dict(node)
        raw["_normalisation_warnings"] = warnings

        return Property(
            property_id=make_property_id(address),
            address=address,
            provenance=self.provenance_for(record),
            property_type=self._property_type(node, blob),
            legal_tenure=tenure,
            floor_area_sqm=floor_area,
            land_area_sqm=land_area,
            bedrooms=units.to_int(node.get("numberOfBedrooms")),
            bathrooms=units.to_int(
                node.get("numberOfBathroomsTotal") or node.get("numberOfBathrooms")
            ),
            asking_price=price.amount if price else None,
            price_currency=price.currency if price else None,
            description=description,
            image_urls=self._images(node),
            raw=raw,
        )

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _additional_properties(node: dict[str, Any]) -> dict[str, str]:
        """Flatten schema.org additionalProperty into a name -> value map.

        Portals stash the interesting fields here: "Land Size", "Tenure",
        "Lease Until". Names are lowercased; values kept verbatim.
        """
        result: dict[str, str] = {}
        entries = node.get("additionalProperty") or []
        if isinstance(entries, dict):
            entries = [entries]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            key = _text_of(entry.get("name"))
            value = _text_of(entry.get("value"))
            if key and value:
                result[key.strip().lower()] = value
        return result

    def _address(self, node: dict[str, Any], blob: str) -> Address:
        raw_address = node.get("address")
        if isinstance(raw_address, list) and raw_address:
            raw_address = raw_address[0]
        if not isinstance(raw_address, dict):
            raw_address = {}

        locality = _text_of(raw_address.get("addressLocality"))
        region = _text_of(raw_address.get("addressRegion"))
        street = _text_of(raw_address.get("streetAddress"))

        # Locality first, then the whole page: a listing that never fills in
        # addressLocality will still say "Canggu" in its title.
        admin_code, admin_path = resolve_locality(
            " ".join(p for p in (locality, region, street) if p)
        )
        if admin_code is None:
            admin_code, admin_path = resolve_locality(blob)

        geo = node.get("geo")
        if isinstance(geo, list) and geo:
            geo = geo[0]
        latitude = longitude = None
        if isinstance(geo, dict):
            latitude = units.to_float(geo.get("latitude"))
            longitude = units.to_float(geo.get("longitude"))

        return Address(
            country=self.country,
            lines=[line for line in (street,) if line],
            postcode=_text_of(raw_address.get("postalCode")),
            locality=locality or (admin_path[-1] if admin_path else None),
            region=region or "Bali",
            admin_code=admin_code,
            admin_path=admin_path,
            latitude=latitude,
            longitude=longitude,
        )

    @staticmethod
    def _areas(
        node: dict[str, Any], extras: dict[str, str], blob: str
    ) -> tuple[float | None, float | None, list[str]]:
        """Resolve building and land area, in square metres.

        schema.org `floorSize` is building area. Land area has no standard
        field, so it comes from additionalProperty or the listing text, where
        it is almost always quoted in are.
        """
        warnings: list[str] = []

        def convert(value: Any, unit_text: str | None) -> float | None:
            key = (unit_text or "sqm").strip().lower()
            unit = UNIT_CODES.get(key)
            if unit is None:
                warnings.append(f"unrecognised area unit {unit_text!r}; area dropped")
                return None
            try:
                return units.normalise_area(value, unit)
            except ValueError as exc:
                warnings.append(str(exc))
                return None

        floor_area = None
        floor_size = node.get("floorSize")
        if isinstance(floor_size, dict):
            floor_area = convert(
                floor_size.get("value"),
                _text_of(floor_size.get("unitText")) or _text_of(floor_size.get("unitCode")),
            )
        elif floor_size is not None:
            floor_area = convert(_text_of(floor_size), "sqm")

        land_area = None
        for key, value in extras.items():
            if "land" in key or "tanah" in key:
                match = re.search(r"(\d[\d.,]*)\s*([a-z²]+)?", value, re.I)
                if match:
                    land_area = convert(match.group(1), match.group(2) or "are")
                break

        if land_area is None:
            match = _LAND_AREA.search(blob)
            if match:
                land_area = convert(match.group(1), match.group(2).replace("²", "2"))

        if floor_area is None:
            match = _BUILD_AREA.search(blob)
            if match:
                floor_area = convert(match.group(1), match.group(2).replace("²", "2"))

        if (
            floor_area is not None
            and land_area is not None
            and floor_area > land_area * 3
        ):
            warnings.append(
                f"building area {floor_area} sqm implausible against land area "
                f"{land_area} sqm; are/sqm confusion is the usual cause"
            )

        return floor_area, land_area, warnings

    @staticmethod
    def _price(
        node: dict[str, Any], extras: dict[str, str], blob: str
    ) -> tuple[money.Money | None, list[str]]:
        """Resolve an outright asking price.

        Rental rates are rejected rather than stored: Bali leasehold is often
        advertised per year, and an annual figure in `asking_price` makes a
        villa look an order of magnitude cheaper than it is.
        """
        warnings: list[str] = []

        offers = node.get("offers")
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict):
            currency = _text_of(offers.get("priceCurrency"))
            price_text = _text_of(offers.get("price"))
            if price_text:
                parsed = money.parse_money(
                    f"{currency or ''} {price_text}", default_currency=currency
                )
                if parsed and parsed.period is None:
                    return parsed, warnings
                if parsed:
                    warnings.append(
                        f"offer price is a rate per {parsed.period}; not stored "
                        "as an asking price"
                    )
                    return None, warnings

        for key, value in extras.items():
            if "price" in key or "harga" in key:
                parsed = money.parse_money(value, default_currency="IDR")
                if parsed and parsed.period is None:
                    return parsed, warnings
                if parsed:
                    warnings.append(
                        f"price field {key!r} is a rate per {parsed.period}; "
                        "not stored as an asking price"
                    )
                return None, warnings

        parsed = money.parse_money(blob, default_currency=None)
        if parsed and parsed.period is None:
            warnings.append("price recovered from listing text, not a price field")
            return parsed, warnings
        return None, warnings

    @staticmethod
    def _property_type(node: dict[str, Any], blob: str) -> PropertyType:
        candidates = [
            _text_of(node.get("additionalType")),
            _text_of(node.get("category")),
            _text_of(node.get("name")),
            blob,
        ]
        for candidate in candidates:
            if not candidate:
                continue
            lowered = candidate.lower()
            for term, mapped in PROPERTY_TYPES.items():
                if re.search(rf"\b{term}\b", lowered):
                    return mapped
        return PropertyType.UNKNOWN

    @staticmethod
    def _images(node: dict[str, Any]) -> list[str]:
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
            url = _text_of(item.get("url")) if isinstance(item, dict) else _text_of(item)
            if url:
                urls.append(url)
        return urls
