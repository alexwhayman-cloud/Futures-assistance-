# Futures-assistance-

Property detail collection, normalised across countries.

## What this is

A single canonical property record, plus a source-adapter framework that
everything — official registers and, later, listing portals — normalises into.

Sources split into two tiers, because they have completely different economics:

| | Tier 1 — register | Tier 2 — portal |
|---|---|---|
| Gives you | floor area, property type, built form, rooms, age, energy rating | asking price, photos, agent copy, condition |
| Access | bulk download, cleanly licensed | scraped, ToS-restricted |
| Changes | slowly | constantly |
| Breaks | on annual schema revisions | on any markup change |

Tier 1 first, always. It provides the canonical spine — an authoritative
property identity keyed on UPRN/BAG/parcel — that Tier 2 records attach to.
Scraped listings without that spine are floating strings.

## Layout

```
propdata/
  schema.py            canonical Property record, enums, identity
  units.py             area conversion and null-sentinel coercion
  storage.py           SQLite sink: properties + retained raw payloads
  cli.py               python -m propdata ...
  sources/
    base.py            Source ABC: fetch -> parse -> normalise
    registry.py        source lookup by id
    uk_epc.py          Tier 1: UK EPC register (England & Wales)
```

No third-party dependencies. Python 3.11+.

## Usage

```bash
python -m propdata sources
python -m propdata ingest uk-epc --path /data/epc/ --db properties.db
python -m unittest discover -s tests -t .
```

`--path` takes the EPC bulk download as it arrives: the `.zip`, a single
`certificates.csv`, or the unpacked directory tree.

## Design decisions worth knowing

**Area is always square metres.** There is no unit field. A unit column is an
invitation to store 1,200 sqft as `1200` and sort it next to 110 sqm. Convert
at the edge, in `units.normalise_area`, which raises on an unknown unit rather
than guessing.

**Legal tenure and occupancy are separate fields.** EPC's `TENURE` column says
"Owner-occupied", which is *not* freehold. Conflating them silently corrupts
every jurisdiction that has both, and it is unrecoverable once loaded.

**A row is not a property.** EPC ships certificates; dwellings are re-assessed
and reappear with new keys. `storage` upserts on `(property_id, source_id)`
keeping the most recent assessment, so re-ingesting is idempotent and row
counts are never dwelling counts.

**Raw payloads are retained.** A mapping bug should be a re-normalise, not a
re-crawl. That matters little for a register you can re-download and a lot for
a portal that is slow, rate-limited and legally awkward to hit twice.

**`parse` is separate from `fetch`.** Overkill for a CSV register, where it is
one `DictReader`. It earns its place on portal sources: that is where you try
JSON-LD, then an embedded JSON payload (`__NEXT_DATA__` and friends), and only
then fall back to DOM selectors — all against the same fetched bytes.

## Adding a source

Subclass `Source`, set `id` / `country` / `tier` / `licence`, implement the
three stages, register it in `sources/registry.py`. `run()` wires the pipeline.

## Roadmap

Next Tier 1 loaders, in rough order of data quality: Denmark BBR, Netherlands
BAG, France DPE, US county assessors. Then three portal adapters written by
hand across three countries — and only then extract the generic scraper
framework from whatever those three genuinely had in common.

Two things to settle before Tier 2 starts:

- **Photo copyright.** Listing photos are owned by the photographer or agency,
  separately from the listing facts. Internal matching is one thing; serving
  them is another. Decide before building image storage.
- **Cross-portal deduplication.** One flat, three agents, five portals, two
  languages. Resolution against a canonical address/parcel key is where most
  of the engineering will actually go.

## Licensing

Every record carries its source licence in `provenance.licence`, so "can this
row be served to a customer?" stays answerable per row rather than being
re-derived per source months later.

UK EPC data is Open Government Licence v3.0, subject to the register's terms
of use. Bulk download requires free registration at
<https://epc.opendatacommunities.org/>.
