# TwoCoasts brand guidelines

Version 1.0 · September 2026

TwoCoasts is the umbrella brand for a family of apps, files and documents. This guide covers the idea behind the identity, the logo system, colour, typography and how to apply them, so everything we ship looks like it came from the same place.

<p align="center"><img src="logo/svg/twocoasts-logo-primary-tagline.svg" width="480" alt="TwoCoasts logo"></p>

---

## 1. The idea

Two coasts, one game.

The brand lives between two shorelines: the Arabian Gulf at Dubai and the Andaman coast of Thailand. Both are places of sand, warm water and golf played with the sea in view. The identity borrows from all three:

- **Dubai**: desert gold, sunlit sand, clear skies, a polished and premium feel.
- **Thailand**: lagoon turquoise, deep tropical water, an easy warmth.
- **Golf**: the dimpled ball, the flag on the green, the discipline of clean lines.

The mark is a golf ball rising like a sun over two waves. The upper wave is the Andaman, the lower the deeper Gulf. A pin with a pennant stands on the crest, because on both coasts the game is played at the water's edge. Two waves, two coasts.

**Voice.** Calm, confident and specific. Short sentences. Numbers over adjectives. Warm but never gushing. We say "clear view", not "revolutionary insights".

---

## 2. Logo system

All files are in `logo/svg/` (vector, use these whenever you can) with PNG renders in `logo/png/` at 1x and 2x. The wordmark is converted to outlines, so no font needs to be installed for the SVGs to render correctly.

| Asset | File | Use it for |
|---|---|---|
| **Primary logo** | `twocoasts-logo-primary.svg` | Default. Headers, documents, anything on white, ivory or sand. |
| Primary with tagline | `twocoasts-logo-primary-tagline.svg` | Covers, letterheads, hero areas, anywhere the logo is 200 px or wider. |
| **Reverse logo** | `twocoasts-logo-primary-reverse.svg` (+ `-tagline`) | On navy, charcoal, dark photos and the coast gradient. |
| **Stacked logo** | `twocoasts-logo-stacked-primary.svg` | Square spaces: social tiles, app splash screens, badges. |
| Mono navy / white / black | `twocoasts-logo-mono-*.svg` | Single-colour print, embroidery, engraving, watermarks, co-branding rows where colour would clash. |
| **Mark (day)** | `twocoasts-mark-day.svg` | Icon-sized uses on light backgrounds: avatars, list icons, buttons. |
| Mark (night) | `twocoasts-mark-night.svg` | Icon-sized uses on dark backgrounds. |
| Mark mono | `twocoasts-mark-mono-*.svg` | One-colour icon uses. |
| **App icon** | `twocoasts-app-icon.svg`, `twocoasts-app-icon-dark.svg` | iOS, Android, macOS, Windows and PWA icons. Rounded square, full bleed. |
| Wordmark | `twocoasts-wordmark*.svg` | Footers, page headers next to a product name, places the mark is shown separately. |
| Favicon | `logo/favicon/` | Ready-made set: `favicon.svg`, `.ico`, PNG sizes, Apple touch icon, PWA icons, `site.webmanifest`. |
| Social | `logo/social/` | Avatar, X/Twitter banner, LinkedIn banner, Open Graph image. |

### Choosing a version

1. Light background (white, ivory, sand, light photo): **primary**.
2. Dark background (navy, charcoal, coast gradient, dark photo): **reverse**.
3. Only one ink, or the background is busy or a strong colour: **mono** navy, white or black, whichever contrasts most.
4. Space narrower than it is tall: **stacked**.
5. Smaller than 120 px wide: **mark** only.

### Clear space and minimum size

- Keep clear space of at least **half the mark's height** on all sides. Nothing else (text, other logos, edges) goes inside it.
- Minimum sizes: horizontal logo 120 px / 30 mm wide, stacked logo 80 px / 20 mm, mark 24 px. Below 32 px use `favicon.svg`, which drops the dimples and thickens the pin so it stays legible.
- Drop the tagline below 200 px wide.

### Don't

- Don't recolour the logo outside the supplied versions. Don't put the day mark on navy or the night mark on sand.
- Don't stretch, rotate, skew, add shadows, glows, outlines or gradients.
- Don't place the mark and wordmark in a new arrangement. Use the lockups provided.
- Don't set "twocoasts" in Montserrat to imitate the wordmark. Use the SVG.
- Don't put the colour logo on a busy photo without a solid or blurred panel behind it.
- Don't separate the flag or the sun from the mark. The mark is one object.

