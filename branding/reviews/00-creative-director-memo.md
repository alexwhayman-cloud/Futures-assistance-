# Creative Director memo: TwoCoasts kit, round 1 decisions

Consolidates reviews 01-05 for one implementer, one round, one regeneration. The mark concept, the 500/800 wordmark and the palette are approved and not redesigned.

## Decision summary

- Mark gets a permanent silhouette: dedicated mark-only sky colours (day `#EFE1C4`, night `#123A63`); Sand backgrounds take mono navy.
- No palette hex changes. Contrast failures are fixed with new semantic tokens (eyebrow, success/danger text, border-strong, focus) plus a mandatory non-colour cue for up/down.
- Fonts go local: `twocoasts.css` self-hosts Montserrat + Inter (+ new Inter Italic); the Google `@import` leaves the theme.
- One slogan ("Two coasts. One clear view."), one casing rule ("TwoCoasts" in prose, "twocoasts" only drawn/URL/code), one locator ("DUBAI · THAILAND", lockups only).
- Templates survive a Mac in dark mode: `data-theme="light"` on the letterhead, CSS-toggled logo pairs, print rules, bracketed placeholders.

## Conflicts resolved

**(a) Eyebrow colour.** Product wins. Bunker Gold stays `#B8862E` (it is also the dimple colour; `#9C7020` muddies the ball for one text style). Add `--tc-eyebrow`: light `var(--tc-teal-deep)` (4.75:1 on White), dark `var(--tc-gold)`. Gold is never text below 18 px on light; the tagline inside locked logo files is exempt as a logotype.

**(b) Green / coral.** Product's mechanism, colour's rigour. Palette hex unchanged for fills and swatches. Add text tokens: light `--tc-success-text: #1F7A52` (5.2:1 on White), `--tc-danger-text: #C0472F` (5.0:1); dark `#4CBF8A` / `#FF8A78` (existing). `.tc-up`/`.tc-down` use the text tokens and carry a glyph ("▲" / "▼"); guidelines say "never colour alone". Colour's `#E4573F` fails as text (3.7:1).

**(c) Fonts.** Product on hosting, typographer on italics. Remove the `@import` from `twocoasts.css`; local `@font-face` for Montserrat, Inter and new `fonts/Inter-Italic.ttf`; `font-synthesis: none`. Custom properties are invalid inside `@font-face src`, so the font path is a documented `../fonts/` comment, not a `--tc-font-path` variable. `typography/fonts.css` stays as the opt-in Google alternative.

**(d) Day-mark sky.** Logo designer wins. Pre-release is the cheapest moment to fix a mark whose outline changes with context, and consistency is served by giving the disc its own colour. Day `#EFE1C4`, night `#123A63` (already the coast-gradient midpoint). Stored in `palette.json` under a new `mark` block, not `colors`, so swatches and exports do not grow.

**(e) Tagline.** Horizontal stays 0.19 em / 0.28 tracking; stacked becomes 0.22 em / 0.24. Single spaces around the middot. Tagline drops below 320 px / 80 mm horizontal and 240 px / 60 mm stacked; both lockups ship with and without it. Logo's 0.24 em is rejected as a global.

**(f) Slogan and casing.** Strategist wins. Slogan "Two coasts. One clear view."; "Two coasts, one game." removed (reads as gambling). "DUBAI · THAILAND" is a locator, lockups only, never rewritten.

## Round 1 build list

### tools/build.mjs

