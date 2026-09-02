# L43 — desk brochure

The brochure for the property carried on the desk as **L43**, plus the listing record that
produced it.

| File | What it is |
|---|---|
| `data/L43.json` | One listing record in the `resale.json` schema, ready to append to `listings` in the phuket-property-hub resale database. Also carries the provenance block tying it back to the sweep. |
| `dist/listing-L43.html` | The brochure. Hand-written in the Two Coasts resale house style rather than emitted by `build-resale.mjs`, because there is no photography to inline yet. |
| `assets/L43/SOURCE.md` | Where the supplied photography lives and how to pull it in. |
| `check-L43.mjs` | Runs the hub's own firewall against both. |

```bash
node resale/check-L43.mjs ../phuket-property-hub/build/lib/firewall.mjs
```

Passing, including the control case: scanned *without* `allowOwn` the page fails on Alex's own
WhatsApp number, which proves the scan is live rather than silently matching nothing. The firewall
is deliberately not vendored into this repo — two divergent copies is how one of them quietly
stops matching a pattern the other still catches.

**Published:** https://claude.ai/code/artifact/83f7433d-4b46-4b38-9373-b61326636445

Artifacts are private until shared from the page's own share menu. Republishing the same file
path updates that URL in place.

## What L43 is

`L43` is the label on the Drive folder the photographer shared. It matches **ops review #43** in
the thbot pipeline, which opened on **PropertyScout listing 1546662** — a 4-bed villa at The Teak
Phuket (Phase 2), Laguna, owner-listed at ฿39,590,000.

That match is **by review number, not by a stored label**. The string `L43` appears nowhere in the
pipeline's own outputs — neither `ops/status.json` nor `resale/data/market.json` contains it — and
the desk keys everything on the portal ref. So the identification rests on the folder's number
matching the review's, and on the folder arriving while that review was the open owner
opportunity. It is a strong match, not a proven one.

If L43 means something else in the scraper chat, the brochure needs repointing. The record to
change is `data/L43.json`; the brochure follows from it.

The folder itself could not be opened from this session: it is link-shared rather than shared to
the account, so its files are invisible to the Drive API, and `drive.google.com` is blocked by the
session's egress policy. Nobody has seen the frames.

## The figures, and why the headline one is not in the brochure

Every number came from the sweep of 1 September 2026, via `resale/data/market.json`.

| | |
|---|---|
| Asking | ฿39,590,000 |
| Rate | ฿69,787/sq.m on 567.3 sq.m built-up |
| Laguna villa median | ฿85,602/sq.m across 188 listings — **18.5% below** |
| Corridor villa median | ฿87,562/sq.m across 333 listings — 20.3% below |
| Other Teak 4-beds | ฿68,677–74,246/sq.m — in line |

Ops review #43 records a **44.4% discount** against seven size-band comparables. That figure is
deliberately not in the brochure. Reconstructing the band on `market.json` (567.3 sq.m ± 25, the
`THBOT_SIZE_BAND` default) returns a bucket whose upper half is POETRY Villas at ~฿118,000/sq.m
and Laguna Homes 2 at ฿114,865/sq.m — a different product tier. That is precisely the case the
pipeline's own `extreme_discount` rule exists to catch: *"discount is too wide to treat as a
bargain without checking the product."*

Against its own scheme the villa is ordinary. The discount belongs to The Teak against Laguna, not
to this villa against The Teak. The brochure says so, and shows all four comparisons with their
populations named.

## What blocks it

Two flags are blocking, and the brochure leads with both:

1. **No instruction.** This is an owner's own portal listing found by the sweep. Two Coasts has no
   mandate and no agreed fee. The owner conversation has to happen before a buyer sees it.
2. **Tenure stated, not proven.** The tenure enrichment recorded `sale_quota = foreigner_quota`
   from the detail page. That is the lister's statement. No title deed, quota certificate or
   building permit has been read. Foreign freehold of land is not available in Thailand, so the
   structure behind a "foreign quota" villa offer needs reading before it is repeated.

Three more are unverified rather than blocking: the size basis is the portal's own unlabelled
figure, the photography has not been reviewed, and there is no feature list — the sweep stores
structured facts only and does not reproduce portal descriptions, so rather than invent one the
brochure renders no features section.

## Finishing it

1. Open the Drive folder, confirm the frames are this villa, and check for identifiable people.
2. Follow `assets/L43/SOURCE.md` to resize and name them.
3. Append the `listing` object from `data/L43.json` to `listings` in the hub's
   `resale/data/resale.json`, set `links[].clientVisible` on the photography entry to `true`, and
   run `node resale/build/build-resale.mjs` so the frames inline as data URIs.
4. Republish to the same artifact URL.
