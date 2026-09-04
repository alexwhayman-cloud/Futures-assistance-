#!/usr/bin/env node
/**
 * TwoCoasts brand asset generator.
 *
 * Builds every logo variant (SVG + PNG), favicons, social images and the
 * brand sheet preview from a single geometry definition, so the whole kit
 * stays consistent. Wordmark text is converted to vector outlines so the
 * SVGs render identically everywhere, with no font installed.
 *
 * Usage:  node branding/tools/build.mjs
 * Needs:  Node 18+, `fontkit` (npm i fontkit) and `playwright` (global or local).
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const fontkit = require('fontkit');

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const OUT = {
  svg: path.join(ROOT, 'logo', 'svg'),
  png: path.join(ROOT, 'logo', 'png'),
  favicon: path.join(ROOT, 'logo', 'favicon'),
  social: path.join(ROOT, 'logo', 'social'),
  preview: path.join(ROOT, 'preview'),
};
for (const d of Object.values(OUT)) fs.mkdirSync(d, { recursive: true });

// ---------------------------------------------------------------------------
// Palette (single source of truth is colors/palette.json; mirrored here)
// ---------------------------------------------------------------------------
const palette = JSON.parse(fs.readFileSync(path.join(ROOT, 'colors', 'palette.json'), 'utf8'));
const C = Object.fromEntries(Object.entries(palette.colors).map(([k, v]) => [k, v.hex]));
const MARK = Object.fromEntries(Object.entries(palette.mark).map(([k, v]) => [k, v.hex]));

// ---------------------------------------------------------------------------
// Mark geometry (512 x 512 canvas)
// ---------------------------------------------------------------------------
const SIZE = 512;
const CX = 256;
const CY = 256;
const R = 248; // badge radius
const SUN = { cx: 236, cy: 214, r: 118 };
const PIN = { x: 318, top: 118, base: 302, w: 14 };
const FLAG = { h: 44, len: 66 }; // pennant from pin top pointing right

// Two coasts = two wave crests. Upper wave (Andaman), lower wave (Gulf).
const WAVE1 = 'M0 348 C70 348 118 366 176 366 C250 366 268 300 318 300 C376 300 424 346 512 336 V512 H0 Z';
const WAVE2 = 'M0 424 C80 424 118 392 198 394 C286 396 328 444 404 438 C462 434 490 412 512 408 V512 H0 Z';

function pinPath() {
  const { x, top, base, w } = PIN;
  return `M${x - w / 2} ${top} H${x + w / 2} V${base} H${x - w / 2} Z`;
}
function flagPath() {
  const { x, top, w } = PIN;
  const x0 = x + w / 2 - 1;
  return `M${x0} ${top} L${x0 + FLAG.len} ${top + FLAG.h / 2} L${x0} ${top + FLAG.h} Z`;
}

/** Hex-grid dimples. Retired: the founder asked for no golf ball in the mark. Kept for reference; not called. */
function dimples(fill, opacity) {
  const step = 32;
  const rows = [];
  for (let j = -4; j <= 4; j++) {
    const y = SUN.cy + j * step * 0.866;
    const offset = j % 2 ? step / 2 : 0;
    for (let i = -5; i <= 5; i++) {
      const x = SUN.cx + i * step + offset;
      const d = Math.hypot(x - SUN.cx, y - SUN.cy);
      if (d < SUN.r - 18) rows.push(`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="8"/>`);
    }
  }
  return `<g fill="${fill}" opacity="${opacity}">${rows.join('')}</g>`;
}

/**
 * Colour mark. `sky` may be null for a transparent badge.
 * `simple` thickens the pin for tiny favicon sizes.
 */
