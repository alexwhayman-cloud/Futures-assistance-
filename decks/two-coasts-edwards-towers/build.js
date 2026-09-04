// Builds the phone-safe Two Coasts × Edwards and Towers deck from the outline in deck.md.
// Run: node build.js   → writes Two-Coasts-x-Edwards-and-Towers.pptx
const pptxgen = require('pptxgenjs');

const INK = '0E1A2B', INK2 = '1A2A40', PAPER = 'FFFFFF', TINT = 'F4F1EA', SAND = 'E6DCC6';
const GOLD = 'B8963E', GOLD_TXT = '8F7226', TEXT = '22303F', MUTED = '6B7482', LINE = 'D9D2C3';
const HEAD = 'Cambria', BODY = 'Calibri';
const W = 5.625, H = 10, M = 0.45, CW = W - 2 * M;
const FOOTER = 'Two Coasts × Edwards and Towers · Private & Confidential';

const pres = new pptxgen();
pres.defineLayout({ name: 'PHONE', width: W, height: H });
pres.layout = 'PHONE';
pres.author = 'Alex Whayman'; pres.company = 'Two Coasts';
pres.title = 'Two Coasts × Edwards and Towers · Partnership proposal';

// Greedy word-wrap estimate: average glyph width = pt * factor (points).
const lines = (txt, pt, width, factor) => {
  const cw = pt * factor / 72;
  return txt.split('\n').reduce((n, para) => {
    let count = 1, cur = 0;
    for (const w of para.split(' ')) {
      const ww = w.length * cw, sp = cur ? cw : 0;
      if (cur + sp + ww > width && cur > 0) { count += 1; cur = ww; } else cur += sp + ww;
    }
    return n + count;
  }, 0);
};
const hHead = (t, pt, w = CW) => lines(t, pt, w, 0.62) * pt * 1.22 / 72 + 0.08;
const hBody = (t, pt, w = CW) => lines(t, pt, w, 0.52) * pt * 1.25 / 72 + 0.06;

let n = 0; const TOTAL = 27;
function chrome(slide, dark, kicker, tight) {
  n += 1;
  slide.background = { color: dark ? INK : PAPER };
  slide.addText(kicker.toUpperCase(), { x: M, y: 0.42, w: CW - 0.8, h: 0.25, margin: 0, isTextBox: true,
    fontFace: BODY, fontSize: tight ? 8 : 8.5, bold: true, color: GOLD, charSpacing: tight ? 1.2 : 2.5, valign: 'middle' });
  slide.addText(String(n).padStart(2, '0') + ' / ' + TOTAL, { x: W - M - 0.8, y: 0.42, w: 0.8, h: 0.25, margin: 0, isTextBox: true,
    fontFace: BODY, fontSize: 8.5, color: dark ? SAND : MUTED, align: 'right', valign: 'middle' });
  slide.addText(FOOTER, { x: M, y: H - 0.5, w: CW, h: 0.22, margin: 0, isTextBox: true,
    fontFace: BODY, fontSize: 7.5, color: dark ? SAND : MUTED, align: 'center', valign: 'middle' });
}
// Motif: a large gold ring bleeding off the corner of dark slides.
function ring(slide, x, y, d) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { type: 'none' }, line: { color: GOLD, width: 1.25, transparency: 55 } });
}