---

## 3. Colour

Source of truth: `colors/palette.json`. Ready-made exports: `colors/colors.css`, `colors/colors.scss`, `colors/tailwind.colors.js`, `colors/twocoasts.gpl` (GIMP, Inkscape, Krita).

### Core palette

| | Name | Hex | RGB | Role |
|---|---|---|---|---|
| ![](https://placehold.co/20x20/0B2545/0B2545.png) | **Gulf Navy** | `#0B2545` | 11, 37, 69 | Primary. Headings, dark surfaces, the lower wave. |
| ![](https://placehold.co/20x20/0FA3B1/0FA3B1.png) | **Andaman Teal** | `#0FA3B1` | 15, 163, 177 | Primary accent. The upper wave, "coasts". Large text and shapes only on white. |
| ![](https://placehold.co/20x20/0B7F8A/0B7F8A.png) | Deep Teal | `#0B7F8A` | 11, 127, 138 | Accessible teal: links, button fills, small text on light. |
| ![](https://placehold.co/20x20/8EDCD9/8EDCD9.png) | Lagoon | `#8EDCD9` | 142, 220, 217 | Tints, tags, highlights, the upper wave at night. |
| ![](https://placehold.co/20x20/D9A64A/D9A64A.png) | **Dubai Gold** | `#D9A64A` | 217, 166, 74 | The sun. Taglines on dark, premium accents. Decorative on white. |
| ![](https://placehold.co/20x20/B8862E/B8862E.png) | Bunker Gold | `#B8862E` | 184, 134, 46 | Gold text on light backgrounds (large sizes). Dimples. |
| ![](https://placehold.co/20x20/F6ECD9/F6ECD9.png) | **Sand** | `#F6ECD9` | 246, 236, 217 | Warm surfaces. The sky in the mark. |
| ![](https://placehold.co/20x20/FCFAF5/FCFAF5.png) | Ivory | `#FCFAF5` | 252, 250, 245 | Page background. |
| ![](https://placehold.co/20x20/2F9E6B/2F9E6B.png) | Fairway Green | `#2F9E6B` | 47, 158, 107 | Success, positive change, golf accents. |
| ![](https://placehold.co/20x20/F0715F/F0715F.png) | Sunset Coral | `#F0715F` | 240, 113, 95 | Errors, negative change, urgent highlights. |
| ![](https://placehold.co/20x20/1E2A3A/1E2A3A.png) | Charcoal | `#1E2A3A` | 30, 42, 58 | Body text. Dark-mode surface. |
| ![](https://placehold.co/20x20/7A7266/7A7266.png) | Driftwood | `#7A7266` | 122, 114, 102 | Secondary text, captions, borders. |

### Proportions

Think of a page as a beach: mostly Ivory and Sand, a strong line of Navy, a stripe of Teal, and Gold only where the sun hits.

- 60% Ivory / Sand / White
- 25% Gulf Navy (text, headers, dark panels)
- 10% Andaman Teal / Deep Teal (actions, links, highlights)
- 5% Dubai Gold, Fairway Green, Sunset Coral (accents and status only)

### Gradients

- **Coast**: `linear-gradient(120deg, #0B2545 0%, #123A63 60%, #0B7F8A 100%)` for hero panels, covers and banners.
- **Shore**: `linear-gradient(180deg, #FCFAF5 0%, #F6ECD9 100%)` for soft section backgrounds.
- **Sun**: `linear-gradient(180deg, #EFC65E, #D9A64A)` is used inside the mark only.

### Accessibility

Contrast ratios for every pairing are in `colors/contrast.md`. The short version:

- Text on light backgrounds: Gulf Navy, Charcoal, Deep Teal or Driftwood. Andaman Teal, gold, green and coral only at 18 px bold and above, or as shapes and icons.
- Text on Gulf Navy: White, Sand, Lagoon, Dubai Gold, Andaman Teal all pass.
- Buttons: Deep Teal fill with white text (light mode), or Andaman Teal fill with navy text (dark mode). White on Andaman Teal is borderline; avoid it for small text.

### Dark mode

Swap surfaces to `#071A33` / Gulf Navy, body text to Sand, headings to White, links to Lagoon, and use the night mark and reverse logo. `tokens/twocoasts.css` does this automatically from the system preference or `data-theme="dark"`.

---

## 4. Typography

Montserrat for display and headings, Inter for everything else. Both are free (SIL OFL) and included in `fonts/`. Full scale and rules in `typography/typography.md`.

| Role | Face | Weight | Size |
|---|---|---|---|
| Hero | Montserrat | 800 | 48 to 64 px |
| H1 | Montserrat | 800 | 48 px |
| H2 | Montserrat | 700 | 36 px |
| H3 | Montserrat | 700 | 22 px |
| Eyebrow / tagline | Montserrat | 600, uppercase, +0.18 em | 12 px |
| Body | Inter | 400 | 16 px |
| Small / table | Inter | 400 | 14 px |
| Caption | Inter | 500 | 12 px |

The tagline "DUBAI · THAILAND" is always uppercase Montserrat 600 with wide tracking, in Dubai Gold on dark or Bunker Gold on light.

---

## 5. Graphic language

- **The wave.** A single soft wave line can divide sections, sit under a heading, or run along the bottom of a slide. Use the shape from `.tc-wave` in `tokens/twocoasts.css` or copy the path from `tools/build.mjs`. One or two waves, never a pattern.
- **The dimple grid.** Fine dots on a gold or sand field can texture a cover or a card corner at low opacity (under 20%). Use sparingly.
- **Rounded shapes.** Corners of 12 px on cards and 20 px on panels; pill buttons. Nothing sharp-cornered except tables.
- **Photography.** Coastlines at golden hour, fairways beside water, clean architecture, wide horizons. Warm light, low contrast, real places. No stock handshakes, no neon.
- **Icons.** Simple two-tone line icons in Navy with a Teal or Gold accent. 2 px stroke at 24 px.

---

## 6. Applying the brand

### Apps and websites

1. Link `tokens/twocoasts.css` (fonts, tokens, light/dark, base components) or import `tokens/tokens.json` into your design tool.
2. Copy `logo/favicon/*` next to your `index.html` and paste the `<link>` tags from `templates/app-shell.html`.
3. Use the primary logo in the header at 36 to 44 px tall, the reverse logo in dark mode, and the mark alone on mobile.
4. Tailwind: `colors/tailwind.colors.js`.

### Documents

- **Letters, reports, proposals**: start from `templates/letterhead.html` (A4, prints to PDF from any browser).
- **Word / Google Docs**: install the fonts from `fonts/`, use Montserrat 800 for the title, 700 for headings, Inter 11 pt for body. Put `twocoasts-logo-primary-tagline.svg` (or the `@2x` PNG) top-left at 18 mm wide, and the navy mono wordmark in the footer.
- **Slides**: navy title slide with the reverse logo and a coast gradient; ivory content slides with the primary logo small in a corner; Gold for the one number you want remembered.
- **Spreadsheets**: header row Gulf Navy with white Montserrat 600 text; alternate rows Ivory and Sand; positive numbers Fairway Green, negative Sunset Coral.
- **Email**: `templates/email-signature.html`.
- **READMEs and docs sites**: `templates/markdown-snippets.md`.

### Sub-brands and product names

Products sit next to the wordmark, separated by a thin Driftwood rule, set in Montserrat 500 Navy at the same cap height: `twocoasts | Futures`. Products do not get their own marks. If a product needs an icon, use the app icon with a small product glyph in the bottom-right corner, never a different mark.

### Co-branding

Our logo and a partner's sit on the same baseline, separated by a 1 px Driftwood rule with clear space on both sides. Match visual weight, not pixel height.

---

## 7. Files

```
branding/
├── BRAND_GUIDELINES.md         this document
├── README.md                   quick start
├── logo/
│   ├── svg/                    all logo variants (vector, preferred)
│   ├── png/                    1x and 2x renders, mark size ladder
│   ├── favicon/                favicon.svg/.ico, PNGs, apple-touch-icon, PWA icons, site.webmanifest
│   └── social/                 avatar, X banner, LinkedIn banner, Open Graph image
├── colors/                     palette.json, colors.css, colors.scss, tailwind.colors.js, twocoasts.gpl, contrast.md
├── tokens/                     tokens.json (W3C design tokens), twocoasts.css (drop-in theme)
├── typography/                 typography.md, fonts.css
├── fonts/                      Montserrat and Inter variable TTFs + OFL licences
├── templates/                  letterhead, app shell, email signature, markdown snippets
├── preview/                    brand-sheet.html and brand-sheet.png
└── tools/build.mjs             regenerates every logo, PNG, favicon and social image
```

To change the logo or colours, edit `colors/palette.json` or the geometry in `tools/build.mjs`, then run `node branding/tools/build.mjs`. Never hand-edit files in `logo/`; they are overwritten.
