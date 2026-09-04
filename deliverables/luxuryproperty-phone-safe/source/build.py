#!/usr/bin/env python3
"""Build the phone-safe Two Coasts x LuxuryProperty.com deck.

Canvas: 1080 x 1920 CSS px == 7.5in x 13.333in  ->  1pt = 2px.
Rendered at device scale 2 -> 2160 x 3840 px per slide.
"""
import base64, json, os, re, sys, html
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------ palette
NAVY = "#0B1B2E"
WHITE = "#FFFFFF"
ACCENT = "#3F70B5"        # restrained blue on white
ACCENT_ON_DARK = "#9FC2E8"
TINT = "#E8F1F9"          # light-blue statement background
GREY = "#5F6B7A"          # secondary text on white
GREY_ON_DARK = "#B7C7D9"
RULE = "#D5DDE6"
RULE_ON_DARK = "#26405C"
FOOT = "#7A848F"
FOOT_ON_DARK = "#8FA3B8"

FOOTER_TEXT = "Two Coasts × LuxuryProperty.com · Private &amp; Confidential"

NBSP = " "


def nb(s: str) -> str:
    """Escape for HTML and glue numbers to their units / partners with NBSP."""
    s = html.escape(s, quote=False)
    # currency + amount (+ suffix): THB 45bn+, AED 100k, US$400K, ~THB 7.2m
    s = re.sub(r"((?:[>~≥]\s?)?(?:US\$|THB|AED))\s([\d.,]+)", lambda m: m.group(1) + NBSP + m.group(2), s)
    s = re.sub(r"(≥)\s(THB)", r"\1" + NBSP + r"\2", s)
    # ratios 75 / 25
    s = re.sub(r"(\d+)\s/\s(\d+)", lambda m: m.group(1) + NBSP + "/" + NBSP + m.group(2), s)
    # number + unit words
    s = re.sub(r"(\d[\d.,–+]*%?)\s(sqm|yrs|rooms|closings|data|unsigned|international|foreign|Phuket|per|total|residential|condo|pre-sale|airport|transaction)",
               lambda m: m.group(1) + NBSP + m.group(2), s)
    # "H1 2025", "Q1 2026", "s.27", "day 90"
    s = re.sub(r"\b(H1|Q1|DAY|Day)\s(\d{2,4})", lambda m: m.group(1) + NBSP + m.group(2), s)
    # "–10%" pairs: "–4% to –10%"
    s = s.replace("–4% to –10%", "–4%" + NBSP + "to" + NBSP + "–10%")
    s = s.replace("|", "<br>")
    return s


# ------------------------------------------------------------------ content
# Faithful to the original deck: every figure, term and claim is carried over
# verbatim; dense slides are split, never abbreviated.

S = []  # list of slide dicts

S.append(dict(kind="cover",
    eyebrow="Partnership proposal · September 2026",
    title="Two markets.|One distribution|advantage.",
    sub="A verified Phuket inventory and transaction desk for LuxuryProperty.com’s global network.",
    prepared_1="Prepared by Alex Whayman for Jason Farr",
    prepared_2="Director, LuxuryProperty.com, Dubai",
))

S.append(dict(kind="content", eyebrow="The opportunity",
    title="The partnership closes a specific market gap",
    sub="LuxuryProperty.com owns reach. Two Coasts owns verified supply and local execution.",
    rows=[("75", "Verified projects", "Tenure, pricing and measurement traced to source documents."),
          ("GCC + global", "Distribution reach", "A trusted luxury audience ready for Phuket product."),
          ("5", "Revenue lines", "Sales, leasing and specialist investor mandates.")],
    callout=("The result", "A new product line for LuxuryProperty.com—with no Thailand-side buildout."),
))

S.append(dict(kind="content", eyebrow="Proof of execution",
    title="The platform already operates at scale",
    sub="Live inventory and comparable pricing—not a future roadmap.",
    rows=[("75", "developer projects", "Across 15 Phuket areas"),
          ("2,001", "resale units tracked", "~1,000 direct sellers"),
          ("998", "currently available", "Reference-level status"),
          ("12", "developer relationships", "")],
))

S.append(dict(kind="hero", eyebrow="Proof of execution",
    heroes=[(">US$400K", "commission", "One agreed transaction")],
))

