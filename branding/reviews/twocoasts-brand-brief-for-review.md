# TwoCoasts brand kit — review brief

Paste this whole file into Grok or ChatGPT and use the prompts at the end. It is self-contained: it describes every part of the identity in text and includes the logo's SVG source, so a text-only model can reason about it.

---

## 1. Context

- **Brand name**: TwoCoasts. Wordmark is set lowercase as one word: **twocoasts**. Prose uses "TwoCoasts".
- **What it is**: an umbrella identity for a family of apps, files and documents. The first product is a futures/betting analysis tool ("helps choose good bets to make"). More products will follow under the same brand.
- **Inspiration given by the founder**: Dubai beaches, Thailand beaches, and golf.
- **Tagline**: DUBAI · THAILAND (uppercase, wide tracking). There is no slogan yet.
- **Audience**: the founder and collaborators, then customers of each product. Must work on phone apps, websites, Word/PowerPoint/Google Docs, spreadsheets, email, print.

## 2. Brand story (as currently written)

> Two coasts, one game. The brand lives between two shorelines: the Arabian Gulf at Dubai and the Andaman coast of Thailand. Both are places of sand, warm water and golf played with the sea in view.
>
> - Dubai: desert gold, sunlit sand, clear skies, a polished and premium feel.
> - Thailand: lagoon turquoise, deep tropical water, an easy warmth.
> - Golf: the dimpled ball, the flag on the green, the discipline of clean lines.
>
> The mark is a golf ball rising like a sun over two waves. The upper wave is the Andaman, the lower the deeper Gulf. A pin with a pennant stands on the crest, because on both coasts the game is played at the water's edge. Two waves, two coasts.

**Voice**: calm, confident and specific. Short sentences. Numbers over adjectives. Warm but never gushing. "Clear view", not "revolutionary insights".

## 3. The logo

### 3.1 Mark (icon)

A circular badge, 512 × 512 canvas. Elements, back to front:

1. **Sky**: circle r 248 filled Sand `#F6ECD9` (day version) or Gulf Navy `#0B2545` (night version).
2. **Sun / golf ball**: circle centre (236, 214), r 118, vertical gradient Sunlit Gold `#EFC65E` → Dubai Gold `#D9A64A`, with a hex grid of 30 small dimple dots in Bunker Gold `#B8862E` at 45% opacity.
3. **Upper wave** (the Andaman): a filled wave whose crest peaks at x 318, y 300. Andaman Teal `#0FA3B1` by day, Lagoon `#8EDCD9` at night.
4. **Lower wave** (the Gulf): a second, deeper wave. Gulf Navy by day, Andaman Teal at night.
5. **Pin and pennant**: a 9-unit-wide flagstick at x 318 from y 118 down to 302 (planted on the crest), with a triangular pennant 66 long × 44 tall pointing right. Navy by day, white at night.

Geometry as coded:

```js
const SIZE = 512;
const CX = 256;
const CY = 256;
const R = 248; // badge radius
const SUN = { cx: 236, cy: 214, r: 118 };
const PIN = { x: 318, top: 118, base: 302, w: 9 };
const FLAG = { h: 44, len: 66 }; // pennant from pin top pointing right

// Two coasts = two wave crests. Upper wave (Andaman), lower wave (Gulf).
const WAVE1 = 'M0 348 C70 348 118 366 176 366 C250 366 268 300 318 300 C376 300 424 346 512 336 V512 H0 Z';
const WAVE2 = 'M0 424 C80 424 118 392 198 394 C286 396 328 444 404 438 C462 434 490 412 512 408 V512 H0 Z';
```

Full SVG of the day mark (dimples abbreviated):

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-labelledby="t">
  <title id="t">TwoCoasts mark</title>
  <defs>
    <linearGradient id="mark-day-sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#EFC65E"/><stop offset="1" stop-color="#D9A64A"/></linearGradient>
    <clipPath id="mark-day-badge"><circle cx="256" cy="256" r="248"/></clipPath>
  </defs>
  <g clip-path="url(#mark-day-badge)">
    <circle cx="256" cy="256" r="248" fill="#F6ECD9"/>
    <circle cx="236" cy="214" r="118" fill="url(#mark-day-sun)"/>
    <!-- 30 dimple circles (r 6.5, hex grid step 27) clipped to the sun, fill #B8862E at 45% -->
    <path d="M0 348 C70 348 118 366 176 366 C250 366 268 300 318 300 C376 300 424 346 512 336 V512 H0 Z" fill="#0FA3B1"/>
    <path d="M0 424 C80 424 118 392 198 394 C286 396 328 444 404 438 C462 434 490 412 512 408 V512 H0 Z" fill="#0B2545"/>
    <path d="M313.5 118 H322.5 V322 H313.5 Z" fill="#0B2545"/>
    <path d="M321.5 118 L387.5 140 L321.5 162 Z" fill="#0B2545"/>
  </g>
