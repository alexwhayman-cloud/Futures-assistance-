# L43 — Palm Jumeirah frond villa

Desk record and brochure for **L43**: frond L, villa 43, Palm Jumeirah, Dubai.

**Published:** https://claude.ai/code/artifact/83f7433d-4b46-4b38-9373-b61326636445

The page is currently a **shell** and says so on its face. It carries the location and nothing
else, because nothing else has been established. Do not send it to a buyer in this state.

| File | What it is |
|---|---|
| `data/L43.json` | The desk record. **Internal** — it holds the exact address. |
| `dist/listing-L43.html` | The brochure. Frond level only, no villa number anywhere in it. |
| `assets/L43/SOURCE.md` | Where the supplied photography lives and how to pull it in. |
| `check-L43.mjs` | Runs the hub's contact firewall against both. |

## The address rule

See `CLAUDE.md` at the repo root. In short: published material gives **`Palm Jumeirah`**, or at
most **`L frond, Palm Jumeirah`**. The villa number is never published, in text or in a photograph.

The reference `L43` is itself an exact address, so it stays in file names and desk records and out
of page titles and body copy. The published page is titled "Palm Jumeirah Frond Villa".

## What is known

- Frond L, Palm Jumeirah, Dubai.
- A photographer has supplied a Drive folder labelled L43, created 1 June 2026 and shared on
  2 September 2026.

That is the whole of it. Price, size, villa type, bedrooms, tenure, service charge and the
instruction position are all outstanding, and the record holds `null` for each rather than a guess.

The Drive folder could not be opened from the session that set this up: it is link-shared rather
than shared to the account, so its files are invisible to the Drive API, and `drive.google.com` is
blocked by that session's egress policy. Nobody has seen the frames.

## Correction, 3 September 2026

The first version of this brochure described **a completely different property** — a villa at The
Teak Phuket, in Thailand — with a full specification, price, comparables and tenure analysis, none
of which had anything to do with L43.

The error: the Drive folder was labelled `L43`, and ops review **#43** in the Phuket scraper
happened to be open on a Phuket villa at the time. The number matched, so the property was assumed
to match. It did not. `L43` is a Palm Jumeirah frond-and-plot reference and always was.

Everything in that version has been removed. Nothing from it was carried into this record — not a
figure, not a comparison, not a flag. The lesson is in `CLAUDE.md`: confirm which property a label
refers to before building on it.

## Finishing it

1. Open the Drive folder. Confirm the frames show this villa; check for identifiable people; check
   no frame shows the villa number, a gate plate or a neighbour's plate.
2. Follow `assets/L43/SOURCE.md` to resize and name them.
3. Enter the specification, price, tenure and service charge in `data/L43.json`, replacing the
   `null`s and clearing the corresponding flags.
4. Rebuild the brochure from the record, remove the "not for circulation" banner, and republish to
   the same artifact URL.

## Firewall check

```bash
node resale/check-L43.mjs ../phuket-property-hub/build/lib/firewall.mjs
```

Checks the brochure and the record for third-party contact details, commission keys and vendor
refs. The control case scans the page *without* `allowOwn` and must fail on Alex's own number —
that proves the scan is live rather than silently matching nothing.

The firewall lives in the Phuket hub and is not vendored here; two divergent copies is how one of
them quietly stops matching a pattern the other still catches. If a Dubai-side equivalent exists in
the Edwards & Towers project, point the script at that instead.

**It does not check the address rule.** No firewall pattern catches a villa number. That one is on
whoever publishes the page.