function markColour({ id, sky, sun, sunTop, dimple, wave1, wave2, pin, simple = false }) {
  const grad = sunTop
    ? `<linearGradient id="${id}-sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${sunTop}"/><stop offset="1" stop-color="${sun}"/></linearGradient>`
    : '';
  const sunFill = sunTop ? `url(#${id}-sun)` : sun;
  const pinW = simple ? 30 : PIN.w;
  const pinD = `M${PIN.x - pinW / 2} ${PIN.top} H${PIN.x + pinW / 2} V${PIN.base + 20} H${PIN.x - pinW / 2} Z`;
  const flagD = simple
    ? `M${PIN.x + pinW / 2 - 1} ${PIN.top} L${PIN.x + pinW / 2 + 110} ${PIN.top + 34} L${PIN.x + pinW / 2 - 1} ${PIN.top + 68} Z`
    : flagPath();
  return `
  <defs>
    ${grad}
    <clipPath id="${id}-badge"><circle cx="${CX}" cy="${CY}" r="${R}"/></clipPath>
  </defs>
  <g clip-path="url(#${id}-badge)">
    ${sky ? `<circle cx="${CX}" cy="${CY}" r="${R}" fill="${sky}"/>` : ''}
    <circle cx="${SUN.cx}" cy="${SUN.cy}" r="${SUN.r}" fill="${sunFill}"/>
    <path d="${WAVE1}" fill="${wave1}"/>
    <path d="${WAVE2}" fill="${wave2}"/>
    <path d="${pinD}" fill="${pin}"/>
    <path d="${flagD}" fill="${pin}"/>
  </g>`;
}

/**
 * Single-colour mark: solid silhouette with knocked-out gaps so it prints in
 * one ink and survives embossing, engraving and low-contrast placements.
 */
function markMono({ id, ink }) {
  const gap = 20;
  return `
  <defs>
    <clipPath id="${id}-badge"><circle cx="${CX}" cy="${CY}" r="${R - 18}"/></clipPath>
    <mask id="${id}-cut">
      <rect width="${SIZE}" height="${SIZE}" fill="#fff"/>
      <rect x="${PIN.x}" y="${PIN.top}" width="${SUN.cx + SUN.r - PIN.x}" height="${300 - PIN.top}" fill="#000"/>
      <path d="${WAVE1}" fill="none" stroke="#000" stroke-width="${gap}"/>
      <path d="${WAVE2}" fill="none" stroke="#000" stroke-width="${gap}"/>
      <path d="${pinPath()}" fill="#000" stroke="#000" stroke-width="${gap - 2}" stroke-linejoin="round"/>
      <path d="${flagPath()}" fill="#000" stroke="#000" stroke-width="${gap - 2}" stroke-linejoin="round"/>
    </mask>
  </defs>
  <circle cx="${CX}" cy="${CY}" r="${R - 7}" fill="none" stroke="${ink}" stroke-width="14"/>
  <g clip-path="url(#${id}-badge)" mask="url(#${id}-cut)" fill="${ink}">
    <circle cx="${SUN.cx}" cy="${SUN.cy}" r="${SUN.r}"/>
    <path d="${WAVE1}"/>
    <path d="${WAVE2}"/>
  </g>
  <path d="${pinPath()}" fill="${ink}"/>
  <path d="${flagPath()}" fill="${ink}"/>`;
}

// ---------------------------------------------------------------------------
// Wordmark: text -> outlines with fontkit (variable Montserrat)
// ---------------------------------------------------------------------------
const montserrat = fontkit.openSync(path.join(ROOT, 'fonts', 'Montserrat.ttf'));

/** Returns { d, width } for `text` at font-size `em` with baseline at (x, y). */
function outline(text, { wght, em, x = 0, y = 0, tracking = 0 }) {
  const font = montserrat.getVariation({ wght });
  const run = font.layout(text);
  const s = em / font.unitsPerEm;
  let penX = x;
  const parts = [];
  run.glyphs.forEach((glyph, i) => {
    const pos = run.positions[i];
    const gx = penX + pos.xOffset * s;
    const gy = y - pos.yOffset * s;
    for (const cmd of glyph.path.commands) {
      const a = cmd.args;
      const px = (v) => (gx + v * s).toFixed(2);
      const py = (v) => (gy - v * s).toFixed(2);
      switch (cmd.command) {
        case 'moveTo': parts.push(`M${px(a[0])} ${py(a[1])}`); break;
        case 'lineTo': parts.push(`L${px(a[0])} ${py(a[1])}`); break;
        case 'quadraticCurveTo': parts.push(`Q${px(a[0])} ${py(a[1])} ${px(a[2])} ${py(a[3])}`); break;
        case 'bezierCurveTo': parts.push(`C${px(a[0])} ${py(a[1])} ${px(a[2])} ${py(a[3])} ${px(a[4])} ${py(a[5])}`); break;
        case 'closePath': parts.push('Z'); break;
      }
    }
    penX += pos.xAdvance * s + tracking * em;
  });
  return { d: parts.join(''), width: penX - x };
}

