"""Canonical property record.

Every source — bulk register or scraped portal — normalises into `Property`.
The schema is deliberately opinionated about a few things that are easy to get
wrong once and painful to fix later:

* Area is always square metres. There is no `area_unit` field, because a unit
  field is an invitation to store 1,200 sqft as `1200` and sort it next to
  110 sqm. Convert at the edge (see `propdata.units`).
* Land area and building area are separate fields. In much of Asia land is the
  priced asset and the building is an improvement on it; a single "area" field
  makes a 5-are plot with a 200 sqm villa unrepresentable.
* Tenure is a structured value, not an enum member. See `Tenure`.
* Legal tenure and occupancy are separate. "Owner-occupied" is not "freehold",
  and conflating them silently corrupts every country that has both.
* Nothing is required except identity and provenance. A Tier 1 register fills
  in structure; a Tier 2 portal fills in price and presentation. Both produce
  the same type, and records merge on `property_id`.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class Tier(str, Enum):
    """Where a source sits in the sourcing split.

    REGISTER  official bulk data: structure, cleanly licensed, slow-moving.
    PORTAL    listing sites: asking price, photos, agent copy, condition.
    """

    REGISTER = "register"
    PORTAL = "portal"


class PropertyType(str, Enum):
    HOUSE = "house"
    VILLA = "villa"
    FLAT = "flat"
    MAISONETTE = "maisonette"
    BUNGALOW = "bungalow"
    PARK_HOME = "park_home"
    LAND = "land"
    COMMERCIAL = "commercial"
    OTHER = "other"
    UNKNOWN = "unknown"


class BuiltForm(str, Enum):
    DETACHED = "detached"
    SEMI_DETACHED = "semi_detached"
    MID_TERRACE = "mid_terrace"
    END_TERRACE = "end_terrace"
    UNKNOWN = "unknown"


class TenureFamily(str, Enum):
    """Cross-country *family* of a property right.

    This is a classification, not a translation. Indonesian Hak Pakai is not
    "leasehold" and Hak Guna Bangunan is not "freehold"; forcing either into
    an Anglo category destroys the distinction that actually governs who may
    hold the property and for how long. The family supports coarse filtering
    ("show me things I can own outright"); `Tenure.local_name` keeps the term
    that legally matters.
    """

    FREEHOLD = "freehold"           # UK freehold, ID Hak Milik
    LEASEHOLD = "leasehold"         # UK leasehold, ID Hak Sewa
    BUILD_RIGHT = "build_right"     # ID Hak Guna Bangunan
    USE_RIGHT = "use_right"         # ID Hak Pakai
    CULTIVATION_RIGHT = "cultivation_right"  # ID Hak Guna Usaha
    CUSTOMARY = "customary"         # ID girik / letter C / tanah adat
    STRATA = "strata"               # ID SHMSRS, AU strata, condominium title
    COMMONHOLD = "commonhold"
    SHARED_OWNERSHIP = "shared_ownership"
    UNKNOWN = "unknown"


class Occupancy(str, Enum):
    """Who lives there and on what basis. Orthogonal to tenure."""

    OWNER_OCCUPIED = "owner_occupied"
    RENTED_PRIVATE = "rented_private"
    RENTED_SOCIAL = "rented_social"
    VACANT = "vacant"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class Tenure:
    """How the interest in a property is held.

    A flat enum was enough for the UK and broke immediately on Indonesia. Two
    properties can both be "leasehold-ish" and be completely different assets:
    a 25-year Hak Sewa with 6 years left is not a fresh 30-year Hak Guna
    Bangunan with two statutory extensions available.

    `local_name` is the verbatim local term and is the field a human should
    read. `family` is for filtering. `years_remaining` is what actually prices
    a time-limited right, and is why it lives here rather than being derived.

    `foreign_holdable` records whether a non-citizen may hold this right at
    all. In Indonesia that is the single most consequential fact about a
    listing, and it is routinely misstated in listing copy — "freehold villa"
    advertised to foreigners who cannot legally hold Hak Milik. None means
    unknown, never assume True.
    """

    family: TenureFamily = TenureFamily.UNKNOWN
    local_name: str | None = None      # "Hak Guna Bangunan"
    local_code: str | None = None      # "HGB"
    years_remaining: int | None = None
    expires_on: date | None = None
    extendable: bool | None = None
    foreign_holdable: bool | None = None


@dataclass(slots=True)
class Address:
    """Postal address plus whatever authoritative keys the source carried.

    `uprn` (GB), `bag_id` (NL), `parcel_id` (generic cadastral reference) are
    the join keys that make cross-source merging tractable. Where a source
    gives one, dedup is basically free; where it doesn't, you are down to
    fuzzy matching.

    `admin_code` and `admin_path` carry the official administrative hierarchy
    where one exists — Indonesia's Kode Wilayah, for instance. In places with
    no reliable street numbering this is the only structured location signal
    on the record, so it is a first-class field rather than free text.
    """

    country: str  # ISO 3166-1 alpha-2
    lines: list[str] = field(default_factory=list)
    postcode: str | None = None
    locality: str | None = None
    region: str | None = None
    admin_code: str | None = None
    admin_path: list[str] = field(default_factory=list)
    uprn: str | None = None
    bag_id: str | None = None
    parcel_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    @property
    def normalised_line(self) -> str:
        """Lowercased, punctuation-stripped, whitespace-collapsed address.

        Good enough to be a blocking key for dedup; not good enough to be a
        primary key on its own. Real address matching wants a proper
        libpostal-style parser, which is a dependency this scaffold doesn't
        take yet.
        """
        joined = " ".join(part for part in self.lines if part)
        joined = re.sub(r"[^\w\s]", " ", joined.lower())
        return re.sub(r"\s+", " ", joined).strip()

    @property
    def identity_confidence(self) -> str:
        """How much weight `property_id` can bear for this address.

        "authoritative"  a cadastral/registry key is present; collisions are
                         intentional and merging is safe.
        "address"        postcode plus a real address line; usually right,
                         defeated by formatting differences.
        "weak"           neither. Common for Indonesian listings, which give
                         a village and a road name and nothing else. Do not
                         auto-merge on a weak id without a second signal.
        """
        if self.uprn or self.bag_id or self.parcel_id:
            return "authoritative"
        if self.postcode and self.normalised_line:
            return "address"
        return "weak"


@dataclass(slots=True)
class Provenance:
    """Where a field came from, and whether you are allowed to use it.

    `licence` is not decoration. It is what lets you answer "can this row be
    served to a customer, or is it internal-only?" without re-deriving the
    answer per source months later.
    """

    source_id: str
    source_record_id: str
    retrieved_at: datetime
    licence: str
    tier: Tier
    source_url: str | None = None


@dataclass(slots=True)
class EnergyRating:
    scheme: str  # "EPC-EnglandWales", "DPE-FR", ...
    current_band: str | None = None
    potential_band: str | None = None
    current_score: int | None = None
    assessed_on: date | None = None


@dataclass(slots=True)
class Property:
    """One property, as known from one source.

    Records from different sources describing the same property share a
    `property_id` and are merged downstream — merging is not this class's job.
    """

    property_id: str
    address: Address
    provenance: Provenance

    property_type: PropertyType = PropertyType.UNKNOWN
    built_form: BuiltForm = BuiltForm.UNKNOWN
    legal_tenure: Tenure | None = None
    occupancy: Occupancy = Occupancy.UNKNOWN

    floor_area_sqm: float | None = None
    land_area_sqm: float | None = None
    habitable_rooms: int | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    construction_age_band: str | None = None
    energy: EnergyRating | None = None

    # Tier 2 territory. Left empty by registers.
    asking_price: int | None = None
    price_currency: str | None = None
    listed_on: date | None = None
    description: str | None = None
    image_urls: list[str] = field(default_factory=list)

    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_property_id(address: Address) -> str:
    """Deterministic identity for a property.

    Prefers an authoritative key so that two sources citing the same UPRN
    collide on purpose. Falls back to a hash of country + administrative code
    + postcode + normalised address line.

    The fallback is weaker than it looks, and weakest exactly where there is
    no cadastral key to fall back from — see `Address.identity_confidence`.
    """
    if address.uprn:
        return f"uprn:{address.country}:{address.uprn}"
    if address.bag_id:
        return f"bag:{address.country}:{address.bag_id}"
    if address.parcel_id:
        return f"parcel:{address.country}:{address.parcel_id}"

    basis = "|".join(
        [
            address.country.upper(),
            (address.admin_code or ""),
            (address.postcode or "").replace(" ", "").upper(),
            address.normalised_line,
        ]
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]
    return f"addr:{address.country}:{digest}"
