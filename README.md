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
  money.py             price parsing across number conventions
  storage.py           SQLite sink: properties + retained raw payloads
  cli.py               python -m propdata ...
  regions/
    indonesia.py       Indonesian tenure vocabulary, Bali admin lookup
  sources/
    base.py            Source ABC: fetch -> parse -> normalise
    registry.py        source lookup by id
    uk_epc.py          Tier 1: UK EPC register (England & Wales)
    id_bali.py         Tier 2: Bali listings (saved HTML, JSON-LD first)
```

No third-party dependencies. Python 3.11+.

## Usage

```bash
python -m propdata sources
python -m propdata ingest uk-epc --path /data/epc/ --db properties.db
python -m propdata ingest id-bali-listings --path /data/bali-html/ --db properties.db
python -m unittest discover -s tests -t .
```

For `uk-epc`, `--path` takes the bulk download as it arrives: the `.zip`, a
single `certificates.csv`, or the unpacked directory tree. For
`id-bali-listings` it takes a file or directory of saved listing pages — that
adapter does not crawl, see below.

## Design decisions worth knowing

**Area is always square metres, and land is a separate field from building.**
There is no unit column — it is an invitation to store 1,200 sqft as `1200`
and sort it next to 110 sqm. Convert at the edge in `units.normalise_area`,
which raises on an unknown unit rather than guessing. Land and building area
are distinct because in much of Asia land is the priced asset: a Bali villa is
"5 are, 200 sqm build", and a single area field cannot hold that.

**Tenure is a structured value, not an enum member.** See below — this is the
part the second country broke.

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

## What Bali changed

Bali was picked as the second market specifically to find out whether the
schema generalised or merely fit the UK. It did not generalise. Three things
had to change, and they were all in the same place: the assumption that an
English-law vocabulary describes property everywhere.

**Tenure stopped being an enum.** `LegalTenure.FREEHOLD | LEASEHOLD |
COMMONHOLD | STRATA` cannot express Indonesian land rights. Hak Milik,
Hak Guna Bangunan, Hak Pakai, Hak Sewa and girik differ in *who may hold
them* — the fact that decides whether a listing is purchasable by a given
buyer at all — and flattening them into "freehold" or "leasehold" destroys
exactly that. Tenure is now a `Tenure` record: a coarse `family` for
filtering, the verbatim `local_name` a human should actually read,
`years_remaining` for time-limited rights, and `foreign_holdable`.

**Marketing language is not evidence.** Bali listings routinely advertise
"freehold villas" to foreign buyers who cannot lawfully hold Hak Milik. So an
English adjective maps to a `family` and nothing else — no `local_name`, no
`foreign_holdable` — and the record carries a warning. Only a stated
Indonesian legal term sets the legal fields.

**Identity got a confidence level.** There is no UPRN equivalent, no reliable
street numbering, and postcodes cover whole districts. Every Bali record comes
out `identity_confidence == "weak"` and says so in its warnings, because the
UK assumption that a postcode plus an address line nearly identifies a
property is simply false there.

Two smaller traps, both silent-corruption class:

- **Land is quoted in *are*** (1 are = 100 m²). Reading "5 are" as 5 sqm is a
  clean factor-of-100 error that looks like a plausible studio flat.
- **Indonesian decimal convention is inverted, and "M" means *miliar*.**
  "3,5" is three point five, "1.500.000" is one and a half million, and
  `Rp 3,5 M` is 3.5 billion — where `USD 3.5M` is 3.5 million. Same letter,
  1000x apart. `money.py` resolves the multiplier by currency.

`money.parse_money` also anchors on the currency token rather than taking the
first number in the text, and returns a `period` so that rental rates — Bali
leasehold is often advertised per year — are rejected instead of being stored
as asking prices.

## On scraping Bali

`id_bali.py` reads saved HTML and does not crawl. That is deliberate: a live
crawler needs per-portal terms review, robots handling, rate limiting and an
identifiable user agent, and those are per-portal decisions rather than
defaults to inherit from a scaffold. Parsing is generic — schema.org JSON-LD
first, embedded state second — so it encodes no single portal's markup.

Indonesia has no Tier 1 register to fall back on. ATR/BPN maintains the
cadastre and exposes parcel lookups through Bhumi and Sentuh Tanahku, but
there is no open bulk download comparable to the UK EPC register or the Dutch
BAG. So Bali inverts the sourcing order the rest of the project relies on:
portals are not enrichment on top of a register spine, they are the only
source, and every weakness of listing data lands unmitigated.

## Adding a source

Subclass `Source`, set `id` / `country` / `tier` / `licence`, implement the
three stages, register it in `sources/registry.py`. `run()` wires the pipeline.

## Roadmap

Two adapters exist across two countries and two tiers. The generic scraper
framework still should not be extracted yet — one portal adapter is not
enough evidence about what portal adapters have in common.

Next: a third market that is neither a clean register nor a bare listing
portal. Denmark BBR or the Dutch BAG would confirm the register path
generalises; a second portal market would give the two data points the
framework extraction actually needs.

Open problems, in order of how much engineering they will absorb:

- **Cross-portal deduplication.** One villa, twelve agents, two languages,
  fuzzed map pins, no cadastral key. With Bali records at weak identity
  confidence this is now the blocking problem rather than a future one.
- **Photo copyright.** `image_urls` stores URLs, never bytes, on purpose.
  Listing photographs are separately copyrighted from the listing facts,
  usually by the agency or photographer. Internal matching is one thing;
  serving them is another. Settle it before building image storage.
- **A tenure model that survives a third legal system.** `TenureFamily`
  already carries Indonesian rights. Strata/commonhold variants and
  ground-lease systems will test it again.

## Licensing

Every record carries its source licence in `provenance.licence`, so "can this
row be served to a customer?" stays answerable per row rather than being
re-derived per source months later.

UK EPC data is Open Government Licence v3.0, subject to the register's terms
of use. Bulk download requires free registration at
<https://epc.opendatacommunities.org/>.

Bali listing data carries no such licence. Portal records are stored with
`licence = "per-portal terms; not redistributable without review"` and tier
`portal`, so a redistribution query can exclude them by tier alone.

The Indonesian tenure flags in `regions/indonesia.py` are a coarse engineering
aid, not legal advice: they describe the ordinary case for an individual
foreign natural person, and PT PMA structures, nominee arrangements and
regulatory amendments all change the answer.
