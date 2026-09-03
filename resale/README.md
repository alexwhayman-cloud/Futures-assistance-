# L43 — Palm Jumeirah, Frond L Signature Villa

Desk record and owner-approach sheet for **L43**: frond L, villa 43, Palm Jumeirah, Dubai.

**Published:** https://claude.ai/code/artifact/83f7433d-4b46-4b38-9373-b61326636445

| File | What it is |
|---|---|
| `data/L43.json` | The desk record. **Internal** — it holds the exact address. |
| `dist/listing-L43.html` | The sheet. Frond level only; no villa number, ours or a comparable's. |
| `assets/L43/SOURCE.md` | Where the supplied photography lives and how to pull it in. |
| `check-L43.mjs` | Contact firewall, address rule and third-party PII, each with a control. |

## The address rule

See `CLAUDE.md` at the repo root. Published material gives **`Palm Jumeirah`**, at most
**`Frond L, Palm Jumeirah`**. The villa number is never published, in text or in a photograph.

Two extensions applied here:

- **`L43` and `PJFRL043` are themselves exact addresses.** They stay in file names and desk
  records and out of page copy. The published page contains neither.
- **Comparables get the same courtesy.** Every other villa on the page is identified by frond
  letter and date. Their plot codes are in the desk record and nowhere else — publishing a
  comparable's unit number exposes *that* owner's address just as surely.

## The villa

Corroborated across four independent registers in the Drive (see `provenance.sources`):

| | |
|---|---|
| Type | Signature Villa, Gallery View model, Arabic elevation |
| Bedrooms | 6 |
| Built-up | 7,000 sq ft |
| Plot | 13,000 sq ft |
| Held since | September 2007, original purchaser |
| Sale history | **None recorded** in the DLD register, January 2018 to December 2024 |
| Asking price | **None — it is not for sale** |
| Let campaign | February 2025, AED 5.0M then 5.5M a year, several agencies at once |

**This is not a live listing.** The villa is on no sale listing on file. Nineteen years with one
owner and a 2025 rental campaign does not read as a seller, so the page is written as an owner
approach, not a brochure to send a buyer.

## The numbers, and what they rest on

The anchor is the **2024 transaction range for the same villa type: AED 53M–61.5M** — five
registered sales of Signature Villas on the standard plot, from the DLD register. Frond L asking
prices in 2025 ran AED 53M–75M, which is the usual gap between hope and record.

Two cautions are carried in the record and on the page:

- In the source SALE sheet the unit code and the listing URL disagree on several rows, so the 2025
  asks are usable as a **range only**, never row by row.
- The 7,000 / 13,000 sq ft areas are a developer register's round figures, not a survey. The DLD
  type record gives 650.32 sq m built on a 1,244–1,246 sq m plot.

## Owner personal data is deliberately not here

The source registers carry the owner's name, three telephone numbers, an email and a nationality.
**None of it is copied into this repo or any published output.** `data/L43.json` records which
files hold it, and nothing more. `check-L43.mjs` fails the build if a UAE phone number or an owner
email reaches either the page or the record.

## Do not merge this with the E&T "two villas" draft

An Edwards & Towers Instagram draft in the Drive offers two villas, one owner, on an extended
20,494 sq ft plot at AED 97.5M — a 6-bed Signature plus a 4-bed Garden Home. The same registered
owner does hold a second Palm villa, a 4-bed on another frond. But those two plots are on
different fronds and total 19,500 sq ft, not 20,494, so they cannot be the plot described. The
shapes rhyme; the evidence does not connect them.

## Also worth knowing

The Drive folder `ET-Palm-Listing-Correct` and the `ET-Palm-Photos` folder do **not** contain Palm
Jumeirah material. All fifteen PNGs are macOS screenshots of Phuket sale kits — The Trinity Village
and The Victory, by Andaman Asset Solution. `ET-Instagram-Preview-Palm-Villas.html` embeds those
same screenshots, so that preview card shows Phuket brochure pages under a Palm Jumeirah caption.

## Correction, 3 September 2026

The first version of this brochure described **a completely different property** — a villa at The
Teak Phuket, in Thailand — with a full specification, price, comparables and tenure analysis, none
of which related to L43.

The error: the Drive folder was labelled `L43`, and ops review **#43** in the Phuket scraper
happened to be open on a Phuket villa. The number matched, so the property was assumed to match.
It did not. Everything from that version was removed; nothing was carried over.

## Checks

```bash
node resale/check-L43.mjs ../phuket-property-hub/build/lib/firewall.mjs
```

Three groups, each with a control that proves the scan is live rather than silently matching
nothing:

- **Contact firewall** — the page must pass with `allowOwn`, and must *fail* without it on Alex's
  own number.
- **Address rule** — the page must contain no unit code, villa number or frond-and-plot pair,
  and the same patterns must still find the address in the desk record.
- **Third-party PII** — no UAE phone number or owner email in either file.

Verified against a planted villa number: the address check fails as it should.

## Finishing it

1. Open the photography folder. Confirm the frames show this villa; check for identifiable people;
   check no frame shows the villa number, a gate plate or a neighbour's plate.
2. Establish whether the owner will sell at all, and what happened to the 2025 letting.
3. Read the title deed; check the DLD record for mortgages and restrictions; get the service
   charge and any outstanding balance.
4. Fill in the `null`s in `data/L43.json`, clear the matching flags, rebuild and republish.
