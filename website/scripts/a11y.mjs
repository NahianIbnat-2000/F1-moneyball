/**
 * Accessibility check: runs axe-core (WCAG 2.1 A and AA rules plus best practices) on every page at desktop and
 * phone width, against a running preview server. Exits with an error if any page has a violation.
 *
 *   npm run build && npx vite preview --port 4174 &
 *   CHROME=/path/to/chrome node scripts/a11y.mjs
 *
 * Automated checks find only part of the possible problems; keyboard and screen-reader testing by hand is still needed.
 */
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import puppeteer from "puppeteer-core";

const require = createRequire(import.meta.url);
const axe = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");
const base = (process.env.A11Y_BASE ?? "http://localhost:4174/").replace(/\/?$/, "/");
const pages = ["", "research/", "moneyball/", "lab/", "cost-cap/", "grand-prix-economy/", "data/",
  "provenance/?team=mclaren&season=2023", "methodology/", "faq/", "about/", "changelog/",
  "research/does-money-buy-speed/", "research/cost-cap-paradox/", "research/grand-prix-economy/"];

const browser = await puppeteer.launch({ executablePath: process.env.CHROME ?? "/usr/bin/google-chrome", args: ["--no-sandbox"] });
let failures = 0;
for (const width of [1280, 390]) {
  for (const p of pages) {
    const page = await browser.newPage();
    await page.setViewport({ width, height: 900 });
    await page.goto(base + p, { waitUntil: "networkidle0", timeout: 60000 });
    await new Promise((r) => setTimeout(r, 1500)); // charts render after the data load
    await page.addScriptTag({ content: axe });
    const violations = await page.evaluate(async () =>
      (await window.axe.run(document, { runOnly: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"] })).violations
        .map((v) => `[${v.impact}] ${v.id}: ${v.help} (${v.nodes.length}) e.g. ${v.nodes[0].target.join(" ")}`));
    for (const v of violations) console.log(`/${p} at ${width}px  ${v}`);
    failures += violations.length;
    await page.close();
  }
}
await browser.close();
console.log(failures ? `${failures} accessibility violation(s)` : `No accessibility violations on ${pages.length} pages at 1280px and 390px`);
process.exit(failures ? 1 : 0);