S.append(dict(kind="content", eyebrow="Market evidence", compact=True,
    title="Phuket has depth, growth and global demand",
    sub="The market can support a dedicated GCC distribution lane.",
    rows=[("THB 45bn+", "H1 2025 residential sales", "~60% foreign buyers"),
          ("+34.9%", "Q1 2026 condo transfer value", "Highest Thai province"),
          ("62%", "Q1 2026 pre-sale absorption", "Within 90 days"),
          ("17.4m", "2025 airport passengers", "10m international")],
))

S.append(dict(kind="statement", eyebrow="Market evidence",
    text="Phuket now sits with Dubai and Miami among global branded-residence capitals.",
))

S.append(dict(kind="content", eyebrow="Strategic fit",
    title="Phuket diversifies a Dubai-led client base",
    sub="A second coast adds a cycle hedge—not a substitute.",
    group="Gulf demand in Phuket",
    rows=[("~10%", "of Phuket off-plan sales", "From Gulf capital in 2024—and rising"),
          ("+28%", "Saudi arrivals to Thailand", "2024")],
))

S.append(dict(kind="content", eyebrow="Strategic fit",
    title="Dubai market context",
    rows=[("AED 917bn", "2025 transaction value", "A mature, high-volume distribution machine"),
          ("–4% to –10%", "market correction", "From the late-February 2026 peak")],
))

S.append(dict(kind="content", eyebrow="Operating model",
    title="Transactions fund the data moat",
    sub="The platform verifies inventory; the desk monetises it.",
    tagged=[("Source", "Developer files"),
            ("Verify", "Price · size · tenure"),
            ("Distribute", "Dated buyer attribution"),
            ("Close", "Local transaction desk")],
))

S.append(dict(kind="content", eyebrow="Operating model",
    title="Five revenue lines",
    numbered=[("01", "Sales"),
              ("02", "Long-term letting · 10%"),
              ("03", "Licensed short-let · 20%"),
              ("04", "Commercial mandates"),
              ("05", "Investor-incentives desk")],
))

S.append(dict(kind="content", eyebrow="Revenue model",
    title="Five revenue lines create multiple ways to win",
    sub="Start with sales; add recurring and specialist income as the channel proves itself.",
    lettered=[("A", "Sales", "Developer off-plan, primary and resale · immediate pipeline"),
              ("B", "Long-term letting", "10% of gross rent · recurring income"),
              ("C", "Licensed short-let", "20% of gross rent · lawful operator-led delivery"),
              ("D", "Commercial + incentives", "Success fees · specialist investor access")],
    callout=("", "Sales proves the channel. Recurring services compound its value."),
))

S.append(dict(kind="content", eyebrow="Buyer protection",
    title="Lawful routes protect buyer confidence",
    sub="Every buyer and asset is matched to a defensible structure.",
    lettered=[("01", "Foreign freehold condo", "Title in the buyer’s name · verify the 49% project quota"),
              ("02", "Registered 30-year lease", "Fully enforceable term · price on 30 years only"),
              ("03", "BOI-promoted company", "100% foreign ownership · genuine promoted activity required")],
    callout=("", "Thai counsel confirms each structure before commitment.", "Superficies and usufruct remain case-specific."),
))

S.append(dict(kind="content", eyebrow="Large-investor desk",
    title="BOI turns qualifying assets into investable structures",
    sub="For hotels, branded hospitality and wellness—not residential-for-sale.",
    rows=[("100%", "foreign ownership", ""),
          ("s.27", "potential land rights", ""),
          ("3–13 yrs", "CIT exemption", "By activity group")],
))

S.append(dict(kind="content", eyebrow="Large-investor desk",
    title="Hotel entry thresholds",
    lettered=[("A", "100+ rooms", "≥ THB 2m per room"),
              ("B", "Fewer than 100 rooms", "≥ THB 500m total")],
))

S.append(dict(kind="content", eyebrow="Venture economics",
    title="The model pays for reach and execution",
    sub="Distribution becomes recurring venture income.",
    rows=[("AED 100k", "launch contribution", "Paid in full on signing"),
          ("AED 30k", "monthly operator pay", "Venture operating cost"),
          ("75 / 25", "Alex / Jason equity", "85 / 15 if support falls short"),
          ("50 / 50", "LPC-originated deals", "Dated attribution controls")],
))

S.append(dict(kind="hero", eyebrow="Venture economics",
    heroes=[("15 closings", "→ ~THB 7.2m / AED 735k", "gross commission before costs.")],
))