/**
 * Wordmark lockup: "two" (weight 500) + "coasts" (weight 800), optional tagline.
 * Returns { svg, width, height } in local units with origin top-left.
 */
const TAGLINE = 'DUBAI · THAILAND';

function wordmark({ two, coasts, tagline, withTagline, em = 230, id = 'wm', tagScale = 0.19, tagTracking = 0.28 }) {
  const baseline = em * 0.78; // ascender room above baseline
  const t = outline('two', { wght: 500, em, x: 0, y: baseline, tracking: -0.015 });
  const c = outline('coasts', { wght: 800, em, x: t.width + em * 0.02, y: baseline, tracking: -0.02 });
  const width = t.width + em * 0.02 + c.width;
  let height = em * 1.0;
  let tag = '';
  if (withTagline) {
    const tagEm = em * tagScale;
    const tagBase = baseline + em * 0.42;
    const tg = outline(TAGLINE, { wght: 600, em: tagEm, tracking: tagTracking });
    // centre the tagline under the wordmark
    const tx = (width - tg.width) / 2;
    const tg2 = outline(TAGLINE, { wght: 600, em: tagEm, x: tx, y: tagBase, tracking: tagTracking });
    tag = `<path id="${id}-tagline" d="${tg2.d}" fill="${tagline}"/>`;
    height = tagBase + tagEm * 0.05;
  }
  const svg = `<path id="${id}-two" d="${t.d}" fill="${two}"/><path id="${id}-coasts" d="${c.d}" fill="${coasts}"/>${tag}`;
  return { svg, width, height };
}

// ---------------------------------------------------------------------------
// Assemblers
// ---------------------------------------------------------------------------
const XMLNS = 'xmlns="http://www.w3.org/2000/svg"';
const HEADER = `<!-- TwoCoasts brand asset. Generated by branding/tools/build.mjs; edit the generator, not this file. -->\n`;

function svgDoc({ w, h, body, title, bg }) {
  return `${HEADER}<svg ${XMLNS} viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-labelledby="t">
  <title id="t">${title}</title>${bg ? `\n  <rect width="${w}" height="${h}" fill="${bg}"/>` : ''}${body}
</svg>\n`;
}

const MARKS = {
  'mark-day': {
    title: 'TwoCoasts mark',
    build: (id) => markColour({ id, sky: MARK.skyDay, sun: C.gold, sunTop: C.goldLight, dimple: C.goldDeep, wave1: C.teal, wave2: C.navy, pin: C.navy }),
  },
  'mark-night': {
    title: 'TwoCoasts mark (night, for dark backgrounds)',
    build: (id) => markColour({ id, sky: MARK.skyNight, sun: C.gold, sunTop: C.goldLight, dimple: C.goldDeep, wave1: C.lagoon, wave2: C.teal, pin: C.white }),
  },
  'mark-mono-navy': { title: 'TwoCoasts mark, one colour (navy)', build: (id) => markMono({ id, ink: C.navy }) },
  'mark-mono-white': { title: 'TwoCoasts mark, one colour (white)', build: (id) => markMono({ id, ink: C.white }) },
  'mark-mono-black': { title: 'TwoCoasts mark, one colour (black)', build: (id) => markMono({ id, ink: '#000000' }) },
};

