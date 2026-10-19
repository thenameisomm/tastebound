import { chromium } from "playwright";

const BASE = process.env.WEB_URL ?? "http://localhost:3000";
const DEMO_RUN = process.env.DEMO_RUN ?? "demo-e5b2b8fd";
const OUT = "assets/readme";

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});
const page = await context.newPage();

async function shot(path, file, action) {
  await page.goto(`${BASE}${path}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1800);
  if (action) await action();
  await page.screenshot({ path: `${OUT}/${file}` });
  console.log(file);
}

await shot("/", "01-landing.png");
await shot(`/runs/${DEMO_RUN}`, "02-results.png", async () => {
  await page.evaluate(() => window.scrollTo(0, 470));
  await page.waitForTimeout(600);
});
await shot(`/runs/${DEMO_RUN}/markets/co-cartagena`, "03-market.png");
await shot(`/runs/${DEMO_RUN}/plan`, "04-plan.png", async () => {
  await page.evaluate(() => window.scrollTo(0, 240));
  await page.waitForTimeout(600);
});
await shot(`/runs/${DEMO_RUN}/trace`, "05-trace.png");
await shot("/start", "06-wizard.png");

await browser.close();
console.log("done");
