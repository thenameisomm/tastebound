import { chromium } from "playwright";

const BASE = process.env.WEB_URL ?? "http://localhost:3000";
const DEMO_RUN = process.env.DEMO_RUN ?? "demo-e5b2b8fd";

const checks = [
  { path: "/", expect: ["Find the markets", "See a sample run"] },
  { path: "/sample", expect: ["Sample run", "read-only"] },
  { path: `/runs/${DEMO_RUN}`, expect: ["Gap quadrant", "Markets"] },
  { path: `/runs/${DEMO_RUN}/plan`, expect: ["Budget & briefs", "Budget split", "Briefs"] },
  { path: `/runs/${DEMO_RUN}/trace`, expect: ["Trace"] },
  { path: `/runs/${DEMO_RUN}/markets/co-cartagena`, expect: ["Taste score", "Campaign angle"] },
];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));
page.on("console", (message) => {
  if (message.type() === "error") errors.push(`console: ${message.text()}`);
});

let failed = false;
for (const check of checks) {
  await page.goto(`${BASE}${check.path}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  const body = await page.textContent("body");
  for (const text of check.expect) {
    if (!body?.includes(text)) {
      console.log(`FAIL ${check.path}: missing "${text}"`);
      failed = true;
    }
  }
  if (!failed) console.log(`ok ${check.path}`);
}

await page.goto(`${BASE}/runs/${DEMO_RUN}`, { waitUntil: "networkidle" });
await page.waitForTimeout(1500);
await page.screenshot({ path: "/tmp/tb-shot-run.png", fullPage: false });
await page.goto(`${BASE}/runs/${DEMO_RUN}/markets/co-cartagena`, { waitUntil: "networkidle" });
await page.waitForTimeout(1500);
await page.screenshot({ path: "/tmp/tb-shot-market.png", fullPage: false });

if (errors.length > 0) {
  console.log("Console/page errors:");
  for (const error of errors.slice(0, 20)) console.log("  " + error);
  failed = true;
}
await browser.close();
process.exit(failed ? 1 : 0);