const WORDMARKS = {
  'wordmark': { two: C.navy, coasts: C.teal, tagline: C.gold },
  'wordmark-reverse': { two: C.white, coasts: C.lagoon, tagline: C.gold },
  'wordmark-mono-navy': { two: C.navy, coasts: C.navy, tagline: C.navy },
  'wordmark-mono-white': { two: C.white, coasts: C.white, tagline: C.white },
  'wordmark-mono-black': { two: '#000000', coasts: '#000000', tagline: '#000000' },
};

// Which mark pairs with which wordmark in lockups.
const LOCKUPS = [
  { name: 'logo-primary', mark: 'mark-day', word: 'wordmark' },
  { name: 'logo-primary-reverse', mark: 'mark-night', word: 'wordmark-reverse' },
  { name: 'logo-mono-navy', mark: 'mark-mono-navy', word: 'wordmark-mono-navy' },
  { name: 'logo-mono-white', mark: 'mark-mono-white', word: 'wordmark-mono-white' },
  { name: 'logo-mono-black', mark: 'mark-mono-black', word: 'wordmark-mono-black' },
];

const written = [];
function write(file, content) {
  fs.writeFileSync(file, content);
  written.push(path.relative(ROOT, file));
}

// Marks --------------------------------------------------------------------
for (const [name, m] of Object.entries(MARKS)) {
  write(path.join(OUT.svg, `twocoasts-${name}.svg`), svgDoc({ w: SIZE, h: SIZE, body: m.build(name), title: m.title }));
}

// Wordmarks ------------------------------------------------------------------
const PAD = 24;
for (const [name, col] of Object.entries(WORDMARKS)) {
  for (const withTagline of [false, true]) {
    const wm = wordmark({ ...col, withTagline, id: name });
    const w = Math.ceil(wm.width + PAD * 2);
    const h = Math.ceil(wm.height + PAD * 2);
    const body = `\n  <g transform="translate(${PAD} ${PAD})">${wm.svg}</g>`;
    const file = `twocoasts-${name}${withTagline ? '-tagline' : ''}.svg`;
    write(path.join(OUT.svg, file), svgDoc({ w, h, body, title: `TwoCoasts wordmark${withTagline ? ' with tagline' : ''}` }));
  }
}

// Horizontal lockups ------------------------------------------------------------
for (const { name, mark, word } of LOCKUPS) {
  for (const withTagline of [false, true]) {
    const col = WORDMARKS[word];
    const em = 236;
    const wm = wordmark({ ...col, withTagline, em, id: `${name}-w` });
    const gapX = 44;
    const w = Math.ceil(SIZE + gapX + wm.width + PAD * 2);
    const h = SIZE + PAD * 2;
    // vertically centre the wordmark block on the mark
    const wy = PAD + (SIZE - wm.height) / 2 + (withTagline ? 0 : em * 0.06);
    const body = `
  <g transform="translate(${PAD} ${PAD})">${MARKS[mark].build(`${name}-m`)}</g>
  <g transform="translate(${PAD + SIZE + gapX} ${wy.toFixed(1)})">${wm.svg}</g>`;
    const file = `twocoasts-${name}${withTagline ? '-tagline' : ''}.svg`;
    write(path.join(OUT.svg, file), svgDoc({ w, h, body, title: 'TwoCoasts logo' }));
  }
}

// Stacked lockups ------------------------------------------------------------
for (const { name, mark, word } of LOCKUPS) {
  for (const withTagline of [false, true]) {
    const col = WORDMARKS[word];
    const em = 150;
    const wm = wordmark({ ...col, withTagline, em, id: `${name}-s`, tagScale: 0.22, tagTracking: 0.24 });
    const markScale = 0.9;
    const markW = SIZE * markScale;
    const w = Math.ceil(Math.max(markW, wm.width) + PAD * 2);
    const gapY = 30;
    const h = Math.ceil(markW + gapY + wm.height + PAD * 2);
    const body = `
  <g transform="translate(${((w - markW) / 2).toFixed(1)} ${PAD}) scale(${markScale})">${MARKS[mark].build(`${name}-sm`)}</g>
  <g transform="translate(${((w - wm.width) / 2).toFixed(1)} ${(PAD + markW + gapY).toFixed(1)})">${wm.svg}</g>`;
    const file = `twocoasts-${name.replace('logo', 'logo-stacked')}${withTagline ? '-tagline' : ''}.svg`;
    write(path.join(OUT.svg, file), svgDoc({ w, h, body, title: 'TwoCoasts logo (stacked)' }));
  }
}

