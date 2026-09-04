# Typography review

Reviewer: Typographer (virtual design team). Round 1.

## Strengths

- The 500/800 wordmark split is intentional and works; in mono versions it is the only thing carrying "two | coasts". Keep 500/800.
- Wordmark is vector outlines from the bundled variable Montserrat; the horizontal tagline proportions (0.19 em, +0.28 em tracking, ~85% width) are right.
- Montserrat + Inter is a sensible free pairing; body defaults (16 px / 1.55, tabular-nums helper) are correct.

## Issues

1. [P1] No italic faces anywhere; every em/i renders faux-oblique. Fix: request Inter italics from Google Fonts, add fonts/Inter-Italic.ttf with an italic @font-face, add font-synthesis: none to .tc.
2. [P1] Stacked lockup only exists with the tagline, but guidelines forbid the tagline under 200 px and allow stacked down to 80 px. At the stacked em the tagline is ~2.8% of file height and illegible on the brand sheet. Fix: emit stacked with and without tagline; in the stacked variant raise tagline to 0.22 em and tracking 0.24.
3. [P1] Rule "headings in Montserrat, everything else in Inter" contradicts the CSS (buttons, badges, table headers, eyebrows, nav and KPI figures are Montserrat). The implementation is right, the rule is wrong. Fix the rule; add tabular-nums to .tc-table td.
4. [P1] The brand sheet h1 and the email signature fake the wordmark in text, breaking Rule 5. Fix: brand sheet h1 -> "TwoCoasts brand" or the SVG; signature uses plain bold "TwoCoasts".
5. [P1] .tc-display has no size/weight; no classes for body-sm or caption; brand sheet shows a 20 px / 600 sample that matches nothing in the scale. Fix: add .tc-display, .tc-small, .tc-caption; make the sample a real h3.
6. [P2] Wordmark bounding box is not ink-tight (height = 1.0 em, ink ~0.62 em), hence the em*0.06 fudge in the horizontal assembler and header logos rendering smaller than intended. Fix: compute real bbox in outline(), size wordmark from ink plus 0.08 em optical margin, delete the fudge.
7. [P2] Tagline uses double spaces on top of +0.28 em tracking, leaving a hole around the dot; uppercase labels use five different trackings across the kit. Fix: single spaces; standardise on .18em (eyebrow/tagline) and .08em (badges/table headers/nav); explicit font-weight 600 on th.
8. [P2] Font loading: render-blocking @import, double download (Google + local @font-face), no metric-matched fallback, unused Montserrat 500. Fix: link/preload in templates, drop 500, add size-adjusted fallback aliases.

## Verdict

Core decisions are right; the layer around it is not release-ready (no italics, stacked-only-with-tagline, a rule the CSS breaks, the kit faking its own wordmark). Not as-is; fix 1-5 and it is releasable, 6-8 as follow-up.
