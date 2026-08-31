"""Per-country property identity schemes.

`Address.identity_confidence` started as one heuristic for the whole world:
a cadastral key means authoritative, a postcode plus an address line means
probably-right, anything else is weak. That is wrong in both directions.

* An Irish Eircode identifies a single delivery point. A UK postcode covers
  around fifteen addresses and an Indonesian kode pos covers a district. They
  are the same field and they are not remotely the same evidence.
* A French parcelle is a perfectly good key that cannot tell one apartment
  from another in the same building. Treating it as authoritative for a flat
  merges twenty properties into one.

So identity is assessed per country, against three conditions. Most countries
fail the third:

1. a stable unique ID exists **at dwelling granularity**, not just parcel
2. it is in open or obtainable bulk data
3. it is recoverable **from a listing** — quoted outright, or derivable from
   the address deterministically

Germany and Italy are the instructive failures. Both have excellent cadastral
identifiers — Italy's subalterno is genuinely unit-level — and both fail (2)
and (3). A perfect key you cannot get from a listing is worth nothing here.

Each entry carries a `confidence` marking how sure the entry itself is.
"medium" entries are believed correct but have not been checked against the
current source, and licensing in particular moves: several national mapping
agencies have shifted towards open data in recent years. Verify a medium
entry before building an adapter that depends on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class IdentityTier(str, Enum):
    """How well a country supports property identity end to end."""

    S = "S"    # dwelling-level ID, open, derivable from a listing
    A = "A"    # strong, with one caveat
    B = "B"    # strong registry, weak listing linkage
    B_MINUS = "B-"  # strong but namespaced, or key/address mismatch
    C = "C"    # no usable key
    UNKNOWN = "?"


class Granularity(str, Enum):
    DWELLING = "dwelling"
    BUILDING = "building"
    PARCEL = "parcel"
    NONE = "none"


class PostcodePrecision(str, Enum):
    """What a postcode narrows to, when no cadastral key is available."""

    UNIT = "unit"          # IE Eircode: one delivery point
    BUILDING = "building"  # SG: one building; NL: with house number, unique
    STREET = "street"      # GB, ES: a street or street section
    DISTRICT = "district"  # ID, FR: a whole district or commune
    NONE = "none"


#: Property types occupying part of a building. A parcel-level key cannot
#: distinguish these from their neighbours. Compared as plain strings so this
#: module stays free of a schema import — `schema` imports it, not the other
#: way round.
MULTI_UNIT_TYPES = frozenset({"flat", "maisonette"})


@dataclass(frozen=True, slots=True)
class CountryIdentity:
    country: str
    tier: IdentityTier
    #: Human name of the scheme, used in warnings so they name the real thing.
    key_name: str | None
    #: Which `Address` attribute carries it, if any.
    key_field: str | None
    granularity: Granularity
    open_data: bool
    #: Recoverable from a listing — quoted, or deterministically derivable
    #: from the address. A country can be strong and still fail this.
    listing_derivable: bool
    postcode_precision: PostcodePrecision
    #: Set where the key is only unique within a sub-national namespace.
    namespaced_by: str | None = None
    #: How sure this entry is: "high" or "medium". See module docstring.
    confidence: str = "high"
    notes: str = ""


def _entry(country: str, tier: str, **kwargs: Any) -> CountryIdentity:
    return CountryIdentity(country=country, tier=IdentityTier(tier), **kwargs)


REGISTRY: dict[str, CountryIdentity] = {
    # -- Tier S: dwelling-level, open, address-derivable -------------------
    "NL": _entry(
        "NL", "S",
        key_name="BAG verblijfsobject ID", key_field="bag_id",
        granularity=Granularity.DWELLING, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.BUILDING,
        notes="Postcode plus house number is unique, so address -> BAG is "
              "deterministic. Probably the strongest scheme anywhere.",
    ),
    "DK": _entry(
        "DK", "S",
        key_name="BFE-nummer", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.STREET,
        notes="BFE ties straight to the ownership register; DAR gives every "
              "address a UUID. Apartments have their own BFE.",
    ),
    "CH": _entry(
        "CH", "S",
        key_name="EGID / EWID", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.STREET,
        confidence="medium",
        notes="Building plus dwelling identifiers; the textbook design. "
              "Public search is open, bulk access terms vary.",
    ),
    "NO": _entry(
        "NO", "S",
        key_name="Matrikkel (gnr/bnr/fnr/snr)", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.STREET,
        confidence="medium",
        notes="snr is the section number, so apartments resolve.",
    ),
    "EE": _entry(
        "EE", "S",
        key_name="Cadastral unit code", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.STREET,
        confidence="medium",
        notes="Small market, fully digital. Apartment ownerships are "
              "registered separately in the e-Land Register.",
    ),
    # -- Tier A: strong, one caveat each -----------------------------------
    "ES": _entry(
        "ES", "A",
        key_name="referencia catastral", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.STREET,
        notes="Quoted in many listings but not all. The 20-char reference "
              "includes the unit, so flats resolve.",
    ),
    "IE": _entry(
        "IE", "A",
        key_name="Eircode", key_field=None,
        granularity=Granularity.DWELLING, open_data=False,
        listing_derivable=True, postcode_precision=PostcodePrecision.UNIT,
        notes="Identity arrives through the postcode field rather than a "
              "cadastral key: an Eircode is one delivery point. The ECAD "
              "database itself is licensed.",
    ),
    "GB": _entry(
        "GB", "A",
        key_name="UPRN", key_field="uprn",
        granularity=Granularity.DWELLING, open_data=True,
        listing_derivable=False, postcode_precision=PostcodePrecision.STREET,
        notes="Open since 2020 and present in EPC data, but listings never "
              "quote it — a portal source needs an address-matching step.",
    ),
    "NZ": _entry(
        "NZ", "A",
        key_name="LINZ title reference", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.DISTRICT,
        confidence="medium",
        notes="Unit titles cover apartments. Small market.",
    ),
    "CZ": _entry(
        "CZ", "A",
        key_name="RÚIAN / katastr nemovitostí", key_field="parcel_id",
        granularity=Granularity.BUILDING, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.STREET,
        confidence="medium",
        notes="RÚIAN is excellent and open, and underrated. Unit-level "
              "coverage is less certain than building-level.",
    ),
    "SG": _entry(
        "SG", "A",
        key_name="postal code + unit number", key_field=None,
        granularity=Granularity.BUILDING, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.BUILDING,
        notes="A six-digit postcode identifies a single building. Unusual, "
              "and very strong once a unit number is added.",
    ),
    "FR": _entry(
        "FR", "A",
        key_name="parcelle cadastrale", key_field="parcel_id",
        granularity=Granularity.PARCEL, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.DISTRICT,
        notes="Parcel-level is solid and DVF carries it, but copropriété lot "
              "numbers are not public, so apartments degrade.",
    ),
    # -- Tier B: strong registry, weak listing linkage ---------------------
    "DE": _entry(
        "DE", "B",
        key_name="Flurstück", key_field="parcel_id",
        granularity=Granularity.PARCEL, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.STREET,
        notes="ALKIS is state-by-state and largely paid; listings never quote "
              "it. Wohnungsgrundbuch covers apartments separately.",
    ),
    "IT": _entry(
        "IT", "B",
        key_name="foglio / particella / subalterno", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.STREET,
        notes="Subalterno is genuinely unit-level, which makes the missing "
              "open bulk access the whole problem.",
    ),
    "PT": _entry(
        "PT", "B",
        key_name="artigo matricial", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.STREET,
        confidence="medium",
        notes="Fração autónoma covers apartments.",
    ),
    "AT": _entry(
        "AT", "B",
        key_name="Grundstücksnummer + KG", key_field="parcel_id",
        granularity=Granularity.PARCEL, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.STREET,
        confidence="medium",
    ),
    "SE": _entry(
        "SE", "B",
        key_name="fastighetsbeteckning", key_field="parcel_id",
        granularity=Granularity.PARCEL, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.STREET,
        confidence="medium",
        notes="Lantmäteriet access has been opening up; check current terms "
              "before relying on this entry.",
    ),
    "FI": _entry(
        "FI", "B",
        key_name="kiinteistötunnus", key_field="parcel_id",
        granularity=Granularity.PARCEL, open_data=True,
        listing_derivable=False, postcode_precision=PostcodePrecision.STREET,
        confidence="medium",
    ),
    # -- Tier B-: strong but namespaced, or key/address mismatch -----------
    "US": _entry(
        "US", "B-",
        key_name="APN", key_field="parcel_id",
        granularity=Granularity.PARCEL, open_data=True,
        listing_derivable=True, postcode_precision=PostcodePrecision.DISTRICT,
        namespaced_by="county (FIPS)",
        notes="Solid within a county and there are ~3,100 of them with no "
              "national namespace. Every id needs a county qualifier.",
    ),
    "JP": _entry(
        "JP", "B-",
        key_name="地番 (chiban)", key_field="parcel_id",
        granularity=Granularity.PARCEL, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.STREET,
        notes="The registry runs on chiban while postal addresses use 住居表示 "
              "(jūkyo hyōji). The key exists; the join is the hard part.",
    ),
    "AU": _entry(
        "AU", "B-",
        key_name="Lot/Plan (DP, SP for strata)", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=True,
        listing_derivable=False, postcode_precision=PostcodePrecision.DISTRICT,
        namespaced_by="state",
        confidence="medium",
        notes="Strata plans cover apartments. Fragmented by state, with "
              "differing access terms.",
    ),
    # -- Tier C: no usable key ---------------------------------------------
    "TH": _entry(
        "TH", "C",
        key_name="Chanote (Nor Sor 4 Jor) deed number", key_field="parcel_id",
        granularity=Granularity.PARCEL, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.DISTRICT,
        notes="Deeds exist and are not open; listings never quote them.",
    ),
    "ID": _entry(
        "ID", "C",
        key_name=None, key_field=None,
        granularity=Granularity.NONE, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.DISTRICT,
        notes="No open cadastre, no reliable street numbering, kode pos "
              "covers a district. Every record is weak.",
    ),
    "VN": _entry(
        "VN", "C",
        key_name="thửa đất / tờ bản đồ (LURC)", key_field="parcel_id",
        granularity=Granularity.PARCEL, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.DISTRICT,
        notes="Land Use Right Certificates carry parcel and map-sheet "
              "numbers, neither open nor quoted. Note there is no private "
              "land ownership at all — only time-bounded use rights — so the "
              "thing being owned is not the land.",
    ),
    "PH": _entry(
        "PH", "C",
        key_name="TCT / CCT title number", key_field="parcel_id",
        granularity=Granularity.DWELLING, open_data=False,
        listing_derivable=False, postcode_precision=PostcodePrecision.DISTRICT,
        confidence="medium",
        notes="CCT covers condominiums.",
    ),
}

#: Used for any country with no entry. Degrades safely: assume nothing.
UNKNOWN_COUNTRY = CountryIdentity(
    country="??",
    tier=IdentityTier.UNKNOWN,
    key_name=None,
    key_field=None,
    granularity=Granularity.NONE,
    open_data=False,
    listing_derivable=False,
    postcode_precision=PostcodePrecision.NONE,
    confidence="medium",
    notes="No entry for this country; identity treated as weak.",
)

AUTHORITATIVE_FIELDS = ("uprn", "bag_id", "parcel_id")


def get(country: str | None) -> CountryIdentity:
    if not country:
        return UNKNOWN_COUNTRY
    return REGISTRY.get(country.upper(), UNKNOWN_COUNTRY)


@dataclass(frozen=True, slots=True)
class IdentityAssessment:
    #: "authoritative" | "address" | "weak", unchanged from before so that
    #: downstream consumers keep working.
    confidence: str
    tier: IdentityTier
    key_field: str | None
    key_value: str | None
    #: Why this verdict, phrased for a warning message.
    reason: str


def assess(address: Any, property_type: str | None = None) -> IdentityAssessment:
    """Judge how much weight a property id derived from `address` can bear.

    `property_type` is the schema value ("flat", "house", ...). It matters
    because a parcel-level key is authoritative for a house and misleading for
    a flat: every apartment in the building shares it.
    """
    entry = get(getattr(address, "country", None))

    key_field = key_value = None
    for field_name in AUTHORITATIVE_FIELDS:
        value = getattr(address, field_name, None)
        if value:
            key_field, key_value = field_name, value
            break

    if key_value is not None:
        if (
            entry.granularity is Granularity.PARCEL
            and property_type in MULTI_UNIT_TYPES
        ):
            return IdentityAssessment(
                confidence="address",
                tier=entry.tier,
                key_field=key_field,
                key_value=key_value,
                reason=(
                    f"{entry.key_name or key_field} is parcel-level in "
                    f"{entry.country}, so it cannot distinguish one "
                    f"{property_type} from others in the same building"
                ),
            )
        if entry.namespaced_by and ":" not in str(key_value):
            return IdentityAssessment(
                confidence="address",
                tier=entry.tier,
                key_field=key_field,
                key_value=key_value,
                reason=(
                    f"{entry.key_name or key_field} is only unique within a "
                    f"{entry.namespaced_by}; qualify it before merging"
                ),
            )
        return IdentityAssessment(
            confidence="authoritative",
            tier=entry.tier,
            key_field=key_field,
            key_value=key_value,
            reason=f"{entry.key_name or key_field} present",
        )

    postcode = getattr(address, "postcode", None)
    line = getattr(address, "normalised_line", "")

    if postcode and entry.postcode_precision is PostcodePrecision.UNIT:
        return IdentityAssessment(
            confidence="authoritative",
            tier=entry.tier,
            key_field="postcode",
            key_value=postcode,
            reason=(
                f"{entry.key_name or 'postcode'} identifies a single delivery "
                f"point in {entry.country}"
            ),
        )

    if postcode and entry.postcode_precision is PostcodePrecision.BUILDING:
        return IdentityAssessment(
            confidence="address",
            tier=entry.tier,
            key_field="postcode",
            key_value=postcode,
            reason=(
                f"postcode identifies a building in {entry.country} but no "
                "unit number was found"
            ),
        )

    if postcode and line and entry.postcode_precision is PostcodePrecision.STREET:
        return IdentityAssessment(
            confidence="address",
            tier=entry.tier,
            key_field=None,
            key_value=None,
            reason="postcode and address line, but no registry key",
        )

    missing = (
        f"no {entry.key_name}" if entry.key_name else "no registry key exists"
    )
    if entry.postcode_precision in (
        PostcodePrecision.DISTRICT,
        PostcodePrecision.NONE,
    ):
        detail = (
            f"and a postcode in {entry.country} covers a "
            f"{entry.postcode_precision.value}"
        )
    else:
        detail = "and no postcode with an address line"
    return IdentityAssessment(
        confidence="weak",
        tier=entry.tier,
        key_field=None,
        key_value=None,
        reason=f"{missing}, {detail}",
    )
