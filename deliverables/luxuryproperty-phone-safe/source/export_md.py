"""Export the deck content (the S list in build.py) as an editable Markdown file."""
from pathlib import Path
src = Path("build.py").read_text()
ns = {"__file__": str(Path("build.py").resolve())}
exec(src.split("# ------------------------------------------------------------------ CSS")[0], ns)   # content only, no rendering
S = ns["S"]
L = ["# Two Coasts × LuxuryProperty.com", "", "Partnership proposal · September 2026  ", "Prepared by Alex Whayman for Jason Farr, Director, LuxuryProperty.com, Dubai", "",
     "> Edit any line below. Slide numbers match the phone-safe deck. Send the file back and the deck will be rebuilt from it.", ""]
def row(num, label, note):
    s = f"- **{num}** {label}"
    return s + (f" · {note}" if note else "")
for i, s in enumerate(S, 1):
    L += [f"## Slide {i:02d} · {s['eyebrow']}", ""]
    if s["kind"] == "cover":
        L += [f"### {s['title'].replace('|', ' ')}", "", s["sub"], "", f"{s['prepared_1']}  ", s["prepared_2"], "", "Private & Confidential", ""]
        continue
    if s["kind"] == "statement":
        L += [f"### {s['text']}", ""]; continue
    if s["kind"] == "hero":
        for num, label, note in s["heroes"]: L.append(row(num, label, note))
        if s.get("note"): L += ["", s["note"]]
        L.append(""); continue
    L += [f"### {s['title']}", ""]
    if s.get("sub"): L += [s["sub"], ""]
    if s.get("group"): L += [f"**{s['group'].upper()}**", ""]
    for num, label, note in s.get("rows", []): L.append(row(num, label, note))
    for g, (num, label, note) in s.get("grouped_rows", []): L += [f"**{g.upper()}**", row(num, label, note), ""]
    for m, label, note in s.get("lettered", []): L.append(row(m, label, note))
    for tag, text in s.get("tagged", []): L.append(f"- **{tag.upper()}** {text}")
    if s.get("why"): L += [f"**{s['why'][0].upper()}**", "", s["why"][1], "", f"**{s['next_label'].upper()}**", ""]
    for m, text in s.get("numbered", []): L.append(f"- **{m}** {text}")
    if s.get("callout"):
        c = s["callout"]; L += ["", (f"**{c[0].upper()}** " if c[0] else "") + c[1]]
        if len(c) > 2: L.append(c[2])
    if s.get("signoff"): L += ["", s["signoff"]]
    L.append("")
L += ["---", "Footer on every slide: Two Coasts × LuxuryProperty.com · Private & Confidential", ""]
Path("out/Two_Coasts_LuxuryProperty_Deck_Content.md").write_text("\n".join(L), encoding="utf-8")
print("slides exported:", len(S))