S.append(dict(kind="content", eyebrow="Office strategy",
    title="Ground-floor access matters more than prestige",
    sub="A 120 sqm office must earn its premium through qualified traffic.",
    grouped_rows=[("Preferred corridor", ("Boat / Porto", "Ground floor · 100–150 sqm", "THB 165k rent + service / month")),
                  ("Strongest fallback", ("Blue Tree", "Test if access is weak or the cap is exceeded", "THB 180k maximum all-in occupancy"))],
))

S.append(dict(kind="content", eyebrow="Office strategy",
    title="No lease without",
    numbered=[("01", "Visible signage"),
              ("02", "Client parking"),
              ("03", "Tested footfall"),
              ("04", "Written proposals")],
))

S.append(dict(kind="content", eyebrow="Operating case",
    title="The office runs at THB 618k per month",
    sub="Eight local staff plus a premium ground-floor location.",
    rows=[("THB 283k", "people cost", "Four sales + four support"),
          ("THB 165k", "occupancy target", "Rent + service charges"),
          ("THB 130k", "office operations", "Systems · utilities · travel"),
          ("THB 40k", "local activation", "Office-led marketing")],
))

S.append(dict(kind="hero", eyebrow="Operating case",
    heroes=[("THB 7.42m", "annual fixed cost", ""),
            ("THB 8.547m", "fully loaded", "")],
))

S.append(dict(kind="content", eyebrow="Funding bridge",
    title="AED 100k mobilises the venture—not the office",
    sub="The office remains gated until unit, lease and funding are approved.",
    rows=[("AED 492k", "opening cash", "Startup + three-month runway"),
          ("AED 100k", "launch contribution", "20.3% of opening cash"),
          ("AED 392k", "funding gap", "Source + timing open")],
))

S.append(dict(kind="hero", eyebrow="Funding bridge",
    heroes=[("THB 2.71m", "startup cash", "Fit-out · tech · signage")],
    note="No additional office capital is implied without a separate written decision.",
))

S.append(dict(kind="content", eyebrow="Partnership design",
    title="The commercial frame aligns contribution and reward",
    sub="Equity rewards commitment; deal income follows client source.",
    lettered=[("A", "Equity", "75% Alex / 25% Jason · moves to 85 / 15 if support is not delivered"),
              ("B", "LPC-originated", "50 / 50 · dated referral registration controls attribution"),
              ("C", "Alex-originated", "80 / 20 · independent clients remain outside exclusivity"),
              ("D", "Earned exclusivity", "Three months at US$50k+ LPC fees · quarterly lapse test")],
))

S.append(dict(kind="content", eyebrow="First 90 days",
    title="Start with one verified mandate, then expand",
    sub="A narrow first deal creates proof for the broader relationship.",
    lettered=[("01", "Sign + set up", "Pay AED 100k · instruct Thai counsel · file the DTV and work plan"),
              ("02", "Launch", "Activate the LPC campaign with dated attribution and reporting"),
              ("03", "Prove + scale", "Review pipeline · add partner agencies and Dubai data scope")],
    callout=("", "DAY 90: live referral channel · verified project · reporting cadence"),
))

S.append(dict(kind="content", eyebrow="Risk discipline",
    title="Risk discipline is part of the proposition",
    sub="The plan is stronger when constraints remain visible.",
    tagged=[("Tenure", "Only verified lawful structures enter the catalogue."),
            ("Compliance", "Thai counsel confirms entity, work-permit and BOI files."),
            ("Catalogue", "22 data flags and 36 unsigned commission files remain visible."),
            ("Demand", "Russian, European and Gulf demand carried growth."),
            ("Key person", "Year one depends on Alex; the system is documented and scalable.")],
))

S.append(dict(kind="statement", eyebrow="Risk discipline",
    text="Underwrite today’s law, dated attribution and verified inventory—not launch hype.",
))

S.append(dict(kind="closing", eyebrow="Decision",
    title="Launch together. Gate the office.",
    sub="Launch Two Coasts with LuxuryProperty.com; release office capital only after diligence.",
    why=("Why now", "The platform is ready now; the office proceeds only when location and funding are proven."),
    next_label="Next working session",
    numbered=[("01", "Walk the live catalogue and provenance ledger"),
              ("02", "Agree attribution, economics and reporting"),
              ("03", "Commission three written office proposals"),
              ("04", "Confirm legal entity, funding gates and term sheet")],
    signoff="Alex Whayman · Two Coasts · September 2026",
))

