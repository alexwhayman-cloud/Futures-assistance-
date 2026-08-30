"""Command line entry point: python -m propdata ..."""

from __future__ import annotations

import argparse
import itertools
import sys
from collections.abc import Iterator

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


def cmd_ingest(args: argparse.Namespace) -> int:
    source = get_source(args.source)
    with Store(args.db) as store:
        written = store.write(_limited(source.run(path=args.path), args.limit))
        print(
            f"{source.id}: processed {written} records -> {args.db} "
            f"({store.count()} distinct properties)"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="propdata")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("sources", help="list registered sources").set_defaults(
        func=cmd_sources
    )

    ingest = subparsers.add_parser("ingest", help="load a source into the store")
    ingest.add_argument("source", help="source id, e.g. uk-epc")
    ingest.add_argument("--path", required=True, help="path to the bulk download")
    ingest.add_argument("--db", default="properties.db", help="SQLite file")
    ingest.add_argument("--limit", type=int, default=None, help="stop after N records")
    ingest.set_defaults(func=cmd_ingest)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
