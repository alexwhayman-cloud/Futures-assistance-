# Product (UX/UI) & Print review

Reviewer: Product & Print Designer (virtual design team). Round 1. Rendered templates at 1400 px light/dark, 390 px mobile, dark-OS letterhead, toggled-theme app shell and a 4-page print PDF.

## Strengths

- The semantic token layer is the right shape and dark-mode values are well chosen (lagoon links 9.8:1, status 6.7:1, muted 7.3:1 on navy). The --tc-/.tc- prefix discipline avoids collisions.
- Favicon/PWA set is technically correct: .ico carries 16/32/48, apple-touch-icon 180 opaque, 192/512, maskable inside the safe zone, manifest paths relative so "copy the folder" works.
- Logo naming is systematic and complete; light-mode app shell and letterhead look on-brand; tabular-numeral table is a good default.

## Issues

1. [P0] Letterhead is unreadable on any dark-OS machine: the theme's prefers-color-scheme block wins over the letterhead's light overrides, giving white headings on a white page. Fix: data-theme="light" on the letterhead root; document data-theme as the opt-in/opt-out in README and the CSS header.
2. [P0] Logos do not follow the theme. The header uses a picture/media switch, so the shipped Theme button leaves the navy-text primary logo on a navy header. Footer wordmark is hard-coded navy. Fix: ship light/dark logo pairs toggled by CSS in both dark blocks.
3. [P1] .tc-eyebrow: the dark rule is a dead selector when .tc is on html; light-mode Bunker Gold fails AA at 12 px. Fix: a --tc-eyebrow token in all blocks (light: Deep Teal or Navy; dark: Gold); delete the dead rule; forbid gold text under 18 px on light.
4. [P1] Badges and up/down colours fail AA (white on green 3.4:1, white on coral 2.9:1; .tc-down coral on white 2.9:1; .tc-badge-navy invisible in dark mode). Fix: navy text on green/coral badges; success-text / danger-text tokens (deep green ~#237A52, deep coral ~#C0472F) for .tc-up/.tc-down; outline treatment for navy badge in dark.
5. [P1] Mobile header overflows at 390 px (scrollWidth 442). Fix: flex-wrap, a 640 px breakpoint swapping to the mark, a .tc-nav component.
6. [P1] Letterhead print: footer only on the last page with hard-coded "Page 1"; 40 mm top margin in print; no break rules; economy colour printing hides badges. Fix: print media resets, fixed footer or @page counters, break-after/inside avoid, print-color-adjust exact.
7. [P1] Google Fonts @import hard-wired into the theme (render-blocking, GDPR exposure, fails offline); templates re-declare @font-face to compensate. JetBrains Mono is referenced but never loaded. Fix: local @font-face in twocoasts.css with a documented --tc-font-path, optional separate Google CSS; system mono fallback only.
8. [P1] Component layer too thin: no inputs, alerts, nav, container; no disabled state; anchor and button render at different heights; secondary button on dark needs inline styles; .tc-wave needs inline styles to be useful. Fix: line-height/appearance on .tc-btn, :disabled, .tc-on-dark, wave variants, .tc-input, .tc-alert-*, .tc-nav.
9. [P2] Email signature image path is repo-relative and breaks when pasted; Arial 900 does nothing. Fix: obvious https://YOUR-HOST placeholder; drop fake weight.
10. [P2] Token organisation: three files declare --tc-* on :root; dark block duplicated; colors.css claims to be generated but build.mjs does not write it; tokens.json "0.5x" is not a valid dimension; theme-color meta paints navy chrome over a white header; manifest lacks id/scope. Fix: build.mjs emits CSS/JSON from palette.json; hoist dark tokens; clear-space as description; media-qualified theme-color.

## Verdict

Not as-is. Foundations are good and fixes are cheap, but the two P0s trigger on the most common real condition (a Mac in dark mode). Fix 1-6 for a solid v1; 7 and 8 stop teams writing their own overrides.