# ------------------------------------------------------------------ CSS
def font_face(name, path, style="normal"):
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return f"@font-face{{font-family:'{name}';font-style:{style};font-weight:100 900;src:url(data:font/ttf;base64,{data}) format('truetype');}}"

CSS = f"""
{font_face('Playfair', HERE / 'fonts/PlayfairDisplay.ttf')}
{font_face('Playfair', HERE / 'fonts/PlayfairDisplay-Italic.ttf', 'italic')}
{font_face('Inter', HERE / 'fonts/inter/InterVariable.ttf')}
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{background:#888;}}
body{{font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased;font-feature-settings:'tnum' 0;}}
.slide{{position:relative;width:1080px;height:1920px;overflow:hidden;background:{WHITE};color:{NAVY};margin:0 0 40px 0;}}
.slide.dark{{background:{NAVY};color:{WHITE};}}
.slide.tint{{background:{TINT};}}
.eyebrow{{position:absolute;left:96px;right:96px;top:124px;font-weight:600;font-size:28px;line-height:36px;
  letter-spacing:0.18em;text-transform:uppercase;color:{ACCENT};white-space:nowrap;}}
.dark .eyebrow{{color:{ACCENT_ON_DARK};}}
.content{{position:absolute;left:96px;right:96px;top:250px;bottom:230px;display:flex;flex-direction:column;justify-content:center;}}
.footer{{position:absolute;left:96px;right:96px;top:1776px;height:2px;background:{RULE};}}
.dark .footer{{background:{RULE_ON_DARK};}}
.foot{{position:absolute;left:96px;top:1802px;font-size:22px;line-height:28px;font-weight:500;letter-spacing:0.09em;
  text-transform:uppercase;color:{FOOT};white-space:nowrap;}}
.pagenum{{position:absolute;right:96px;top:1802px;font-size:22px;line-height:28px;font-weight:500;letter-spacing:0.14em;color:{FOOT};}}
.dark .foot,.dark .pagenum{{color:{FOOT_ON_DARK};}}

.title,.num,.marker,.statement{{font-variant-numeric:lining-nums;font-feature-settings:'lnum' 1;}}
.title{{font-family:'Playfair','Inter',serif;font-weight:600;font-size:80px;line-height:1.12;letter-spacing:-0.01em;text-wrap:balance;}}
.sub{{margin-top:28px;font-size:40px;line-height:1.35;color:{GREY};text-wrap:balance;}}
.dark .sub{{color:{GREY_ON_DARK};}}
.head{{margin-bottom:52px;}}

.group{{font-weight:600;font-size:28px;line-height:36px;letter-spacing:0.16em;text-transform:uppercase;color:{ACCENT};margin-bottom:16px;}}
.group.later{{margin-top:56px;}}
.dark .group{{color:{ACCENT_ON_DARK};}}

.rows{{border-top:2px solid {RULE};}}
.row{{border-bottom:2px solid {RULE};padding:26px 0 28px 0;}}
.dark .rows{{border-top-color:{RULE_ON_DARK};}} .dark .row{{border-bottom-color:{RULE_ON_DARK};}}
.num{{font-family:'Playfair','Inter',serif;font-weight:600;font-size:72px;line-height:1.06;white-space:nowrap;letter-spacing:-0.01em;}}
.label{{margin-top:8px;font-weight:600;font-size:40px;line-height:1.3;text-wrap:balance;}}
.note{{margin-top:6px;font-size:38px;line-height:1.35;color:{GREY};text-wrap:balance;}}
.dark .note{{color:{GREY_ON_DARK};}}

.lrow{{display:grid;grid-template-columns:112px 1fr;column-gap:16px;border-bottom:2px solid {RULE};padding:30px 0 32px 0;}}
.lrows{{border-top:2px solid {RULE};}}
.marker{{font-family:'Playfair','Inter',serif;font-weight:600;font-size:52px;line-height:52px;color:{ACCENT};padding-top:0px;}}
.dark .marker{{color:{ACCENT_ON_DARK};}}
.lrow .label{{margin-top:0;}}

.trow{{border-bottom:2px solid {RULE};padding:26px 0 30px 0;}}
.trows{{border-top:2px solid {RULE};}}
.tag{{font-weight:600;font-size:28px;line-height:36px;letter-spacing:0.16em;text-transform:uppercase;color:{ACCENT};}}
.trow .label{{margin-top:8px;}}

.nrow{{display:grid;grid-template-columns:112px 1fr;column-gap:16px;border-bottom:2px solid {RULE};padding:28px 0 30px 0;align-items:baseline;}}
.nrows{{border-top:2px solid {RULE};}}
.dark .nrows{{border-top-color:{RULE_ON_DARK};}} .dark .nrow{{border-bottom-color:{RULE_ON_DARK};}}
.nrow .label{{margin-top:0;}}

.compact .row{{padding:20px 0 22px 0;}} .compact .head{{margin-bottom:44px;}}
.callout{{margin-top:56px;}}
.callout .tag{{margin-bottom:14px;}}
.callout .text{{font-weight:600;font-size:40px;line-height:1.35;text-wrap:balance;}}
.callout .note{{margin-top:14px;}}

.hero{{}}
.hero .num{{font-size:104px;line-height:1.08;}}
.hero .label{{margin-top:18px;font-size:44px;}}
.hero .note{{margin-top:12px;}}
.hero + .hero{{margin-top:72px;}}
.heronote{{margin-top:80px;padding-top:44px;border-top:2px solid {RULE};font-weight:600;font-size:40px;line-height:1.35;text-wrap:balance;}}

.statement{{font-family:'Playfair','Inter',serif;font-weight:600;font-size:66px;line-height:1.25;text-wrap:balance;letter-spacing:-0.005em;}}

.cover .title{{font-size:86px;color:{WHITE};}}
.cover .sub{{color:{GREY_ON_DARK};}}
.photo{{margin-top:64px;width:888px;height:636px;border-radius:6px;overflow:hidden;}}
.photo img{{width:100%;height:100%;object-fit:cover;display:block;}}
.prepared{{margin-top:64px;font-size:38px;line-height:1.35;font-weight:600;color:{WHITE};text-wrap:balance;}}
.prepared2{{font-size:38px;line-height:1.35;color:{GREY_ON_DARK};text-wrap:pretty;}}

.why{{margin-top:48px;}}
.why .text{{margin-top:12px;font-weight:600;font-size:40px;line-height:1.35;text-wrap:balance;}}
.signoff{{margin-top:48px;font-size:36px;line-height:1.3;color:{GREY_ON_DARK};}}
"""

