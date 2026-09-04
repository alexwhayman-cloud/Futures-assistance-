# Two Coasts × LuxuryProperty.com — phone-safe proposal

Redesign of the partnership proposal for Jason Farr, optimised for iPhone viewing.

| File | Purpose |
|---|---|
| `Two_Coasts_LuxuryProperty_Phone_Safe.pptx` | 27 slides, 9:16 portrait (7.5 in × 13.33 in). Every slide is a single flattened 2160 × 3840 px image with no editable text boxes or shapes. |
| `Two_Coasts_LuxuryProperty_Phone_Safe.pdf` | Same 27 pages for WhatsApp / sharing. |
| `Visual_Check_All_Slides.jpg` | Contact sheet of all slides with the safe-area outline and pass status. |
| `source/build.py` | Content, layout and automated QA (renders slides with Chromium via Playwright). |
| `source/assemble.py` | Builds the flattened PPTX and the PDF from the rendered slide images. |

## Layout system
- Canvas 1080 × 1920 CSS px, rendered at 2× (1 pt = 2 px). Safe area 96 px each side; content zone 250–1690 px, vertically centred.
- Titles Playfair Display 40–43 pt, key numbers 36 pt (hero figures 52 pt), body Inter 19–20 pt, section labels 14 pt, footer 11 pt.
- Palette: deep navy `#0B1B2E`, white, restrained blue `#3F70B5`, light-blue tint `#E8F1F9`, grey `#5F6B7A`.
- Dense original slides were split rather than shrunk (17 → 27 slides). All figures, terms and claims are carried over verbatim.

## Rebuild
```
pip install playwright python-pptx img2pdf pillow
python source/build.py && python source/assemble.py
```
Fonts (Playfair Display, Inter) are loaded from `fonts/` next to `build.py`.