// Product lockups: wordmark | rule | product name -------------------------
const PRODUCTS = ['Futures'];
for (const product of PRODUCTS) {
  for (const [suffix, col, rule] of [['', WORDMARKS['wordmark'], C.driftwood], ['-reverse', WORDMARKS['wordmark-reverse'], '#A9B4C4']]) {
    const em = 230;
    const wm = wordmark({ ...col, withTagline: false, em, id: `prod-${product}${suffix}` });
    const baseline = em * 0.78;
    const gapX = em * 0.22;
    const ruleX = wm.width + gapX;
    const prod = outline(product, { wght: 500, em, x: ruleX + gapX, y: baseline, tracking: -0.01 });
    const capTop = baseline - em * 0.7;
    const w = Math.ceil(ruleX + gapX + prod.width + PAD * 2);
    const h = Math.ceil(wm.height + PAD * 2);
    const body = `
  <g transform="translate(${PAD} ${PAD})">${wm.svg}
    <rect x="${ruleX.toFixed(1)}" y="${capTop.toFixed(1)}" width="2" height="${(baseline - capTop).toFixed(1)}" fill="${rule}"/>
    <path d="${prod.d}" fill="${col.two}"/>
  </g>`;
    write(path.join(OUT.svg, `twocoasts-logo-product-${product.toLowerCase()}${suffix}.svg`), svgDoc({ w, h, body, title: `TwoCoasts ${product}` }));
  }
}

// App icon (rounded square, full bleed) -------------------------------------
function appIcon({ id, bg, simple }) {
  const dark = bg === C.navy;
  const inner = markColour({ id, sky: null, sun: C.gold, sunTop: C.goldLight, dimple: C.goldDeep, wave1: dark ? C.lagoon : C.teal, wave2: dark ? C.teal : C.navy, pin: dark ? C.white : C.navy, simple });
  // Scale the badge up so the waves bleed off the square edges.
  return `
  <defs><clipPath id="${id}-sq"><rect width="${SIZE}" height="${SIZE}" rx="112"/></clipPath></defs>
  <g clip-path="url(#${id}-sq)">
    <rect width="${SIZE}" height="${SIZE}" fill="${bg}"/>
    <g transform="translate(${CX} ${CY}) scale(1.12) translate(${-CX} ${-CY})">${inner}</g>
  </g>`;
}
write(path.join(OUT.svg, 'twocoasts-app-icon.svg'), svgDoc({ w: SIZE, h: SIZE, body: appIcon({ id: 'ai', bg: C.sand }), title: 'TwoCoasts app icon' }));
write(path.join(OUT.svg, 'twocoasts-app-icon-dark.svg'), svgDoc({ w: SIZE, h: SIZE, body: appIcon({ id: 'aid', bg: C.navy }), title: 'TwoCoasts app icon (dark)' }));
// Favicon source: simplified so it reads at 16 px.
write(path.join(OUT.favicon, 'favicon.svg'), svgDoc({ w: SIZE, h: SIZE, body: appIcon({ id: 'fv', bg: C.navy, simple: true }), title: 'TwoCoasts' }));