// ---------- row renderers (return height used) ----------
function statCard(slide, y, r, dark) {
  const pad = 0.18, w = CW;
  const vPt = 20, lPt = 11.5, dPt = 10.5;
  const hv = hHead(r.v, vPt, w - 2 * pad), hl = hBody(r.l, lPt, w - 2 * pad), hd = r.d ? hBody(r.d, dPt, w - 2 * pad) : 0;
  const h = pad + hv + hl + hd + pad - 0.06;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y, w, h, rectRadius: 0.08, fill: { color: dark ? INK2 : TINT }, line: { color: dark ? INK2 : TINT, width: 0 } });
  slide.addText(r.v, { x: M + pad, y: y + pad - 0.02, w: w - 2 * pad, h: hv, margin: 0, isTextBox: true, fontFace: HEAD, fontSize: vPt, bold: true, color: dark ? GOLD : GOLD_TXT, valign: 'top' });
  slide.addText(r.l, { x: M + pad, y: y + pad + hv - 0.04, w: w - 2 * pad, h: hl, margin: 0, isTextBox: true, fontFace: BODY, fontSize: lPt, bold: true, color: dark ? PAPER : TEXT, valign: 'top' });
  if (r.d) slide.addText(r.d, { x: M + pad, y: y + pad + hv + hl - 0.06, w: w - 2 * pad, h: hd, margin: 0, isTextBox: true, fontFace: BODY, fontSize: dPt, color: dark ? SAND : MUTED, valign: 'top' });
  return h + 0.14;
}
function numRow(slide, y, r, dark) {
  const d = 0.46, gap = 0.2, tx = M + d + gap, tw = CW - d - gap;
  const lPt = 12, dPt = 10.5;
  const hl = hBody(r.l, lPt, tw), hd = r.d ? hBody(r.d, dPt, tw) : 0;
  const h = Math.max(d, hl + hd - 0.04);
  slide.addShape(pres.shapes.OVAL, { x: M, y: y, w: d, h: d, fill: { color: GOLD }, line: { color: GOLD, width: 0 } });
  slide.addText(r.n, { x: M, y: y, w: d, h: d, margin: 0, isTextBox: true, fontFace: HEAD, fontSize: 11, bold: true, color: INK, align: 'center', valign: 'middle' });
  slide.addText(r.l, { x: tx, y: y - 0.02, w: tw, h: hl, margin: 0, isTextBox: true, fontFace: BODY, fontSize: lPt, bold: true, color: dark ? PAPER : TEXT, valign: 'top' });
  if (r.d) slide.addText(r.d, { x: tx, y: y + hl - 0.06, w: tw, h: hd, margin: 0, isTextBox: true, fontFace: BODY, fontSize: dPt, color: dark ? SAND : MUTED, valign: 'top' });
  return h + 0.24;
}
function tagRow(slide, y, r, dark) {
  const dPt = 12, ht = 0.2, hd = hBody(r.d, dPt);
  slide.addText(r.t.toUpperCase(), { x: M, y, w: CW, h: ht, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 8.5, bold: true, color: dark ? GOLD : GOLD_TXT, charSpacing: 2, valign: 'top' });
  slide.addText(r.d, { x: M, y: y + ht, w: CW, h: hd, margin: 0, isTextBox: true, fontFace: BODY, fontSize: dPt, color: dark ? PAPER : TEXT, valign: 'top' });
  slide.addShape(pres.shapes.LINE, { x: M, y: y + ht + hd + 0.08, w: CW, h: 0, line: { color: dark ? INK2 : LINE, width: 0.75 } });
  return ht + hd + 0.26;
}
function groupLabel(slide, y, t, dark) {
  slide.addText(t.toUpperCase(), { x: M, y, w: CW, h: 0.22, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 8.5, bold: true, color: dark ? SAND : MUTED, charSpacing: 2, valign: 'top' });
  return 0.3;
}
function headline(slide, y, t, pt, dark, w = CW) {
  const h = hHead(t, pt, w);
  slide.addText(t, { x: M, y, w, h, margin: 0, isTextBox: true, fontFace: HEAD, fontSize: pt, bold: true, color: dark ? PAPER : INK, valign: 'top' });
  return h + 0.06;
}
function sub(slide, y, t, dark, pt = 12) {
  const h = hBody(t, pt);
  slide.addText(t, { x: M, y, w: CW, h, margin: 0, isTextBox: true, fontFace: BODY, fontSize: pt, color: dark ? SAND : MUTED, valign: 'top' });
  return h + 0.18;
}
function callout(slide, y, tag, t, dark) {
  const pad = 0.2, pt = 12, hd = hBody(t, pt, CW - 2 * pad), h = pad + 0.22 + hd + pad - 0.04;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y, w: CW, h, rectRadius: 0.08, fill: { color: dark ? GOLD : INK }, line: { color: dark ? GOLD : INK, width: 0 } });
  slide.addText(tag.toUpperCase(), { x: M + pad, y: y + pad, w: CW - 2 * pad, h: 0.2, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 8.5, bold: true, color: dark ? INK : GOLD, charSpacing: 2, valign: 'top' });
  slide.addText(t, { x: M + pad, y: y + pad + 0.22, w: CW - 2 * pad, h: hd, margin: 0, isTextBox: true, fontFace: BODY, fontSize: pt, color: dark ? INK : PAPER, valign: 'top' });
  return h + 0.14;
}
function note(slide, y, t, dark) {
  const h = hBody(t, 10.5);
  slide.addText(t, { x: M, y, w: CW, h, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 10.5, italic: true, color: dark ? SAND : MUTED, valign: 'top' });
  return h + 0.1;
}

