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

const mb = Buffer.byteLength(html) / 1024 / 1024;
console.log(`\nPage budget\n  ${mb.toFixed(3)} MB against the 15 MB build limit`);
if (mb > 15) {
  console.log("  FAIL  over the build limit");
  failures++;
}

process.exit(failures ? 1 : 0);