// ---------------------------------------------------------------------------
// Raster rendering with Playwright/Chromium
// ---------------------------------------------------------------------------
async function main() {
  let chromium;
  try { ({ chromium } = require('playwright')); }
  catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }
  const browser = await chromium.launch();
  const page = await browser.newPage();

  async function renderSvg(svgPath, outPath, width, height, { bg = null } = {}) {
    const svg = fs.readFileSync(svgPath, 'utf8');
    const data = 'data:image/svg+xml;base64,' + Buffer.from(svg).toString('base64');
    await page.setViewportSize({ width, height });
    await page.setContent(`<body style="margin:0;background:${bg || 'transparent'}"><img src="${data}" style="display:block;width:${width}px;height:${height}px"></body>`);
    await page.screenshot({ path: outPath, omitBackground: !bg });
    written.push(path.relative(ROOT, outPath));
  }
  function dims(svgPath) {
    const m = fs.readFileSync(svgPath, 'utf8').match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/);
    return { w: +m[1], h: +m[2] };
  }

  // Every SVG -> PNG at 1x (512 tall for logos) and 2x, plus mark at 1024.
  for (const f of fs.readdirSync(OUT.svg).filter((f) => f.endsWith('.svg'))) {
    const src = path.join(OUT.svg, f);
    const { w, h } = dims(src);
    const base = f.replace('.svg', '');
    const isMono = base.includes('mono-white') || base.includes('reverse');
    const bg = isMono ? C.navy : null; // white and reverse variants are previewed on navy
    for (const scale of [1, 2]) {
      const W = Math.round(w * scale), H = Math.round(h * scale);
      await renderSvg(src, path.join(OUT.png, `${base}@${scale}x.png`), W, H, { bg });
    }
  }
  // Mark size ladder for app stores / UI kits. At 96 px and below the
  // simplified drawing (thicker pin) is used.
  const simpleDay = svgDoc({ w: SIZE, h: SIZE, body: markColour({ id: 'sd', sky: MARK.skyDay, sun: C.gold, sunTop: C.goldLight, dimple: C.goldDeep, wave1: C.teal, wave2: C.navy, pin: C.navy, simple: true }), title: 'TwoCoasts mark (simplified)' });
  write(path.join(OUT.svg, 'twocoasts-mark-day-simple.svg'), simpleDay);
  const simpleNight = svgDoc({ w: SIZE, h: SIZE, body: markColour({ id: 'sn', sky: MARK.skyNight, sun: C.gold, sunTop: C.goldLight, dimple: C.goldDeep, wave1: C.lagoon, wave2: C.teal, pin: C.white, simple: true }), title: 'TwoCoasts mark (simplified, night)' });
  write(path.join(OUT.svg, 'twocoasts-mark-night-simple.svg'), simpleNight);
  for (const s of [32, 48, 64, 96, 128, 256, 1024, 2048]) {
    const src = s <= 96 ? 'twocoasts-mark-day-simple.svg' : 'twocoasts-mark-day.svg';
    await renderSvg(path.join(OUT.svg, src), path.join(OUT.png, `twocoasts-mark-day-${s}.png`), s, s);
  }

  // Favicons + PWA icons --------------------------------------------------
  const fav = path.join(OUT.favicon, 'favicon.svg');
  const icon = path.join(OUT.svg, 'twocoasts-app-icon-dark.svg');
  const favPngs = [];
  for (const s of [16, 32, 48]) {
    const p = path.join(OUT.favicon, `favicon-${s}.png`);
    await renderSvg(fav, p, s, s);
    favPngs.push(p);
  }
  await renderSvg(icon, path.join(OUT.favicon, 'apple-touch-icon.png'), 180, 180, { bg: C.navy });
  await renderSvg(icon, path.join(OUT.favicon, 'icon-192.png'), 192, 192);
  await renderSvg(icon, path.join(OUT.favicon, 'icon-512.png'), 512, 512);
  // Maskable icons keep the mark inside the 80% safe zone.
  const maskable = svgDoc({ w: SIZE, h: SIZE, bg: C.navy, body: `<g transform="translate(${CX} ${CY}) scale(0.72) translate(${-CX} ${-CY})">${MARKS['mark-night'].build('mk')}</g>`, title: 'TwoCoasts' });
  const maskPath = path.join(OUT.favicon, 'icon-maskable.svg');
  write(maskPath, maskable);
  await renderSvg(maskPath, path.join(OUT.favicon, 'icon-maskable-512.png'), 512, 512, { bg: C.navy });
  writeIco(favPngs, path.join(OUT.favicon, 'favicon.ico'));

  // Social images ---------------------------------------------------------
  const socials = [
    { name: 'avatar-1024', w: 1024, h: 1024, html: socialAvatar() },
    { name: 'banner-1500x500', w: 1500, h: 500, html: socialBanner(1500, 500) },
    { name: 'og-image-1200x630', w: 1200, h: 630, html: socialBanner(1200, 630) },
    { name: 'linkedin-banner-1584x396', w: 1584, h: 396, html: socialBanner(1584, 396) },
  ];
  for (const s of socials) {
    await page.setViewportSize({ width: s.w, height: s.h });
    await page.setContent(s.html);
    const out = path.join(OUT.social, `twocoasts-${s.name}.png`);
    await page.screenshot({ path: out });
    written.push(path.relative(ROOT, out));
  }

  // Brand sheet preview ---------------------------------------------------
  const sheet = path.join(OUT.preview, 'brand-sheet.html');
  if (fs.existsSync(sheet)) {
    await page.setViewportSize({ width: 1400, height: 1000 });
    await page.goto('file://' + sheet);
    await page.waitForTimeout(400);
    const out = path.join(OUT.preview, 'brand-sheet.png');
    await page.screenshot({ path: out, fullPage: true });
    written.push(path.relative(ROOT, out));
  }

  await browser.close();
  console.log(`Wrote ${written.length} files:`);
  for (const f of written) console.log('  ' + f);
}

