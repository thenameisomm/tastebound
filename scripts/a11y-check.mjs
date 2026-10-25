import { chromium } from "playwright";
import { AxeBuilder } from "@axe-core/playwright";

const BASE = process.env.WEB_URL ?? "http://localhost:3000";
const DEMO_RUN = process.env.DEMO_RUN ?? "demo-e5b2b8fd";

const pages = [
  "/",
  "/sample",
  `/runs/${DEMO_RUN}`,
  `/runs/${DEMO_RUN}/plan`,
  `/runs/${DEMO_RUN}/trace`,
  `/runs/${DEMO_RUN}/markets/co-cartagena`,
];

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
});
const page = await context.newPage();
let failed = false;

for (const path of pages) {
  await page.goto(`${BASE}${path}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const violations = results.violations;
  if (violations.length === 0) {
    console.log(`ok ${path} — 0 violations`);
  } else {
    failed = true;
    console.log(`FAIL ${path} — ${violations.length} violation(s)`);
    for (const violation of violations) {
      console.log(`  [${violation.impact}] ${violation.id}: ${violation.help}`);
      for (const node of violation.nodes.slice(0, 3)) {
        console.log(`    ${node.target.join(" ")}`);
      }
    }
  }
}

await page.goto(`${BASE}/runs/${DEMO_RUN}`, { waitUntil: "networkidle" });
await page.waitForTimeout(1200);
await page.getByRole("button", { name: "Ask TasteBound" }).click();
await page.getByRole("dialog").waitFor({ state: "visible" });
await page.waitForTimeout(700);
const assistantResults = await new AxeBuilder({ page })
  .include('[role="dialog"]')
  .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
  .analyze();
if (assistantResults.violations.length === 0) {
  console.log("ok assistant drawer — 0 violations");
} else {
  failed = true;
  console.log(
    `FAIL assistant drawer — ${assistantResults.violations.length} violation(s)`,
  );
  for (const violation of assistantResults.violations) {
    console.log(`  [${violation.impact}] ${violation.id}: ${violation.help}`);
  }
}
await page.keyboard.press("Escape");

await page.setViewportSize({ width: 360, height: 740 });
await page.goto(`${BASE}/runs/${DEMO_RUN}`, { waitUntil: "networkidle" });
await page.waitForTimeout(1500);
await page.screenshot({ path: "/tmp/tb-360-run.png", fullPage: false });
await page.goto(`${BASE}/runs/${DEMO_RUN}/markets/co-cartagena`, {
  waitUntil: "networkidle",
});
await page.waitForTimeout(1500);
await page.screenshot({ path: "/tmp/tb-360-market.png", fullPage: false });
await page.getByRole("button", { name: "Ask TasteBound" }).click();
await page.getByRole("dialog").waitFor({ state: "visible" });
await page.waitForTimeout(700);
await page.screenshot({ path: "/tmp/tb-360-assistant.png", fullPage: false });
console.log(
  "360px screenshots written to /tmp/tb-360-run.png, /tmp/tb-360-market.png, /tmp/tb-360-assistant.png",
);

await browser.close();
process.exit(failed ? 1 : 0);
