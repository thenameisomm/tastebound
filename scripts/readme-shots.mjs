import { chromium } from "playwright";

const BASE = process.env.WEB_URL ?? "http://localhost:3000";
const DEMO_RUN = process.env.DEMO_RUN ?? "demo-e5b2b8fd";
const OUT = "assets/readme";

const browser = await chromium.launch({ args: ["--disable-gpu"] });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 1,
  reducedMotion: "reduce",
});
async function shot(path, file, prepare) {
  const page = await context.newPage();
  await page.goto(`${BASE}${path}`, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1800);
  if (prepare) {
    await prepare(page);
    await page.waitForTimeout(1500);
  }
  await page.screenshot({ path: `${OUT}/${file}`, animations: "allow" });
  console.log(file);
  await page.close();
}

await shot("/", "01-landing.png");
await shot(`/runs/${DEMO_RUN}`, "02-results.png", async (page) => {
  await page.addStyleTag({
    content:
      ".siteHeader { position: absolute !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important; }",
  });
  await page.evaluate(() => window.scrollTo(0, 380));
});
await shot(`/runs/${DEMO_RUN}/markets/co-cartagena`, "03-market.png");
await shot(`/runs/${DEMO_RUN}/plan`, "04-plan.png");
await shot(`/runs/${DEMO_RUN}/trace`, "05-trace.png");
await shot("/start", "06-wizard.png");

await browser.close();
console.log("done");