# ------------------------------------------------------------------ HTML
photo_b64 = base64.b64encode((HERE / "cover_photo.jpg").read_bytes()).decode()


def footer(n, dark=False):
    return (f'<div class="footer"></div><div class="foot">{FOOTER_TEXT}</div>'
            f'<div class="pagenum">{n:02d}</div>')


def render_rows(rows, cls="rows", rowcls="row"):
    out = [f'<div class="{cls}">']
    for num, label, note in rows:
        out.append(f'<div class="{rowcls}"><div class="num">{nb(num)}</div>'
                   f'<div class="label">{nb(label)}</div>'
                   + (f'<div class="note">{nb(note)}</div>' if note else "") + '</div>')
    out.append('</div>')
    return "".join(out)


def render_lettered(items):
    out = ['<div class="lrows">']
    for m, label, note in items:
        out.append(f'<div class="lrow"><div class="marker">{nb(m)}</div><div>'
                   f'<div class="label">{nb(label)}</div>'
                   + (f'<div class="note">{nb(note)}</div>' if note else "") + '</div></div>')
    out.append('</div>')
    return "".join(out)


def render_tagged(items):
    out = ['<div class="trows">']
    for tag, text in items:
        out.append(f'<div class="trow"><div class="tag">{nb(tag)}</div><div class="label">{nb(text)}</div></div>')
    out.append('</div>')
    return "".join(out)


def render_numbered(items):
    out = ['<div class="nrows">']
    for m, text in items:
        out.append(f'<div class="nrow"><div class="marker">{nb(m)}</div><div class="label">{nb(text)}</div></div>')
    out.append('</div>')
    return "".join(out)


def render_callout(c):
    tag, text = c[0], c[1]
    note = c[2] if len(c) > 2 else ""
    h = '<div class="callout">'
    if tag:
        h += f'<div class="tag">{nb(tag)}</div>'
    h += f'<div class="text">{nb(text)}</div>'
    if note:
        h += f'<div class="note">{nb(note)}</div>'
    return h + '</div>'


