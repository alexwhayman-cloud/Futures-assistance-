<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="logo/svg/twocoasts-logo-primary-reverse-tagline.svg">
    <img alt="TwoCoasts" src="logo/svg/twocoasts-logo-primary-tagline.svg" width="440">
  </picture>
</p>

# TwoCoasts brand kit

Everything needed to make an app, file or document look like a TwoCoasts product. Read `BRAND_GUIDELINES.md` for the full rules; this page is the quick start.

## Pick a logo

| Need | Use |
|---|---|
| Logo on a light background | `logo/svg/twocoasts-logo-primary.svg` |
| Logo on a dark background | `logo/svg/twocoasts-logo-primary-reverse.svg` |
| Square space | `logo/svg/twocoasts-logo-stacked-primary.svg` |
| Icon only | `logo/svg/twocoasts-mark-day.svg` (light) / `twocoasts-mark-night.svg` (dark) |
| One colour | `logo/svg/twocoasts-logo-mono-navy.svg`, `-white`, `-black` |
| App / store icon | `logo/svg/twocoasts-app-icon.svg` or `logo/favicon/icon-512.png` |
| Browser favicon | copy `logo/favicon/*` |
| Social | `logo/social/` |

PNG versions of every SVG are in `logo/png/` at 1x and 2x. Add `-tagline` to any lockup name for the "DUBAI · THAILAND" version.

## Use the colours

```css
@import "branding/tokens/twocoasts.css";   /* fonts + tokens + light/dark + buttons, cards, tables */
```

| Name | Hex |
|---|---|
| Gulf Navy | `#0B2545` |
| Andaman Teal | `#0FA3B1` |
| Deep Teal (accessible) | `#0B7F8A` |
| Lagoon | `#8EDCD9` |
| Dubai Gold | `#D9A64A` |
| Sand | `#F6ECD9` |
| Ivory | `#FCFAF5` |
| Fairway Green | `#2F9E6B` |
| Sunset Coral | `#F0715F` |
| Charcoal | `#1E2A3A` |
| Driftwood | `#7A7266` |

Other formats: `colors/colors.scss`, `colors/tailwind.colors.js`, `colors/twocoasts.gpl`, `tokens/tokens.json`.

## Use the fonts

Montserrat (headings) and Inter (body). Both load from Google Fonts through `tokens/twocoasts.css`, and the TTFs are in `fonts/` for installing locally or embedding in documents.

## Templates

- `templates/app-shell.html`: web app starter with header, hero, cards, table, buttons, dark mode.
- `templates/letterhead.html`: A4 letter and report template, prints to PDF.
- `templates/email-signature.html`: Outlook-safe signature.
- `templates/markdown-snippets.md`: README headers, badges, MkDocs and Docusaurus config.

## Preview

Open `preview/brand-sheet.html` or look at `preview/brand-sheet.png`.

## Regenerating assets

Logos, PNGs, favicons and social images are generated. Edit `colors/palette.json` or the geometry in `tools/build.mjs`, then:

```bash
npm install fontkit playwright   # once; Chromium is needed for the PNGs
node branding/tools/build.mjs
```
