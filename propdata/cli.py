"""Command line entry point: python -m propdata ..."""

from __future__ import annotations

import argparse
import itertools
import sys
from collections.abc import Iterator

from propdata.outreach import rules as marketing_rules
from propdata.regions.identity import REGISTRY
from propdata.schema import Property
from propdata.sources.registry import SOURCES, get_source
from propdata.storage import Store


def _limited(properties: Iterator[Property], limit: int | None) -> Iterator[Property]:
    return properties if limit is None else itertools.islice(properties, limit)


def cmd_sources(_args: argparse.Namespace) -> int:
    for source_id in sorted(SOURCES):
        source = get_source(source_id)
        print(f"{source.id:<12} {source.country}  {source.tier.value:<9} {source.licence}")
        if source.notes:
            print(f"{'':<12} {source.notes}")
    return 0


def cmd_identity(args: argparse.Namespace) -> int:
    """Print the per-country identity table, strongest first."""
    order = {"S": 0, "A": 1, "B": 2, "B-": 3, "C": 4, "?": 5}
    entries = sorted(
        REGISTRY.values(), key=lambda e: (order[e.tier.value], e.country)
    )
    for entry in entries:
        if args.tier and entry.tier.value != args.tier:
            continue
        flags = "".join(
            [
                "o" if entry.open_data else "-",
                "l" if entry.listing_derivable else "-",
            ]
        )
        mark = "*" if entry.confidence == "medium" else " "
        print(
            f"{entry.tier.value:<3}{mark}{entry.country}  {flags}  "
            f"{entry.granularity.value:<9} pc:{entry.postcode_precision.value:<9} "
            f"{entry.key_name or '(none)'}"
        )
    print("\nflags: o=open data, l=derivable from a listing")
    print("*      entry not verified against the current source")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    source = get_source(args.source)
    with Store(args.db) as store:
        written = store.write(_limited(source.run(path=args.path), args.limit))
        print(
            f"{source.id}: processed {written} records -> {args.db} "
            f"({store.count()} distinct properties)"
        )
    return 0


def cmd_outreach_rules(args: argparse.Namespace) -> int:
    """Show the marketing rules for a country, and what it will refuse."""
    rules = marketing_rules.get(args.country)
    print(f"{rules.country}  {rules.regime}")
    print(f"  implemented: {rules.implemented}")
    if not rules.implemented:
        print("  campaigns for this country are refused until rules are written")
        return 0
    print(
        "  corporate channels without consent: "
        + ", ".join(sorted(c.value for c in rules.corporate_channels_without_consent))
    )
    print(
        "  corporate legal forms: "
        + ", ".join(sorted(f.value for f in rules.corporate_forms))
    )
    if rules.phone_preference_service:
        print(f"  phone screening: {rules.phone_preference_service}")
    if rules.notes:
        print(f"  note: {rules.notes}")
    if rules.operator_obligations:
        print("  obligations this system does NOT enforce for you:")
        for obligation in rules.operator_obligations:
            print(f"    - {obligation}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="propdata")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("sources", help="list registered sources").set_defaults(
        func=cmd_sources
    )

    identity = subparsers.add_parser(
        "identity", help="per-country property identity schemes"
    )
    identity.add_argument("--tier", help="filter to one tier, e.g. S")
    identity.set_defaults(func=cmd_identity)

    ingest = subparsers.add_parser("ingest", help="load a source into the store")
    ingest.add_argument("source", help="source id, e.g. uk-epc")
    ingest.add_argument("--path", required=True, help="path to the bulk download")
    ingest.add_argument("--db", default="properties.db", help="SQLite file")
    ingest.add_argument("--limit", type=int, default=None, help="stop after N records")
    ingest.set_defaults(func=cmd_ingest)

    outreach = subparsers.add_parser(
        "outreach-rules", help="direct-marketing rules for a country"
    )
    outreach.add_argument("country", help="ISO 3166-1 alpha-2, e.g. GB")
    outreach.set_defaults(func=cmd_outreach_rules)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