def slide_html(i, s):
    n = i + 1
    k = s["kind"]
    if k == "cover":
        return (f'<section class="slide dark cover" data-n="{n}">'
                f'<div class="eyebrow">{nb(s["eyebrow"])}</div>'
                f'<div class="content"><div class="title">{nb(s["title"])}</div>'
                f'<div class="sub">{nb(s["sub"])}</div>'
                f'<div class="photo"><img src="data:image/jpeg;base64,{photo_b64}"></div>'
                f'<div class="prepared">{nb(s["prepared_1"])}</div>'
                f'<div class="prepared2">{nb(s["prepared_2"])}</div></div>'
                f'<div class="footer"></div><div class="foot">Private &amp; Confidential</div>'
                f'</section>')
    if k == "statement":
        return (f'<section class="slide tint" data-n="{n}">'
                f'<div class="eyebrow">{nb(s["eyebrow"])}</div>'
                f'<div class="content"><div class="statement">{nb(s["text"])}</div></div>'
                f'{footer(n)}</section>')
    if k == "hero":
        body = ""
        for num, label, note in s["heroes"]:
            body += (f'<div class="hero"><div class="num">{nb(num)}</div><div class="label">{nb(label)}</div>'
                     + (f'<div class="note">{nb(note)}</div>' if note else "") + '</div>')
        if s.get("note"):
            body += f'<div class="heronote">{nb(s["note"])}</div>'
        return (f'<section class="slide" data-n="{n}">'
                f'<div class="eyebrow">{nb(s["eyebrow"])}</div>'
                f'<div class="content">{body}</div>{footer(n)}</section>')
    if k == "closing":
        body = (f'<div class="head"><div class="title">{nb(s["title"])}</div><div class="sub">{nb(s["sub"])}</div></div>'
                f'<div class="why"><div class="tag">{nb(s["why"][0])}</div><div class="text">{nb(s["why"][1])}</div></div>'
                f'<div class="group later">{nb(s["next_label"])}</div>'
                + render_numbered(s["numbered"])
                + f'<div class="signoff">{nb(s["signoff"])}</div>')
        body = body.replace('class="head"', 'class="head" style="margin-bottom:0"')
        return (f'<section class="slide dark" data-n="{n}">'
                f'<div class="eyebrow">{nb(s["eyebrow"])}</div>'
                f'<div class="content">{body}</div>{footer(n, True)}</section>')
    # content
    body = f'<div class="head"><div class="title">{nb(s["title"])}</div>'
    if s.get("sub"):
        body += f'<div class="sub">{nb(s["sub"])}</div>'
    body += '</div>'
    if s.get("group"):
        body += f'<div class="group">{nb(s["group"])}</div>'
    if s.get("rows"):
        body += render_rows(s["rows"])
    if s.get("grouped_rows"):
        for gi, (g, row) in enumerate(s["grouped_rows"]):
            body += f'<div class="group{" later" if gi else ""}">{nb(g)}</div>' + render_rows([row])
    if s.get("lettered"):
        body += render_lettered(s["lettered"])
    if s.get("tagged"):
        body += render_tagged(s["tagged"])
    if s.get("numbered"):
        body += render_numbered(s["numbered"])
    if s.get("callout"):
        body += render_callout(s["callout"])
    return (f'<section class="slide{" compact" if s.get("compact") else ""}" data-n="{n}">'
            f'<div class="eyebrow">{nb(s["eyebrow"])}</div>'
            f'<div class="content">{body}</div>{footer(n)}</section>')


doc = ("<!doctype html><html><head><meta charset='utf-8'><style>" + CSS + "</style></head><body>"
       + "".join(slide_html(i, s) for i, s in enumerate(S)) + "</body></html>")
(OUT / "deck.html").write_text(doc, encoding="utf-8")
print("slides:", len(S))