// ---------- slide builders ----------
function content(s) {
  const slide = pres.addSlide(); const dark = !!s.dark;
  chrome(slide, dark, s.kicker);
  if (dark) ring(slide, W - 1.6, -1.2, 3.2);
  let y = 0.95;
  if (s.headline) y += headline(slide, y, s.headline, s.hpt || 24, dark);
  if (s.sub) y += sub(slide, y, s.sub, dark);
  for (const b of s.blocks || []) {
    if (b.group) y += groupLabel(slide, y, b.group, dark);
    for (const r of b.rows || []) {
      if (r.v !== undefined) y += statCard(slide, y, r, dark);
      else if (r.n !== undefined) y += numRow(slide, y, r, dark);
      else y += tagRow(slide, y, r, dark);
    }
    if (b.callout) y += callout(slide, y, b.callout.tag, b.callout.t, dark);
    if (b.note) y += note(slide, y, b.note, dark);
    if (b.text) y += sub(slide, y, b.text, dark, 12.5);
    y += 0.08;
  }
  if (y > H - 0.6) console.warn(`Slide ${n} overflows: y=${y.toFixed(2)}`);
  if (!dark && y < 7.9) ring(slide, -1.5, H - 1.7, 3.4);
  return slide;
}
function statement(s) {
  const slide = pres.addSlide(); chrome(slide, true, s.kicker);
  ring(slide, -1.4, H - 2.6, 3.6); ring(slide, W - 1.6, -1.2, 3.2);
  const pt = 26, h = hHead(s.t, pt);
  slide.addText(s.t, { x: M, y: (H - h) / 2 - 0.3, w: CW, h, margin: 0, isTextBox: true, fontFace: HEAD, fontSize: pt, bold: true, color: PAPER, valign: 'middle' });
  return slide;
}
function hero(s) {
  const slide = pres.addSlide(); chrome(slide, true, s.kicker);
  ring(slide, W - 1.6, -1.2, 3.2);
  const total = s.stats.reduce((a, r) => a + hHead(r.v, 34) + hBody(r.l, 13) + (r.d ? hBody(r.d, 11) : 0) + 0.5, 0);
  let y = (H - total) / 2 - 0.3;
  for (const r of s.stats) {
    const hv = hHead(r.v, 34), hl = hBody(r.l, 13), hd = r.d ? hBody(r.d, 11) : 0;
    slide.addShape(pres.shapes.LINE, { x: M, y, w: 0.6, h: 0, line: { color: GOLD, width: 1.5 } });
    y += 0.18;
    slide.addText(r.v, { x: M, y, w: CW, h: hv, margin: 0, isTextBox: true, fontFace: HEAD, fontSize: 34, bold: true, color: GOLD, valign: 'top' }); y += hv;
    slide.addText(r.l, { x: M, y, w: CW, h: hl, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 13, bold: true, color: PAPER, valign: 'top' }); y += hl;
    if (r.d) { slide.addText(r.d, { x: M, y, w: CW, h: hd, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 11, color: SAND, valign: 'top' }); y += hd; }
    y += 0.32;
  }
  if (s.note) note(slide, y + 0.1, s.note, true);
  return slide;
}

// ---------- 01 cover ----------
{
  const slide = pres.addSlide(); chrome(slide, true, 'Partnership proposal · September 2026', true);
  ring(slide, W - 2.2, -1.6, 4.2); ring(slide, -1.8, H - 3.4, 4.6);
  slide.addText('TWO COASTS  ×  EDWARDS AND TOWERS', { x: M, y: 1.7, w: CW, h: 0.3, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 9.5, bold: true, color: SAND, charSpacing: 3, valign: 'top' });
  let y = 2.2; y += headline(slide, y, 'Two markets.\nOne distribution advantage.', 30, true);
  y += 0.1;
  slide.addText('A verified Phuket inventory and transaction desk for Edwards and Towers’ global network.', { x: M, y, w: CW - 0.3, h: 1.0, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 13.5, color: SAND, valign: 'top' });
  slide.addShape(pres.shapes.LINE, { x: M, y: 6.55, w: 0.6, h: 0, line: { color: GOLD, width: 1.5 } });
  slide.addText([
    { text: 'Prepared by Alex Whayman for Mark Towers', options: { breakLine: true, bold: true, color: PAPER } },
    { text: 'Director, Edwards and Towers, Dubai', options: { color: SAND } },
  ], { x: M, y: 6.7, w: CW, h: 0.6, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 12, valign: 'top' });
  slide.addText('PRIVATE & CONFIDENTIAL', { x: M, y: 8.4, w: CW, h: 0.25, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 8.5, bold: true, color: GOLD, charSpacing: 2.5, valign: 'top' });
}
// ---------- 02 ----------
content({ kicker: 'The opportunity', headline: 'The partnership closes a specific market gap',
  sub: 'Edwards and Towers owns reach. Two Coasts owns verified supply and local execution.',
  blocks: [{ rows: [
    { v: '75', l: 'Verified projects', d: 'Tenure, pricing and measurement traced to source documents.' },
    { v: 'GCC + global', l: 'Distribution reach', d: 'A trusted luxury audience ready for Phuket product.' },
    { v: '5', l: 'Revenue lines', d: 'Sales, leasing and specialist investor mandates.' },
  ], callout: { tag: 'The result', t: 'A new product line for Edwards and Towers, with no Thailand-side buildout.' } }] });
