# Colour & Accessibility review

Reviewer: Colour & Accessibility Specialist (virtual design team). Round 1.

## Strengths

- Core light-mode text system is sound and honestly documented: Charcoal on White 14.5:1, Navy on Sand 13.1:1, Deep Teal on White 4.75:1 (AA), Driftwood on White 4.74:1 (AA). contrast.md matches independent computation.
- Dark mode is strong: Sand on #071A33 14.9:1, Lagoon links on Navy 9.8:1, muted #A9B4C4 on Navy 7.3:1, Navy on Andaman Teal buttons 5.05:1, Gold on Navy 6.96:1. Dark status colours were re-tinted rather than reused.
- The palette evokes the brief: navy + teal + lagoon read as warm sea, sand/ivory as beach, gold as sun and luxury. Fairway Green relegated to status use is the right call; the golf cue lives in the mark.

## Issues

1. [P0] Green vs Coral is not colour-vision-safe for up/down. Under protanopia #2F9E6B and #F0715F collapse to near-identical swatches (dE 4.3, luminance ratio 1.16:1). Dark pair #4CBF8A / #FF8A78 no better. .tc-up/.tc-down carry meaning by colour alone (WCAG 1.4.1). Fix: green -> #1F7A52, coral -> #E4573F so they separate by luminance; and add a non-colour cue (arrow/sign) to .tc-up/.tc-down; state the rule in guidelines.
2. [P0] Green and coral badges ship white text that fails AA: white on #2F9E6B 3.37:1, on #F0715F 2.90:1 at ~11.5 px bold. Fix: navy text on both (4.6:1, 5.3:1) or darker fills; coral badge must use navy text regardless.
3. [P1] Light-mode focus ring (Andaman Teal) fails 3:1 on Ivory (2.92:1). Fix: focus -> Deep Teal #0B7F8A.
4. [P1] Bunker Gold eyebrow text fails AA at 12 px: 3.24:1 on White, 3.10:1 on Ivory, 2.76:1 on Sand. Fix: gold-deep -> #9C7020 (4.42:1 White, 4.24:1 Ivory) and restrict eyebrows to Ivory/White.
5. [P1] Hover colours #096A73 and #1FB6C4 exist only in CSS, not tokens.json. Fix: add primary-hover to both semantic sets.
6. [P1] Borders fail 3:1 for UI components (#E6DCC8 on White 1.36:1; #1F3F66 on Navy 1.44:1). Fine for decoration, not for inputs. Fix: add border-strong (light Driftwood #7A7266, dark #4A6690) and document inputs use it.
7. [P2] Hero body text (Sand) on the teal end of the Coast gradient is 4.06:1. Fix: white body text in heroes or cap gradient end.
8. [P2] Gold role wording invites misuse. Fix: "Decorative only on light backgrounds; never for text outside the locked logo files."

## Verdict

Not as-is. Fix items 1 and 2 plus the cheap focus-ring change in 3 and it can be signed off; 4 to 6 can ship in a 1.0.1 of the token files without touching the logo.