function inlineSvg(name) {
  return fs.readFileSync(path.join(OUT.svg, name), 'utf8').replace(/<!--.*?-->\n/s, '');
}
function socialAvatar() {
  return `<body style="margin:0;width:1024px;height:1024px;background:${C.navy};display:grid;place-items:center">
  <div style="width:760px;height:760px">${inlineSvg('twocoasts-mark-night.svg').replace('width="512" height="512"', 'width="760" height="760"')}</div></body>`;
}
function socialBanner(w, h) {
  const logoH = Math.round(h * 0.42);
  return `<body style="margin:0;width:${w}px;height:${h}px;background:linear-gradient(120deg,${C.navy} 0%,#123a63 60%,${C.tealDeep} 100%);display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative">
  <svg style="position:absolute;inset:0" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
    <path d="M0 ${h * 0.9} C${w * 0.2} ${h * 0.9} ${w * 0.3} ${h * 0.8} ${w * 0.5} ${h * 0.82} S${w * 0.85} ${h * 0.96} ${w} ${h * 0.9} V${h} H0 Z" fill="${C.teal}" opacity="0.28"/>
    <path d="M0 ${h * 0.96} C${w * 0.25} ${h * 0.96} ${w * 0.35} ${h * 0.88} ${w * 0.55} ${h * 0.9} S${w * 0.9} ${h * 1.02} ${w} ${h * 0.97} V${h} H0 Z" fill="${C.lagoon}" opacity="0.22"/>
  </svg>
  <div style="position:relative;height:${logoH}px">${inlineSvg('twocoasts-logo-primary-reverse-tagline.svg').replace(/width="[\d.]+" height="[\d.]+"/, `height="${logoH}"`)}</div></body>`;
}

/** Pack PNG files into a .ico container (PNG-in-ICO is supported by all modern browsers). */
function writeIco(pngPaths, out) {
  const pngs = pngPaths.map((p) => fs.readFileSync(p));
  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0); header.writeUInt16LE(1, 2); header.writeUInt16LE(pngs.length, 4);
  const entries = [];
  let offset = 6 + 16 * pngs.length;
  pngs.forEach((buf) => {
    const size = buf.readUInt32BE(16);
    const e = Buffer.alloc(16);
    e.writeUInt8(size >= 256 ? 0 : size, 0); e.writeUInt8(size >= 256 ? 0 : size, 1);
    e.writeUInt8(0, 2); e.writeUInt8(0, 3); e.writeUInt16LE(1, 4); e.writeUInt16LE(32, 6);
    e.writeUInt32LE(buf.length, 8); e.writeUInt32LE(offset, 12);
    offset += buf.length; entries.push(e);
  });
  fs.writeFileSync(out, Buffer.concat([header, ...entries, ...pngs]));
  written.push(path.relative(ROOT, out));
}

main().catch((e) => { console.error(e); process.exit(1); });