// ---------- 03 ----------
content({ kicker: 'Proof of execution', headline: 'The platform already operates at scale',
  sub: 'Live inventory and comparable pricing, not a future roadmap.',
  blocks: [{ rows: [
    { v: '75', l: 'Developer projects', d: 'Across 15 Phuket areas' },
    { v: '2,001', l: 'Resale units tracked' },
    { v: '998', l: 'Direct sellers' },
    { v: '12', l: 'Developer relationships' },
  ] }] });
// ---------- 04 ----------
hero({ kicker: 'Proof of execution', stats: [{ v: '>US$400K', l: 'Commission', d: 'One agreed transaction' }] });
// ---------- 05 ----------
content({ kicker: 'Market evidence', headline: 'Phuket has depth, growth and global demand',
  sub: 'The market can support a dedicated GCC distribution lane.',
  blocks: [{ rows: [
    { v: 'THB 45bn+', l: 'H1 2025 residential sales', d: '~60% foreign buyers' },
    { v: '+34.9%', l: 'Q1 2026 condo transfer value', d: 'Highest Thai province' },
    { v: '62%', l: 'Q1 2026 pre-sale absorption', d: 'Within 90 days' },
    { v: '17.4m', l: '2025 airport passengers', d: '10m international' },
  ] }] });
// ---------- 06 ----------
statement({ kicker: 'Market evidence', t: 'Phuket now sits with Dubai and Miami among global branded-residence capitals.' });
// ---------- 07 ----------
content({ kicker: 'Strategic fit', headline: 'Phuket diversifies a Dubai-led client base',
  sub: 'A second coast adds a cycle hedge, not a substitute.',
  blocks: [{ group: 'Gulf demand in Phuket', rows: [
    { v: '~10%', l: 'Of Phuket off-plan sales', d: 'From Gulf capital in 2024, and rising' },
    { v: '+28%', l: 'Saudi arrivals to Thailand', d: '2024' },
  ] }] });
// ---------- 08 ----------
content({ kicker: 'Strategic fit', headline: 'Dubai market context',
  blocks: [{ rows: [
    { v: 'AED 917bn', l: '2025 transaction value', d: 'A mature, high-volume distribution machine' },
    { v: '–4% to –10%', l: 'Market correction', d: 'From the late-February 2026 peak' },
  ] }] });
// ---------- 09 ----------
content({ kicker: 'Operating model', headline: 'Transactions fund the data moat',
  sub: 'The platform verifies inventory; the desk monetises it.',
  blocks: [{ rows: [
    { t: 'Source', d: 'Developer files' },
    { t: 'Verify', d: 'Price · size · tenure' },
    { t: 'Distribute', d: 'Dated buyer attribution' },
    { t: 'Close', d: 'Local transaction desk' },
  ] }] });
// ---------- 10 ----------
content({ kicker: 'Operating model', headline: 'Five revenue lines',
  blocks: [{ rows: [
    { n: '01', l: 'Sales' },
    { n: '02', l: 'Long-term letting', d: '10%' },
    { n: '03', l: 'Licensed short-let', d: '20%' },
    { n: '04', l: 'Commercial mandates' },
    { n: '05', l: 'Investor-incentives desk' },
  ] }] });