</svg>
```

**Other mark versions**: one-colour (navy, white, black) built as a solid silhouette with 12-unit knocked-out gaps between sun, waves and pin, plus a 14-unit outer ring; an app icon (rounded square, corner radius 112, mark scaled 1.12× so the waves bleed off the edges); a simplified favicon (no dimples, pin thickened to 16 units) for 16–32 px.

### 3.2 Wordmark

"twocoasts" in Montserrat, converted to outlines:
- "two": weight 500, Gulf Navy, tracking −0.015 em.
- "coasts": weight 800, Andaman Teal, tracking −0.02 em. Gap between the two parts: 0.02 em.
- Tagline "DUBAI  ·  THAILAND": Montserrat 600, 0.19× the wordmark size, tracking +0.28 em, centred under the wordmark, Dubai Gold (Bunker Gold on light backgrounds in UI).
- Reverse: "two" white, "coasts" Lagoon, tagline Dubai Gold.

### 3.3 Lockups

- Horizontal: mark (512 tall) + 44-unit gap + wordmark at 236 units em, vertically centred. With and without tagline.
- Stacked: mark at 90% over the wordmark (150 em) with tagline, centred.
- Mono navy / white / black versions of everything.
- Minimums: horizontal 120 px / 30 mm, stacked 80 px / 20 mm, mark 24 px; drop tagline under 200 px wide. Clear space: half the mark's height on every side.

## 4. Colour

| Name | Hex | Role |
|---|---|---|
| Gulf Navy | `#0B2545` | Primary. Headings, body text on light backgrounds, dark surfaces, the lower wave. |
| Andaman Teal | `#0FA3B1` | Primary accent. Buttons, links, the upper wave, 'coasts' in the wordmark. |
| Deep Teal | `#0B7F8A` | Accessible teal for text and hover states on light backgrounds. |
| Lagoon | `#8EDCD9` | Light tint. Highlights, tags, the upper wave on dark backgrounds. |
| Dubai Gold | `#D9A64A` | Secondary accent. The sun/ball, taglines, premium touches. Decorative only on white. |
| Sunlit Gold | `#EFC65E` | Top of the sun gradient. Use only inside the mark and illustrations. |
| Bunker Gold | `#B8862E` | Dimples on the ball, gold text on light backgrounds. |
| Sand | `#F6ECD9` | Warm light surface. The sky in the mark, cards, section backgrounds. |
| Ivory | `#FCFAF5` | Page background. |
| Fairway Green | `#2F9E6B` | Success states, positive numbers, golf-specific accents. |
| Sunset Coral | `#F0715F` | Alerts, errors, negative numbers, urgent highlights. |
| Charcoal | `#1E2A3A` | Body text where navy is too saturated; dark-mode surfaces. |
| Driftwood | `#7A7266` | Secondary text, captions, borders. |
| White | `#FFFFFF` | Text on dark surfaces, reversed logos. |

Gradients: Coast `linear-gradient(120deg, #0B2545 0%, #123A63 60%, #0B7F8A 100%)` for heroes and banners; Shore `#FCFAF5 → #F6ECD9` for soft backgrounds; Sun `#EFC65E → #D9A64A` inside the mark only.

Proportions rule: 60% Ivory/Sand/White, 25% Gulf Navy, 10% Teal, 5% Gold/Green/Coral.

Semantic tokens, light mode: bg Ivory, surface White, warm surface Sand, text Charcoal, headings Gulf Navy, muted Driftwood, links and primary buttons Deep Teal with white text, accent Dubai Gold, border `#E6DCC8`, success Fairway Green, danger Sunset Coral, focus ring Andaman Teal.

Dark mode: bg `#071A33`, surface Gulf Navy, warm surface `#123A63`, text Sand, headings White, muted `#A9B4C4`, links Lagoon, primary Andaman Teal with navy text, border `#1F3F66`, success `#4CBF8A`, danger `#FF8A78`, focus Dubai Gold.

WCAG contrast ratios (text colour by row, background by column):

