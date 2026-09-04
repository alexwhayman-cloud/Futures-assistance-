# TwoCoasts typography

Two typefaces, both open source (SIL Open Font License) and free for commercial use. Copies of the variable font files and their licences are in `branding/fonts/`.

| Role | Typeface | Weights used | Why |
|---|---|---|---|
| Display and headings | **Montserrat** | 500, 600, 700, 800 | Geometric, open and sunny. The wordmark is set in it (500 + 800). |
| Body and UI | **Inter** | 400, 500, 600, 700 | Highly legible at small sizes, tabular figures for numbers and odds. |
| Code and data | JetBrains Mono, SF Mono, Menlo, Consolas | 400 | System fallback only. Nothing to install. |

## Getting the fonts

- **Web**: `@import` in `typography/fonts.css` or `tokens/twocoasts.css` pulls both from Google Fonts.
- **Desktop apps, Word, PowerPoint, Google Docs**: install `fonts/Montserrat.ttf` and `fonts/Inter.ttf`. Google Docs and Slides already have both under the fonts menu.
- **Fallbacks**: if a document can't embed fonts, use Arial for body and Arial Bold for headings. Never substitute a serif.

## Scale

| Token | Size | Face | Weight | Use |
|---|---|---|---|---|
| display | 64 px / 4 rem | Montserrat | 800 | Hero titles, cover pages |
| h1 | 48 px / 3 rem | Montserrat | 800 | Page titles |
| h2 | 36 px / 2.25 rem | Montserrat | 700 | Section titles |
| h3 | 22 px / 1.375 rem | Montserrat | 700 | Card and panel titles |
| h4 | 18 px / 1.125 rem | Montserrat | 600 | Sub-headings, table captions |
| body | 16 px / 1 rem | Inter | 400 | Paragraphs |
| body-sm | 14 px / .875 rem | Inter | 400 | Secondary text, tables |
| caption | 12 px / .75 rem | Inter | 500 | Labels, footnotes |
| eyebrow | 12 px / .75 rem | Montserrat | 600, uppercase, +0.18 em tracking | Small labels above headings, taglines |

Headings use tight tracking (-0.02 em) and line-height 1.1 to 1.25. Body line-height is 1.55.

## Rules

1. **Headings in Montserrat, everything else in Inter.** Do not set paragraphs in Montserrat.
2. **Numbers**: use Inter with `font-variant-numeric: tabular-nums` in tables and dashboards so columns align.
3. **Uppercase** only for eyebrows, taglines, badges and table headers, always with wide letter-spacing.
4. **Colour**: headings in Gulf Navy (light) or White (dark). Body in Charcoal (light) or Sand (dark). See `colors/contrast.md` before putting teal, gold, green or coral text on a light background.
5. **The wordmark is a logo, not text.** Don't type "twocoasts" in Montserrat to fake it; use the SVG.

## Print

- Body 10 to 11 pt Inter, headings 18 to 28 pt Montserrat.
- Minimum 8 pt for captions.
- Letterhead and document templates in `templates/` already follow this.