// ---------- 11 ----------
content({ kicker: 'Revenue model', headline: 'Five revenue lines create multiple ways to win',
  sub: 'Start with sales; add recurring and specialist income as the channel proves itself.',
  blocks: [{ rows: [
    { n: 'A', l: 'Sales', d: 'Developer off-plan, primary and resale · immediate pipeline' },
    { n: 'B', l: 'Long-term letting', d: '10% of gross rent · recurring income' },
    { n: 'C', l: 'Licensed short-let', d: '20% of gross rent · lawful operator-led delivery' },
    { n: 'D', l: 'Commercial + incentives', d: 'Success fees · specialist investor access' },
  ], note: 'Sales proves the channel. Recurring services compound its value.' }] });
// ---------- 12 ----------
content({ kicker: 'Buyer protection', headline: 'Lawful routes protect buyer confidence',
  sub: 'Every buyer and asset is matched to a defensible structure.',
  blocks: [{ rows: [
    { n: '01', l: 'Foreign freehold condo', d: 'Title in the buyer’s name · verify the 49% project quota' },
    { n: '02', l: 'Registered 30-year lease', d: 'Fully enforceable term · price on 30 years only' },
    { n: '03', l: 'BOI-promoted company', d: '100% foreign ownership · genuine promoted activity required' },
  ], note: 'Thai counsel confirms each structure before commitment.\nSuperficies and usufruct remain case-specific.' }] });
// ---------- 13 ----------
content({ kicker: 'Large-investor desk', headline: 'BOI turns qualifying assets into investable structures',
  sub: 'For hotels, branded hospitality and wellness, not residential-for-sale.',
  blocks: [{ rows: [
    { v: '100%', l: 'Foreign ownership' },
    { v: 's.27', l: 'Potential land rights' },
    { v: '3–13 yrs', l: 'CIT exemption', d: 'By activity group' },
  ] }] });
// ---------- 14 ----------
content({ kicker: 'Large-investor desk', headline: 'Hotel entry thresholds',
  blocks: [{ rows: [
    { n: 'A', l: '100+ rooms', d: '≥ THB 2m per room' },
    { n: 'B', l: 'Fewer than 100 rooms', d: '≥ THB 500m total' },
  ] }] });
// ---------- 15 ----------
content({ kicker: 'Venture economics', headline: 'The model pays for reach and execution',
  sub: 'Distribution becomes recurring venture income.',
  blocks: [{ rows: [
    { v: 'AED 200k', l: 'Launch contribution', d: 'Paid in full on signing' },
    { v: 'AED 30k', l: 'Monthly operator pay', d: 'Venture operating cost' },
    { v: '75 / 25', l: 'Alex / Mark equity', d: '85 / 15 if support falls short' },
    { v: '50 / 50', l: 'E&T-originated deals', d: 'Dated attribution controls' },
  ] }] });
// ---------- 16 ----------
hero({ kicker: 'Venture economics', stats: [{ v: '15 closings', l: '~THB 7.2m / AED 735k', d: 'Gross commission before costs' }] });
// ---------- 17 ----------
content({ kicker: 'Office strategy', headline: 'Ground-floor access matters more than prestige',
  sub: 'A 120 sqm office must earn its premium through qualified traffic.',
  blocks: [
    { group: 'Preferred corridor', rows: [{ v: 'Boat / Porto', l: 'Ground floor · 100–150 sqm', d: 'THB 165k rent + service / month' }] },
    { group: 'Strongest fallback', rows: [{ v: 'Blue Tree', l: 'Test if access is weak or the cap is exceeded', d: 'THB 180k maximum all-in occupancy' }] },
  ] });
// ---------- 18 ----------
content({ kicker: 'Office strategy', headline: 'No lease without',
  blocks: [{ rows: [
    { n: '01', l: 'Visible signage' },
    { n: '02', l: 'Client parking' },
    { n: '03', l: 'Tested footfall' },
    { n: '04', l: 'Written proposals' },
  ] }] });
// ---------- 19 ----------
content({ kicker: 'Operating case', headline: 'The office runs at THB 618k per month',
  sub: 'Eight local staff plus a premium ground-floor location.',
  blocks: [{ rows: [
    { v: 'THB 283k', l: 'People cost', d: 'Four sales + four support' },
    { v: 'THB 165k', l: 'Occupancy target', d: 'Rent + service charges' },
    { v: 'THB 130k', l: 'Office operations', d: 'Systems · utilities · travel' },
    { v: 'THB 40k', l: 'Local activation', d: 'Office-led marketing' },
  ] }] });
