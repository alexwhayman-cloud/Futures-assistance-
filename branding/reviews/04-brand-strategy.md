# Brand Strategy & Copy review

Reviewer: Brand Strategist & Copywriter (virtual design team). Round 1.

## Strengths

- The story is compact and the colour naming carries it (Gulf Navy, Andaman Teal, Dubai Gold, Bunker Gold, Fairway Green, Driftwood). A non-designer understands why each colour exists.
- The Documents section speaks in the units its readers use: mm, pt, "header row Gulf Navy with white Montserrat 600".
- The voice contrast pair ("clear view", not "revolutionary insights") is the right kind of rule. There just aren't enough of them.

## Issues

1. [P0] Three different brand lines and two mark descriptions. Guidelines open with "Two coasts, one game." The brand sheet and app shell use "Two coasts. One clear view." The brand sheet header mentions a "skyline" that is not in the mark. Fix: adopt "Two coasts. One clear view." as the slogan (avoids "game", which reads as gambling on a betting product); state that "DUBAI · THAILAND" is a locator that lives only in the lockup; align the brand sheet description with the guidelines.
2. [P0] No casing rule, and the kit breaks it four ways ("twocoasts" in README prose, snippets footer, badge; the email signature fakes the wordmark with styled text, which the Don'ts forbid). Fix: add a Name rule: "TwoCoasts" in all running text; lowercase "twocoasts" only in the drawn wordmark, URLs, handles and code. Correct README, snippets and signature.
3. [P1] The sub-brand rule is not executable: no lockup file exists and it asks people to type "twocoasts" in Montserrat. Fix: build.mjs emits a product lockup (e.g. twocoasts-logo-product-futures.svg); add a prose rule ("TwoCoasts Futures" on first mention, then "Futures").
4. [P1] Voice section is two lines and ignores the category risk (betting: hype and implied guarantees). Fix: a Say / Don't say table plus "Never promise an outcome. We show probabilities and edges; the reader decides."
5. [P1] Word/PowerPoint users still lack: font fallback rule, point sizes, an Office theme colour mapping, slide logo placement. Fix: half a page in section 6 (Arial fallback; title 40 pt / section 28 pt / body 18-20 pt; logo bottom-right 30 mm on content slides, centred 80 mm on title slide; Office theme slots Dark 1 Gulf Navy, Light 1 Ivory, Accent 1 Deep Teal, Accent 2 Dubai Gold, Accent 3 Andaman Teal, Accent 4 Fairway Green, Accent 5 Sunset Coral, Accent 6 Driftwood). Later: real .potx/.dotx.
6. [P1] Factual miss: the Arabian Gulf is shallow, the Andaman Sea is deep, so "the lower, deeper Gulf" is wrong. Say "lower, darker". The golf bridge is one decorative sentence; the letterhead placeholder implies bases in Dubai and Phuket, which if true is the real reason and should lead. (Needs founder confirmation.)
7. [P2] Tagline "DUBAI · THAILAND" is right as a locator; document why city + country and forbid rewrites. build.mjs uses double spaces around the dot while documents use single; pick one.
8. [P2] Placeholder copy will ship by accident (twocoasts.example in letterhead footer and signature). Root README line is vague. Sunlit Gold is on the brand sheet but missing from the guidelines palette table. Fix: bracketed placeholders, a specific README line, add the Sunlit Gold row.

## Verdict

Visual system and document structure are ahead of the words. Two slogans, two mark descriptions and no casing rule, and the templates already contradict each other on all three. Not as-is; fix 1, 2, 4 and 5 and it is ready for v1.0.
