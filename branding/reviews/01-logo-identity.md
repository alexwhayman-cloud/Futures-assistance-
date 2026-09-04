# Logo & Identity review

Reviewer: Senior Logo & Identity Designer (virtual design team). Round 1.

## Strengths

- The concept is sound and ownable: dimpled ball-as-sun over two stacked waves with the pin on the crest says "two coasts + golf" in one object, without a map or palm tree.
- The wordmark is well judged: 500/800 with -0.015/-0.02 tracking does the job of a space without one; the outlined-glyph pipeline makes the SVGs truly portable.
- The single-source generator is the right architecture: every fix below is a constant change and one regeneration.

## Issues

1. [P0] The mark has two different silhouettes depending on background. Night sky = Gulf Navy on the navy backgrounds it is prescribed for; day sky = Sand on sand backgrounds. The disc vanishes and the waves are clipped by an invisible circle, reading as a sun over a boat hull. Fix: night sky -> #123A63; day sky a step darker than Sand (e.g. #EFE1C4), and amend section 2 so sand backgrounds take reverse or mono. Don't ship a mark whose outline changes with context.
2. [P1] Tagline illegible at documented minimums, and no stacked lockup without it (~3.4 px caps at 200 px horizontal; ~1.9 px at 80 px stacked). Fix: stacked with and without tagline; raise drop thresholds to ~360 px horizontal / 320 px stacked or bump tagEm to 0.24 em; single spaces around the middot.
3. [P1] Pin and dimples don't survive small sizes (pin 0.4 px at 24 px; dimples become moire at 64 px). Fix: PIN.w 14, dimple r 8 / step 32, route <=96 px renders through the simple path. Reconcile "mark minimum 24 px" vs "below 32 px use favicon": make it 32.
4. [P1] Mono mark: crescent sliver of sun to the right of the pin (looks like an error, clogs embroidery); lower half is one solid mass because waves and ring merge. Fix: add a mask rect from PIN.x to the sun's right edge between PIN.top and 300; widen gap 12 -> 20; clip waves at R-18; state mono minimum 48 px / 12 mm.
5. [P1] Social banners break the clear-space rule: decorative wave passes behind the lower third of the badge. Fix: waves start at h*0.88 with crest no higher than h*0.80, or logoH 0.42.
6. [P2] Favicon pin still too thin (pinW 16 = 0.5 px at 16 px). Fix: pinW 30 and flag len >= 110 in simple mode, or drop the pin at 16 px.
7. [P2] Horizontal lockup without tagline sits ~17 units low. Fix: nudge em*0.02 or centre on x-height.
8. [P2] Sun floats on the left (50-unit gap at the left shoulder). Fix: SUN.cy 226, or lift WAVE1's first segment to 340/352.

## Verdict

Concept is good; no redesign. Not as-is: item 1 is a real identity problem and 2-5 mean the kit fails its own minimums and clear-space rules on shipped assets. With 1-5 fixed, release; 6-8 in 1.1.
