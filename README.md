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
  db/
    migrations.py      append-only versioned schema
  outreach/
    models.py          organisations, contacts, campaigns, suppressions
    rules.py           per-country direct-marketing rules
    compliance.py      the gate every message passes through
    store.py           persistence
    campaign.py        contact list -> validated outbox
  units.py             area conversion and null-sentinel coercion
  money.py             price parsing across number conventions
  storage.py           SQLite sink: properties + retained raw payloads
  cli.py               python -m propdata ...
  regions/
    identity.py        per-country identity schemes and confidence rules
    indonesia.py       Indonesian tenure vocabulary, Bali admin lookup
    spain.py           cadastral references, Spanish rights, INE provinces
  sources/
    base.py            Source ABC: fetch -> parse -> normalise
    jsonld.py          shared JSON-LD portal framework
    registry.py        source lookup by id
    uk_epc.py          Tier 1: UK EPC register (England & Wales)
    id_bali.py         Tier 2: Bali listings
    es_listings.py     Tier 2: Spanish listings
```

No third-party dependencies. Python 3.11+.

## Usage

```bash
python -m propdata sources
python -m propdata identity --tier S
python -m propdata outreach-rules GB
python -m propdata ingest uk-epc --path /data/epc/ --db properties.db
python -m propdata ingest id-bali-listings --path /data/bali-html/ --db properties.db
python -m propdata ingest es-listings --path /data/es-html/ --db properties.db
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

## What Spain changed

Spain was picked as the second portal market because it is the sharpest
available contrast with Bali: listings routinely quote a **referencia
catastral**, so portal records arrive with authoritative identity rather than
weak. Two portal adapters at opposite corners of the identity model were
enough to extract the framework — which was the point of building it second.

**`sources/jsonld.py` now holds what portal adapters share**: fetching saved
HTML, finding structured data, walking a decoded tree for listing nodes,
flattening `additionalProperty`, the schema.org field mapping, and the shared
failure modes (unknown area unit, rental rate posing as a sale price,
implausible area ratio). Bali went from 502 lines to about 90 and its tests
did not change — which is what makes the extraction believable rather than
merely plausible. What stayed country-specific became the hooks: property-type
vocabulary, location resolution, tenure, default currency and land unit.

**Spain's tenure hazard is a different kind from Indonesia's.** Indonesia's
question is *who may hold this right*. Spain's is *what is actually being
sold*: `nuda propiedad` is ownership stripped of the right to use it, because
a lifetime usufruct is retained, and it sells at a deep discount that is not a
bargain. To anything treating it as freehold it is the cheapest flat on the
street. `TenureFamily` gained `BARE_OWNERSHIP`, `USUFRUCT` and `TIMESHARE`.

**VPO forced a field.** Protected housing is not a tenure family — it is
ordinary ownership with a statutory price ceiling and buyer eligibility rules.
`foreign_holdable` could not express it, since the restriction is by income
and residency rather than nationality, so `Tenure.transfer_restriction`
carries it.

Three bugs surfaced that only a third locale could have exposed:

- **`units.to_float` was parsing numbers under English rules**, so a Spanish
  "parcela 1.100 m2" became 1.1 sqm. Number parsing moved out of `money.py`
  and into `units.py`, where areas get it too.
- **The area-unit regex could not capture the digit in "m2"**, silently
  dropping every area quoted that way.
- **"2.400 € / mes" was stored as an asking price**, because the period
  vocabulary was English and Indonesian only.

## Identity is assessed per country

`identity_confidence` started as one heuristic for the whole world: a
cadastral key means authoritative, a postcode plus an address line means
probably-right, anything else is weak. That is wrong in both directions, and
`regions/identity.py` now holds a table of 25 countries instead.

Two things the global heuristic could not express:

**A postcode is not a postcode.** An Irish Eircode identifies a single
delivery point, so it is authoritative on its own. A Singapore postcode
identifies a *building*, so it needs a unit number. A UK postcode covers
around fifteen addresses and an Indonesian kode pos covers a district. Same
field, four different verdicts.

**A key can be real and still be too coarse.** A French parcelle is a good
identifier and cannot tell one apartment from another in the same building —
so it is authoritative for a house and degrades to "address" for a flat.
That is why `assess_identity` takes the property type. Likewise a US APN is
solid within a county and there are ~3,100 of them with no national
namespace, so an unqualified APN degrades until it carries its county.

Identity strength is three conditions, and most countries fail the third:

1. a stable unique ID at **dwelling** granularity, not just parcel
2. it is in open or obtainable bulk data
3. it is recoverable **from a listing** — quoted, or derivable from the address