# ------------------------------------------------------------------ QA + render
QA_JS = r"""
() => {
  const W = 1080, H = 1920, L = 96, R = 1080 - 96, TOP = 100, BOT = 1840;
  const report = [];
  document.querySelectorAll('.slide').forEach(slide => {
    const n = slide.dataset.n;
    const sr = slide.getBoundingClientRect();
    const issues = [];
    const content = slide.querySelector('.content');
    if (content && content.scrollHeight > content.clientHeight + 1)
      issues.push(`content overflow: ${content.scrollHeight} > ${content.clientHeight}`);
    // free space in content zone
    let used = 0; if (content) { for (const c of content.children) used += c.getBoundingClientRect().height + parseFloat(getComputedStyle(c).marginTop); }
    const slack = content ? content.clientHeight - used : 0;
    slide.querySelectorAll('*').forEach(el => {
      const hasText = [...el.childNodes].some(nd => nd.nodeType === 3 && nd.textContent.trim());
      const r = el.getBoundingClientRect();
      const x0 = r.left - sr.left, x1 = r.right - sr.left, y0 = r.top - sr.top, y1 = r.bottom - sr.top;
      if (el.tagName === 'IMG' || el.classList.contains('photo')) {
        if (x0 < L - 1 || x1 > R + 1 || y0 < TOP || y1 > BOT) issues.push(`photo outside safe area ${[x0,y0,x1,y1].map(Math.round)}`);
        return;
      }
      if (!hasText) return;
      const cs = getComputedStyle(el);
      const fs = parseFloat(cs.fontSize);
      const small = el.classList.contains('foot') || el.classList.contains('pagenum');
      const labelish = el.classList.contains('eyebrow') || el.classList.contains('tag') || el.classList.contains('group');
      if (!small && !labelish && fs < 36) issues.push(`font ${fs}px too small: "${el.textContent.trim().slice(0,40)}"`);
      if (labelish && fs < 28) issues.push(`label font ${fs}px: "${el.textContent.trim().slice(0,40)}"`);
      if (small && fs < 22) issues.push(`footer font ${fs}px`);
      if (el.scrollWidth > el.clientWidth + 1) issues.push(`horizontal overflow: "${el.textContent.trim().slice(0,40)}"`);
      if (x0 < L - 2 || x1 > R + 2) issues.push(`text beyond horizontal safe area (${Math.round(x0)}-${Math.round(x1)}): "${el.textContent.trim().slice(0,40)}"`);
      if (y0 < TOP || y1 > BOT) issues.push(`text beyond vertical safe area (${Math.round(y0)}-${Math.round(y1)}): "${el.textContent.trim().slice(0,40)}"`);
      // line analysis: words per line
      const range = document.createRange();
      const lines = new Map();
      for (const nd of el.childNodes) {
        if (nd.nodeType !== 3) continue;
        const txt = nd.textContent;
        const re = /\S+/g; let m;
        while ((m = re.exec(txt))) {
          range.setStart(nd, m.index); range.setEnd(nd, m.index + m[0].length);
          const rects = range.getClientRects(); if (!rects.length) continue;
          const top = Math.round(rects[rects.length-1].top);
          if (!lines.has(top)) lines.set(top, []);
          lines.get(top).push(m[0]);
        }
      }
      const arr = [...lines.entries()].sort((a,b)=>a[0]-b[0]).map(e=>e[1]);
      if (arr.length > 1) {
        const last = arr[arr.length-1];
        const lastLen = last.join(' ').length;
        if ((last.length === 1 && lastLen <= 7) || lastLen <= 5) issues.push(`orphan last line "${last.join(' ')}" in "${el.textContent.trim().slice(0,50)}"`);
        arr.forEach(l => { if (l.length === 1 && l[0].length <= 2) issues.push(`fragment line "${l[0]}"`); });
      }
    });
    report.push({n, slack: Math.round(slack), issues});
  });
  return report;
}
"""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
    page.goto((OUT / "deck.html").as_uri())
    page.evaluate("document.fonts.ready.then(()=>true)")
    page.wait_for_timeout(800)
    report = page.evaluate(QA_JS)
    problems = 0
    for r in report:
        flag = "OK " if not r["issues"] else "!! "
        print(f'{flag}slide {int(r["n"]):02d}  slack={r["slack"]:5d}px')
        for it in r["issues"]:
            problems += 1
            print("      -", it)
    (OUT / "qa_report.json").write_text(json.dumps(report, indent=1))
    for d in (OUT / "slides").glob("slide-*.png"):
        d.unlink()
    (OUT / "slides").mkdir(exist_ok=True)
    for i in range(len(S)):
        el = page.locator(f'.slide[data-n="{i+1}"]')
        el.screenshot(path=str(OUT / "slides" / f"slide-{i+1:02d}.png"), type="png")
    browser.close()
print("problems:", problems)
