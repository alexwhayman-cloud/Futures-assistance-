/**
 * Run the phuket-property-hub firewall against the L43 brochure and record.
 *
 *   node resale/check-L43.mjs [path-to-firewall.mjs]
 *
 * Defaults to the hub's own copy. The firewall is deliberately not vendored here —
 * two divergent copies is how one of them quietly stops matching a pattern the other
 * still catches.
 *
 * Exits non-zero on any failure, so it can gate a rebuild.
 */

import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));

const firewallPath =
  process.argv[2] ??
  resolve(here, "../../phuket-property-hub/build/lib/firewall.mjs");

let fw;
try {
  fw = await import(pathToFileURL(firewallPath).href);
} catch {
  console.error(`Cannot load the firewall from ${firewallPath}`);
  console.error("Pass the path to the hub's build/lib/firewall.mjs as the first argument.");
  process.exit(2);
}

const { contactFirewall, FORBIDDEN, assertNoCommissionKey, VENDOR_REF } = fw;

const html = readFileSync(resolve(here, "dist/listing-L43.html"), "utf8");
const rec = JSON.parse(readFileSync(resolve(here, "data/L43.json"), "utf8"));

let failures = 0;
const check = (name, fn) => {
  try {
    fn();
    console.log(`  PASS  ${name}`);
  } catch (err) {
    failures++;
    const detail = err.message.split("\n").join("\n        ");
    console.log(`  FAIL  ${name}\n        ${detail}`);
  }
};

console.log("Brochure — resale page rules (allowOwn: true)");
check("contactFirewall(allowOwn)", () =>
  contactFirewall(html, "listing-L43.html", { allowOwn: true }));
check("no forbidden terms", () => {
  const hits = FORBIDDEN.filter((re) => re.test(html));
  if (hits.length) throw new Error(`matched ${hits.join(", ")}`);
});

// The brochure carries Alex's own WhatsApp and email by design. Scanning without
// allowOwn must therefore fail — if it passes, the scan is not actually running.
console.log("\nControl — the same page without allowOwn must fail");
try {
  contactFirewall(html, "listing-L43.html");
  console.log("  FAIL  scan did not catch own contacts — the firewall is not live");
  failures++;
} catch (err) {
  console.log(`  PASS  caught as expected: ${err.message.split("\n")[1].trim()}`);
}

console.log("\nListing record");
check("no commission-shaped key", () => assertNoCommissionKey(rec));
check("vendorContact is null", () => {
  if (rec.listing.vendorContact !== null) throw new Error("vendorContact is set");
});
check("no vendor ref pattern in the page", () => {
  const m = html.match(new RegExp(VENDOR_REF.source, "g"));
  if (m) throw new Error(`found ${[...new Set(m)].join(", ")}`);
});

// The contact firewall has no pattern for an address, so this is its own check.
// See CLAUDE.md: published material gives the community and at most the frond.
// The desk record is allowed the exact address; the page is not.
console.log("\nAddress rule (published page)");
const ADDRESS_PATTERNS = [
  [/\bL\s?43\b/i, "the reference L43 — it encodes frond and plot"],
  [/\bPJFR[A-Z]\s?\d{2,3}\b/i, "a Palm Jumeirah unit code (ours or a comparable's)"],
  [/\bvilla\s*(?:no\.?|number|#)?\s*43\b/i, "a villa number"],
  [/\b(?:plot|unit)\s*(?:no\.?|number|#)?\s*\d+\b/i, "a plot or unit number"],
  [/\bfrond\s+[A-Z]\s*[-–,]?\s*\d+\b/i, "a frond-and-plot pair"],
  [/\b\d+\s+(?:street|st\.?|road|rd\.?|avenue|ave\.?)\b/i, "a street address"],
];

// Third-party personal data from the source registers. The owner's name is not written
// here — naming it to ban it would put it in the repo — so this catches the shapes:
// UAE phone numbers and any non-Alex email. Alex's own details are stripped first,
// exactly as contactFirewall does with allowOwn.
const PII_PATTERNS = [
  [/\b971[\s|)(-]?\d[\s\d|()-]{6,}/, "a UAE telephone number"],
  [/\b0?5\d[\s-]?\d{3}[\s-]?\d{4}\b/, "a UAE mobile number"],
  [/@emirates\.net\.ae\b/i, "an owner email address"],
];
check("no exact address in the page", () => {
  const hits = [];
  for (const [re, what] of ADDRESS_PATTERNS) {
    const m = html.match(new RegExp(re.source, "gi"));
    if (m) hits.push(`${what} → ${[...new Set(m)].join(", ")}`);
  }
  if (hits.length) throw new Error(hits.join("\n"));
});

console.log("\nThird-party personal data");
check("no owner contact details in the page", () => {
  let scan = html;
  for (const re of [/\+66[\s-]?96[\s-]?026[\s-]?0875/g, /\+?66960260875/g,
                    /alex\.whayman@gmail\.com/gi]) scan = scan.replace(re, "");
  const hits = [];
  for (const [re, what] of PII_PATTERNS) {
    const m = scan.match(new RegExp(re.source, "gi"));
    if (m) hits.push(`${what} → ${[...new Set(m)].slice(0, 3).join(", ")}`);
  }
  if (hits.length) throw new Error(hits.join("\n"));
});
check("no owner contact details in the desk record", () => {
  const raw = readFileSync(resolve(here, "data/L43.json"), "utf8");
  const hits = [];
  for (const [re, what] of PII_PATTERNS) {
    const m = raw.match(new RegExp(re.source, "gi"));
    if (m) hits.push(`${what} → ${[...new Set(m)].slice(0, 3).join(", ")}`);
  }
  if (hits.length) throw new Error(hits.join("\n"));
});

// Control: the desk record does carry the address, so the same scan must find it there.
// If it does not, the patterns have stopped matching and the check above proves nothing.
const recRaw = readFileSync(resolve(here, "data/L43.json"), "utf8");
const recHits = ADDRESS_PATTERNS.some(([re]) => re.test(recRaw));
if (recHits) {
  console.log("  PASS  control: the same scan does find the address in data/L43.json");
} else {
  console.log("  FAIL  control: the scan found no address in the desk record either —");
  console.log("        the patterns are not matching, so the page check means nothing");
  failures++;
}

const mb = Buffer.byteLength(html) / 1024 / 1024;
console.log(`\nPage budget\n  ${mb.toFixed(3)} MB against the 15 MB build limit`);
if (mb > 15) {
  console.log("  FAIL  over the build limit");
  failures++;
}

process.exit(failures ? 1 : 0);