Germany and Italy are the instructive failures: both have excellent cadastral
identifiers (Italy's subalterno is genuinely unit-level) and both fail (2) and
(3). A perfect key you cannot get from a listing is worth nothing here.

`python -m propdata identity` prints the table. Entries marked `*` are
believed correct but unverified against the current source — licensing in
particular moves, as several national mapping agencies have opened up in
recent years. Verify before building an adapter that depends on one.

Every stored row carries `identity_confidence` and `identity_tier`, so a
merge step can select what is safe to merge instead of discovering the
problem later as duplicate villas.

## Outreach

Outreach targets **businesses — estate agencies and their staff — not
homeowners.** That is a deliberate scope limit, not an oversight. Marketing to
homeowners means processing personal data for direct marketing with no consent
trail and no existing relationship; it is a different system with a much worse
legal position, and nothing here is built for it.

The whole thing is arranged around one function. `compliance.evaluate` is the
only place that decides whether a contact may be approached, and it returns a
`Decision` that gets written to the audit log **whether it allowed or refused**.
A refusal with a reason is better evidence than a row that was never written:
"we did not contact them" is a claim, and an absent row does not support it.

### What the UK rules actually turn on

The regime is UK GDPR for the personal data and PECR for the electronic
marketing, and they ask different questions. GDPR asks whether there is a
lawful basis to process the data at all; PECR asks whether this channel may be
used to market to this subscriber. A contact can pass one and fail the other,
which is why `corporate_subscriber` still requires a recorded basis.

The distinction doing the real work is **corporate versus individual
subscriber**. A limited company, PLC, LLP or Scottish partnership may receive
B2B marketing email without prior consent. A sole trader or unincorporated
partnership is an individual subscriber and may not — despite being a
business. A large share of estate agencies are sole traders, so this is not an
edge case, and it is why `Organisation.legal_form` is a first-class field
rather than bookkeeping.

Unknown legal form is treated as *not* corporate. Misclassifying a sole trader
as a company is an unlawful send; the reverse is a missed email. The default
fails towards the missed email.

### Rules that are enforced

- **Suppression outranks consent.** An opt-out recorded after consent is a
  withdrawal of it. There is deliberately no `unsuppress`: re-permission is a
  new consent event with its own evidence, not the deletion of a refusal.
- **Suppression is checked at build time against live state**, keyed on the
  normalised identifier rather than a contact row — so deleting and
  re-importing a contact cannot resurrect someone who opted out. The classic
  failure is a list built Monday, sent Friday, and an opt-out on Wednesday.
- **An invalid campaign evaluates nobody.** Missing sender identity or opt-out
  is unlawful for every recipient, so it fails once rather than per contact.
- **Retention expiry blocks.** A contact past `retain_until` should have been
  deleted, and is refused until it is.
- **An unimplemented country is refused, never approximated.** Spain is Tier A
  for identity and its marketing rules are not written, so a Spanish campaign
  is refused rather than run under UK rules.

### What it deliberately does not do

It does not send. No SMTP, no ESP, no dialler — same reasoning as the portal
adapters not crawling. Choosing a transport means accepting its terms,
authentication, rate limits and deliverability practices, and those are
decisions to make deliberately. It produces a validated outbox for a transport
to consume, and **whatever sends must re-check suppression at send time.**

It also does not screen against CTPS/TPS, and does not write your legitimate
interests assessment. `propdata outreach-rules GB` prints the obligations the
system leaves to the operator. None of this is legal advice; the rules encode
a conservative reading so the default is to refuse.

## Adding a source

For a register, subclass `Source`, set `id` / `country` / `tier` / `licence`,
implement the three stages, and register it in `sources/registry.py`.

For a listing portal, subclass `JsonLdPortalSource` instead: set the locale
class attributes, override `resolve_location`, and implement `localise` for
tenure and title handling. `es_listings.py` is about 120 lines and most of
that is vocabulary.

## Roadmap

Three adapters, three countries, both tiers, one framework. The portal
framework has been extracted and is now evidence-backed rather than guessed.

**The Netherlands is the highest-value next adapter.** It is the only Tier S
market where all three identity conditions hold cleanly: BAG gives every
address a dwelling-level id, it is open, and postcode plus house number makes
address -> BAG deterministic. It would be the first market where portal
records reliably reach `authoritative`, which makes it the right place to
build the merge step — merging is far easier to get right where identity is
certain, and it can then be ported down the tiers.

The register path is also still a single implementation, so it is the weaker
half: Denmark BBR or the Dutch BAG would test whether `Source` generalises
the way `JsonLdPortalSource` did. Spain has a Tier 1 register too — the
Catastro publishes parcel and building data through downloadable INSPIRE
services — so `es-catastro` would give the first market with both tiers and a
real join between them on the cadastral reference.

Markets deliberately not next: Vietnam and Thailand are Tier C and would add
no identity capability. Vietnam is still worth building eventually, but for a
different reason — it has no private land ownership at all, only time-bounded
use rights, so it tests the assumption that the thing being owned is the
land.

Open problems, in order of how much engineering they will absorb:

- **Cross-portal deduplication.** One villa, twelve agents, two languages,
  fuzzed map pins, no cadastral key. With Bali records at weak identity
  confidence this is the blocking problem. Spain shows what the solution
  looks like where a key exists — and how little of the world has one.
- **Transport.** The outbox has no sender. Whatever fills that gap must
  re-check suppression immediately before each send.
- **Merging.** Nothing merges records yet. Two sources describing one
  property produce two rows sharing a `property_id`, which is the right
  shape but not the finished job: field-level precedence between a register
  and a portal is undecided.
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

Listing data carries no such licence. Portal records from both Bali and Spain
are stored with `licence = "per-portal terms; not redistributable without
review"` and tier `portal`, so a redistribution query can exclude them by tier
alone.

Spanish Catastro data is published under its own reuse terms and the Catastro
is a fiscal register: its boundaries are not conclusive as to title, which the
Registro de la Propiedad governs. The cadastral reference is used here as an
identity key, nothing more.

The tenure vocabularies in `regions/` are a coarse engineering aid, not legal
advice. The Indonesian flags describe the ordinary case for an individual
foreign natural person; PT PMA structures, nominee arrangements and regulatory
amendments all change the answer. Spanish VPO regimes vary by autonomous
community and vintage.