| Text \ Background | White | Ivory | Sand | Gulf Navy | Charcoal | Andaman Teal |
|---|---|---|---|---|---|---|
| Gulf Navy | 15.4 AAA | 14.8 AAA | 13.1 AAA | 1.0 fail | 1.1 fail | 5.1 AA |
| Charcoal | 14.5 AAA | 13.9 AAA | 12.4 AAA | 1.1 fail | 1.0 fail | 4.8 AA |
| Deep Teal | 4.8 AA | 4.6 AA | 4.1 AA-large | 3.2 AA-large | 3.1 AA-large | 1.6 fail |
| Andaman Teal | 3.0 AA-large | 2.9 fail | 2.6 fail | 5.1 AA | 4.8 AA | 1.0 fail |
| Bunker Gold | 3.2 AA-large | 3.1 AA-large | 2.8 fail | 4.8 AA | 4.5 AA-large | 1.1 fail |
| Dubai Gold | 2.2 fail | 2.1 fail | 1.9 fail | 7.0 AA | 6.6 AA | 1.4 fail |
| Fairway Green | 3.4 AA-large | 3.2 AA-large | 2.9 fail | 4.6 AA | 4.3 AA-large | 1.1 fail |
| Sunset Coral | 2.9 fail | 2.8 fail | 2.5 fail | 5.3 AA | 5.0 AA | 1.0 fail |
| Driftwood | 4.7 AA | 4.5 AA | 4.0 AA-large | 3.2 AA-large | 3.1 AA-large | 1.6 fail |
| White | 1.0 fail | 1.0 fail | 1.2 fail | 15.4 AAA | 14.5 AAA | 3.0 AA-large |
| Lagoon | 1.6 fail | 1.5 fail | 1.3 fail | 9.8 AAA | 9.3 AAA | 1.9 fail |
| Sand | 1.2 fail | 1.1 fail | 1.0 fail | 13.1 AAA | 12.4 AAA | 2.6 fail |

## 5. Typography

- Display and headings: **Montserrat** 500 / 600 / 700 / 800.
- Body and UI: **Inter** 400 / 500 / 600 / 700, tabular numerals in tables.
- Code: system monospace.
- Scale: hero 64, h1 48 (800), h2 36 (700), h3 22 (700), h4 18 (600), body 16, small 14, caption 12, eyebrow 12 uppercase +0.18 em. Heading tracking −0.02 em, heading line-height 1.1–1.25, body 1.55.
- Rules: headings only in Montserrat; uppercase only for eyebrows, taglines, badges, table headers; never fake the wordmark with live text.

## 6. Graphic language

Single soft wave lines as dividers; dimple-grid texture at under 20% opacity on gold/sand; 12 px card corners, 20 px panels, pill buttons; photography of coastlines at golden hour, fairways beside water, clean architecture; two-tone line icons in navy with a teal or gold accent.

## 7. What ships in the kit

SVG + PNG logos in every variant; favicon set (.svg, .ico, PNGs, Apple touch icon, PWA icons, manifest); social images (avatar, X banner, LinkedIn banner, Open Graph); palette as JSON, CSS, SCSS, Tailwind and GIMP; W3C design tokens JSON; a drop-in `twocoasts.css` theme with light/dark and base components (buttons, cards, badges, tables, header, hero, footer, wave divider); Montserrat and Inter fonts (OFL); templates for a web app shell, A4 letterhead, email signature, README and docs-site snippets; a brand guidelines document; a build script that regenerates every asset from the geometry above.

## 8. Known open questions

- Is "DUBAI · THAILAND" enough as a tagline, or does the brand need a slogan (working option: "Two coasts. One clear view.")?
- Does the mark read as "golf" strongly enough, or does it read as a generic sun-and-sea travel logo?
- Is the "two" (500) / "coasts" (800) weight split intentional-looking or does it look like a mistake?
- Andaman Teal fails AA for small text on white (3.0:1), so Deep Teal is used for UI text. Is that split clean enough for non-designers?
- Sub-brands are written as `twocoasts | Futures`. Is a better system needed for a growing product family?

---

## 9. Prompts for sharpening

Copy one at a time.

1. **Concept critique.** "Act as a senior brand identity designer. Using only the description and SVG above, critique the TwoCoasts mark: concept, balance, legibility at 16 px, one-colour reproduction, and how well it bridges Dubai, Thailand and golf. Rank your findings P0/P1/P2 and give exact geometry or colour changes for each."

2. **Naming and tagline.** "Propose 10 slogans for TwoCoasts (calm, specific, no hype), 5 under four words. Then evaluate whether 'DUBAI · THAILAND' should stay as the lockup tagline, become a slogan, or both."

3. **Colour.** "Audit this palette for a product family that shows financial-style numbers. Check colour-vision safety of Fairway Green vs Sunset Coral for up/down, propose an alternative pair if needed, and suggest any missing neutrals or tints with hex values."

4. **Type.** "Judge Montserrat + Inter for this brand versus two alternative pairings. Comment on the 500/800 split in the wordmark and suggest exact tracking and weight values if you would change them."

5. **Documents.** "Write the specification for a Word/Google Docs template and a PowerPoint/Slides template that follow these rules: margins, logo placement and size, heading styles, table style, title slide, section slide, content slide, chart colours."

6. **Product family.** "Design a naming and lockup system for sub-products under TwoCoasts (e.g. Futures, Golf, Travel) that keeps one mark and scales to ten products. Give rules, examples and edge cases."

7. **Red team.** "List everything that could go wrong when a non-designer applies this kit to a spreadsheet, a phone app and a printed letter. For each, give the one-line rule that should be added to the guidelines."