// ---------- 20 ----------
hero({ kicker: 'Operating case', stats: [
  { v: 'THB 7.42m', l: 'Annual fixed cost' },
  { v: 'THB 8.547m', l: 'Fully loaded' },
] });
// ---------- 21 ----------
content({ kicker: 'Funding bridge', headline: 'AED 200k mobilises the venture, not the office',
  sub: 'The office remains gated until unit, lease and funding are approved.',
  blocks: [{ rows: [
    { v: 'AED 492k', l: 'Opening cash', d: 'Startup + three-month runway' },
    { v: 'AED 200k', l: 'Launch contribution', d: '40.7% of opening cash' },
    { v: 'AED 292k', l: 'Funding gap', d: 'Source + timing open' },
  ] }] });
// ---------- 22 ----------
hero({ kicker: 'Funding bridge', stats: [{ v: 'THB 2.71m', l: 'Startup cash', d: 'Fit-out · tech · signage' }],
  note: 'No additional office capital is implied without a separate written decision.' });
// ---------- 23 ----------
content({ kicker: 'Partnership design', headline: 'The commercial frame aligns contribution and reward',
  sub: 'Equity rewards commitment; deal income follows client source.',
  blocks: [{ rows: [
    { n: 'A', l: 'Equity · 75% Alex / 25% Mark', d: 'Moves to 85 / 15 if support is not delivered' },
    { n: 'B', l: 'E&T-originated · 50 / 50', d: 'Dated referral registration controls attribution' },
    { n: 'C', l: 'Alex-originated · 80 / 20', d: 'Independent clients remain outside exclusivity' },
    { n: 'D', l: 'Earned exclusivity', d: 'Three months at US$50k+ E&T fees · quarterly lapse test' },
  ] }] });
// ---------- 24 ----------
content({ kicker: 'First 90 days', headline: 'Start with one verified mandate, then expand',
  sub: 'A narrow first deal creates proof for the broader relationship.',
  blocks: [{ rows: [
    { n: '01', l: 'Sign + set up', d: 'Pay AED 200k · instruct Thai counsel · file the DTV and work plan' },
    { n: '02', l: 'Launch', d: 'Activate the E&T campaign with dated attribution and reporting' },
    { n: '03', l: 'Prove + scale', d: 'Review pipeline · add partner agencies and Dubai data scope' },
  ], callout: { tag: 'Day 90', t: 'Live referral channel · verified project · reporting cadence' } }] });
// ---------- 25 ----------
content({ kicker: 'Risk discipline', headline: 'Risk discipline is part of the proposition',
  sub: 'The plan is stronger when constraints remain visible.',
  blocks: [{ rows: [
    { t: 'Tenure', d: 'Only verified lawful structures enter the catalogue.' },
    { t: 'Compliance', d: 'Thai counsel confirms entity, work-permit and BOI files.' },
    { t: 'Catalogue', d: '22 data flags and 36 unsigned commission files remain visible.' },
    { t: 'Demand', d: 'Russian, European and Gulf demand carried growth.' },
    { t: 'Key person', d: 'Year one depends on Alex; the system is documented and scalable.' },
  ] }] });
// ---------- 26 ----------
statement({ kicker: 'Risk discipline', t: 'Underwrite today’s law, dated attribution and verified inventory, not launch hype.' });
// ---------- 27 ----------
{
  const slide = content({ kicker: 'Decision', dark: true, headline: 'Launch together.\nGate the office.', hpt: 28,
    sub: 'Launch Two Coasts with Edwards and Towers; release office capital only after diligence.',
    blocks: [
      { group: 'Why now', text: 'The platform is ready now; the office proceeds only when location and funding are proven.' },
      { group: 'Next working session', rows: [
        { n: '01', l: 'Walk the live catalogue and provenance ledger' },
        { n: '02', l: 'Agree attribution, economics and reporting' },
        { n: '03', l: 'Commission three written office proposals' },
        { n: '04', l: 'Confirm legal entity, funding gates and term sheet' },
      ] },
    ] });
  slide.addText('Alex Whayman · Two Coasts · September 2026', { x: M, y: H - 0.95, w: CW, h: 0.25, margin: 0, isTextBox: true, fontFace: BODY, fontSize: 10, bold: true, color: GOLD, valign: 'top' });
}

if (n !== TOTAL) throw new Error(`expected ${TOTAL} slides, built ${n}`);
pres.writeFile({ fileName: 'Two-Coasts-x-Edwards-and-Towers.pptx' }).then(f => console.log('wrote', f));