1. Read `palette.mark.skyDay` / `skyNight`; `mark-day` sky = `#EFE1C4`, `mark-night` sky = `#123A63`. App icons unchanged (full bleed). (Logo #1)
2. `PIN.w` 9 -> 14; dimples `r` 6.5 -> 8, `step` 27 -> 32. (Logo #3)
3. Simple mode: `pinW` 16 -> 30, flag length 80 -> 110. Mark size ladder and any render <= 96 px use `simple: true`. (Logo #3, #6)
4. `markMono`: `gap` 12 -> 20; clip waves at `R - 18`; add mask rect from `PIN.x` to `SUN.cx + SUN.r`, `PIN.top` to 300, to kill the sun sliver right of the pin. (Logo #4)
5. Tagline string `'DUBAI · THAILAND'` (single spaces). Stacked assembler: `tagEm = em * 0.22`, `tracking 0.24`. Emit `twocoasts-logo-stacked-*` **and** `twocoasts-logo-stacked-*-tagline` for primary, reverse and all three monos. (Logo #2, Typo #2, #7, Strategy #7)
6. `socialBanner`: `logoH = h * 0.42`; wave paths start at `h * 0.88` with crests no higher than `h * 0.80`. (Logo #5)
7. New product lockup assembler: wordmark, 1 px Driftwood rule, "Futures" in Montserrat 500 at cap height, outlined. Emit `twocoasts-logo-product-futures.svg` and `-reverse.svg` (PNG ladder picks them up). (Strategy #3)
8. Brand sheet: h1 "TwoCoasts brand kit"; header copy matches guidelines section 1 (no "skyline"); type sample is a real `h3` plus `.tc-small`/`.tc-caption`. (Typo #4, #5, Strategy #1)

### colors/palette.json + exports

9. Add `"mark": { "skyDay": {"name":"Dune","hex":"#EFE1C4"}, "skyNight": {"name":"Night Gulf","hex":"#123A63"} }`, role "Sky inside the mark only". Exports (`colors.css`, `.scss`, `tailwind`, `.gpl`) unchanged; fix `colors.css` header comment that claims generation. (Logo #1, Product #10)
10. `contrast.md`: add rows for the new text tokens, eyebrow, focus and border-strong. (Colour #1-6)

### tokens/tokens.json

11. Add to both semantic sets: `primary-hover` (`#096A73` / `#1FB6C4`), `eyebrow` (`{color.teal-deep}` / `{color.gold}`), `success-text` (`#1F7A52` / `#4CBF8A`), `danger-text` (`#C0472F` / `#FF8A78`), `border-strong` (`{color.driftwood}` / `#4A6690`), `focus` (`{color.teal-deep}` / `{color.gold}`). (Colour #3-6, Product #3-4)
12. `clear-space`: drop the `0.5x` value; keep it as `$description` only. (Product #10)

### tokens/twocoasts.css

13. Remove the Google `@import`. Local `@font-face` for Montserrat (100-900), Inter (100-900), Inter Italic; `font-display: swap`; header comment documents `../fonts/` and `data-theme="light|dark"`. `.tc { font-synthesis: none }`. `--tc-font-mono` becomes a system stack. (Product #7, #1, Typo #1)
14. Light block: `--tc-focus: var(--tc-teal-deep)`; add `--tc-eyebrow`, `--tc-success-text`, `--tc-danger-text`, `--tc-border-strong` per item 11. Mirror in **both** dark blocks. (Colour #3, #6, Product #3)
15. `.tc-eyebrow { color: var(--tc-eyebrow) }`; delete the dead `:root[data-theme="dark"] .tc .tc-eyebrow` rule. (Product #3)
16. `.tc-up`/`.tc-down` use the text tokens; add `.tc-up::before{content:"▲\00a0"}` `.tc-down::before{content:"▼\00a0"}`. (Colour #1, Product #4)
17. `.tc-badge-green`, `.tc-badge-coral`: `color: var(--tc-navy)`. In both dark blocks `.tc-badge-navy { background: transparent; border: 1px solid var(--tc-sand); color: var(--tc-sand) }`. (Colour #2, Product #4)
18. Tracking standardised: `.tc-badge` and `.tc-table th` `letter-spacing: .08em`; `th` `font-weight: 600`; `.tc-table td { font-variant-numeric: tabular-nums }`. (Typo #3, #7)
19. Add `.tc-display` (Montserrat 800, `clamp(48px, 6vw, 64px)`, line-height 1.05), `.tc-small` (Inter 400 14 px), `.tc-caption` (Inter 500 12 px, muted). (Typo #5)
20. `.tc-btn`: `line-height: 1.2; appearance: none`; `:disabled { opacity: .5; cursor: not-allowed }`; add `.tc-on-dark` for the secondary button (Sand text/border). (Product #8, cheap subset)
21. Header: `flex-wrap: wrap`; `.tc-logo-light`/`.tc-logo-dark` pair with `display` toggled in both dark blocks; `@media (max-width: 640px)` swaps lockup for mark. Footer wordmark uses the same pair. (Product #2, #5)
22. `@media print { * { print-color-adjust: exact } .tc-card, .tc-table tr { break-inside: avoid } }`. (Product #6)

### templates

23. `letterhead.html`: `data-theme="light"` on `<html>`; drop duplicate `@font-face`; `@page { margin: 18mm 18mm 22mm }`; footer `position: fixed; bottom: 0` in print, remove "Page 1"; placeholders `[hello@yourdomain]`, `[yourdomain]`. (Product #1, #6, Strategy #8)
24. `app-shell.html`: remove duplicate `@font-face`; light/dark logo `<img>` pair (item 21); `<meta name="theme-color">` media-qualified (Ivory light, Navy dark); `site.webmanifest` gains `id` and `scope`. (Product #2, #10)
25. `email-signature.html`: plain bold "TwoCoasts" (no faked wordmark, no Arial 900); image `src="https://YOUR-HOST/twocoasts-logo-primary@2x.png"`; `[name@yourdomain]`. (Typo #4, Strategy #2, Product #9)
26. `markdown-snippets.md` and `README.md`: "TwoCoasts" in prose; README quick-start names `data-theme` and the local-font copy step; specific one-line root README description. (Strategy #2, #8, Product #1)

### BRAND_GUIDELINES.md / brand-sheet copy

27. Section 1: slogan "Two coasts. One clear view."; "lower, darker Gulf"; Name rule and locator rule; Say / Don't say table (5 pairs) plus "Never promise an outcome. We show probabilities and edges; the reader decides." (Strategy #1, #2, #4, #6, #7)
28. Section 2: rule 1 becomes "white, ivory, light photo: primary; Sand or warm panels: mono navy". Minimums: mark 32 px (remove the 24 px line), mono logo 48 px / 12 mm; tagline thresholds per (e); list the new stacked-without-tagline and product lockup files; sub-brand rule now "use `twocoasts-logo-product-futures.svg`; in prose 'TwoCoasts Futures' on first mention, then 'Futures'". (Logo #1-4, Strategy #3)
29. Section 3: add Sunlit Gold row and a "Mark only" note for Dune / Night Gulf; gold role "Decorative only on light backgrounds; never text outside the locked logo files"; add "Status colours never carry meaning alone: pair with a sign, arrow or label"; hero body text on Coast gradient is White. (Colour #7, #8, Strategy #8)
30. Section 4: rule becomes "Montserrat for headings, labels, buttons, badges, table headers, nav and KPI figures; Inter for running text, tables and captions"; eyebrow colour per (a). (Typo #3)
31. Section 6, Office: Arial fallback; title 40 pt / section 28 pt / body 18-20 pt; logo bottom-right 30 mm on content slides, centred 80 mm on title slide; theme slots Dark 1 Gulf Navy, Light 1 Ivory, Accents 1-6 Deep Teal, Dubai Gold, Andaman Teal, Fairway Green, Sunset Coral, Driftwood. (Strategy #5)

## Deferred to v1.1

- Ink-tight wordmark bbox and removal of the `em * 0.06` fudge; horizontal no-tagline vertical nudge; sun `cy` 226 shoulder fix. (Typo #6, Logo #7, #8)
- Font loading polish: preload links, metric-matched fallback aliases. (Typo #8)
- Full component layer: `.tc-input`, `.tc-alert-*`, wave variants, full `.tc-nav`. (Product #8)
- `build.mjs` emitting `colors.css`/`tokens.json` from `palette.json`; hoisting the duplicated dark block. (Product #10)
- `@page` counters for "Page n of m"; real `.potx`/`.dotx`. (Product #6, Strategy #5)

## Rejected

- Palette hex changes to Fairway Green / Sunset Coral / Bunker Gold: palette is approved; semantic tokens fix the failures. (Colour #1, #4)
- Global tagline 0.24 em: over-scales the horizontal lockup; thresholds do the job. (Logo #2)
- Keeping the Google `@import` in the theme: render-blocking, offline-fail, GDPR exposure. (Typo #1 hosting part)
- Dropping the pin at 16 px: the thicker simple pin survives; keep the mark whole. (Logo #6 alternative)

## Needs founder confirmation

- Real bases in Dubai and Phuket? If yes, that fact leads section 1 and the letterhead gets a real address. (Strategy #6)
- Real domain, email host and image host to replace the bracketed placeholders.
- Product name "TwoCoasts Futures" as the first sub-brand (the lockup is built on it).
- The "probabilities and edges; the reader decides" line is acceptable to whoever owns regulatory wording.

## Sign-off criteria

1. `node branding/tools/build.mjs` runs clean; `logo/`, `preview/` regenerated; no hand edits in `logo/`.
2. Brand sheet PNG: visible disc on the day mark (White and Ivory) and on the reverse logo (navy); mono mark has no sun sliver and clear wave gaps; stacked lockups with and without tagline; product lockup present; h1 "TwoCoasts brand kit".
3. Favicon at 16 px: pin visible; mark ladder PNGs at 64 px show no dimple moire.
4. Social banners: badge clear space (half mark height) contains no wave.
5. Templates at 1400 px light/dark, 390 px, dark-OS: letterhead is white with navy headings; app-shell logos follow the Theme button; no horizontal scroll at 390 px; print preview shows the footer on every page.
6. Contrast spot-check: eyebrow, `.tc-up`, `.tc-down`, both badges, focus ring all >= 4.5:1 text / 3:1 UI; `contrast.md` rows match.
7. Grep: no `fonts.googleapis` in `tokens/`, no `twocoasts.example`, no "One game", no "skyline", no lowercase "twocoasts" in prose outside code/URLs/filenames.
