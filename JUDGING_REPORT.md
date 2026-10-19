# Judging report: TasteBound (2026-10-19)

Protocol: `docs/judge.md`. Inputs reviewed: repository at `/Users/ombadgujar/Development/TasteBound`, README, `docs/`, running local stack (API `:8020`, web `:3000`). Live demo URL and video URL were **not provided** — recorded as Stage 1 findings. Independent J5 (impact/novelty) and J6 (engineering/trust) audits were run in parallel; J1, J2, J3, J4 and J7 were run by the lead judge. No team code was modified by the judging sub-agents; fixes listed in section 9 were made by the team after the findings.

## Verdict

**Stage 1: AT RISK.** The Qloo integration, licence and working app pass; the public repo remote, deployed demo link and English video do not exist yet. The agentic criterion is met only as a deterministic tool pipeline with an LLM in the loop for item proposals and grounded briefs — not as an LLM tool-choice loop, and the copy now says so.

**Scores: C1 4/5 · C2 4/5 · C3 4/5 · C4 4/5 · Total 16/20**

**Placement estimate: credible top-3 contender if the live demo and video land as well as the local product; mid-field if the demo link is missing or the agentic story is oversold.** It is not the favourite: there is no backtest showing that gap markets convert, and the investor-style pick rewards a sharper agentic narrative.

## Stage 1 checklist

| # | Requirement | Result | Evidence |
|---|---|---|---|
| 1 | Working software integrating the Qloo API | **PASS** | Live Lisbon run (68 markets, 252 Qloo calls in fixture); live Kyoto run `f29c1697…` done with 80 live + 13 cached calls; `apps/api/src/tastebound_api/qloo/` |
| 2 | (a) agentic tool, (b) agent framework, or (c) existing-agent integration | **AT RISK (a)** | Phase executor calls guarded tools, records orchestration, falls back deterministically (`agent/executor.py:376-397`); LLM proposes items (`routes/destinations.py:128`) and writes grounded briefs (`executor.py:1215,1244`). No LLM tool-choice loop and no agent framework; `LLM_TOOL_CALLING=false`; copy corrected to match |
| 3 | Functional demo link | **FAIL (not yet)** | Local app works end to end; no deployment URL. Team action required |
| 4 | Public repo with open-source licence | **AT RISK** | `LICENSE` (MIT, Om Badgujar) present; `git remote -v` empty — repo not published |
| 5 | Text description | **PASS** | `README.md`; `docs/` pack; Devpost text skeleton in `docs/17-judging.md` |
| 6 | Demo video (English) | **FAIL (not yet)** | Script exists (`docs/17-judging.md`), corrected for honest agent claims; not recorded |
| 7 | Free, unrestricted testing for judges | **PASS locally** | No login; keyless read-only `/sample` spends no Qloo quota (`test_api.py::test_demo_is_public_and_read_only`); must be re-verified on the deployment |
| 8 | Functions as depicted | **AT RISK** | README/docs overclaims found and corrected during judging (section 9); video must follow the corrected script |
| 9 | New work / significant update in period | **PASS** | Built 2026-10-19; 15 commits |

## What Qloo wants vs what this project provides

| Qloo wants | This project provides | Evidence | Gap |
|---|---|---|---|
| Thorough, skilful Qloo use | Five capabilities in a dependent chain: entity search, tags, location-scoped profile insights, per-market target + baseline insights, demographics, cross-domain partners; 4 rps, cache, per-run/monthly budgets | `qloo/client.py`, `qloo/service.py:640-676`; trace 252 Qloo calls | Chain is a fixed plan; Qloo's recommendation surface is not used |
| Impossible without Qloo | Kill switch: no ranking without Qloo; no other source maps cross-domain taste to origin markets | `test_api.py:122-157` asserts `qloo_unconfigured`, `qloo_live==0` | None |
| Agentic | Run executor plans phases, calls guarded tools, retries, grounds and repairs briefs, records every step; LLM proposes items and writes prose | `executor.py`, `/trace`, run `orchestration` field | LLM does not choose tools — theme risk, now stated honestly |
| Complete product | Intake → profile → quadrant → deep dive → budget → briefs → exports, seven routes | Smoke 6/6 routes, 0 console errors | One polished demo destination; live deployment pending |
| Real problem, real audience | DMO marketing director choosing 3–6 origin markets; verified $1.77M median budget / 92% public; Brand USA $100M → $20M | `docs/00-product-brief.md` with source links | No proof that taste-gap markets convert |
| Non-obvious use | Destination → origin markets, taste lift vs per-market baseline, arrivals-gap quadrant | `scoring/gap.py`; Lisbon and Kyoto rankings | Taste lift over popularity also appears in a 2026 cohort entry (Transplant) |
| Genuine understanding | Destination entity excluded from interests; raw lift beats percentile differences; brands global; demographics need signals; silent-200 guard | `docs/qloo-contract.md:34-90`; `docs/18-risks-and-decisions.md` | Coverage outside the US is thinner and flagged, not solved |

## Qloo integration audit

**Inventory:** `GET /search` (destination, items), `GET /tags`, `POST /v2/insights` for profile affinity and demographics, per-market target insights and per-market baseline insights (same market, destination signals omitted), cross-domain insights for partners, brand insights (global, no location filter). Cache key is `sha256(method, path, params)` with 168 h TTL; retries only on 429/5xx/timeouts; 4 rps spacing; per-run live budget 200; monthly guard at 80% of 10,000.

**Call chain (run):** destination search → item searches → tags → profile insights (per market) → target insights (per market) → baseline insights (per market) → demographics (shortlist) → partner cross-domain calls (shortlist) → brand calls. Scores are pure functions of the stored JSON.

**Decision trace:** `/v1/runs/{id}/trace` returns Qloo, LLM and tool rows. Sample fix during judging: the demo fixture seeded no `QlooCall` rows, so the sample trace returned 0 Qloo items while counters showed 252. Seeding now reconstructs calls from the fixture's `qloo_call` events, deleted by call id on reseed; live check returned 252 Qloo + 16 tool items, and a regression test asserts it.

**Swap test:** removing Qloo is not a configuration swap — the run fails closed with `qloo_unconfigured`, zero partial ranking and no briefs. This is the strongest possible answer to "would it work without Qloo?" (verified by test and by the keyless run test).

**Kill switch:** invalid key → typed `QlooAuthError`, no retry, run `failed`; the demo script rehearses it with an invalid key and restores the real key.

**Judging budget:** the Kyoto verification run (80 live calls) was executed by the team on the team's key, not by the judging sub-agents; the sub-agents made no Qloo calls.

## Claims tested

| # | Claim | Source | Result | Evidence |
|---|---|---|---|---|
| 1 | Scores come from Qloo, not the LLM | README, docs | **VERIFIED** | `scoring/markets.py`; kill-switch test; run trace |
| 2 | Taste score is percentile of lift over a per-market popularity baseline | README:45,107 | **VERIFIED** | `scoring/markets.py:47-63,81`; baseline call in `qloo/service.py:640-676`; demo population corr 0.026 |
| 3 | Different destinations produce different rankings | README, docs | **VERIFIED live** | Kyoto/APAC-15 top five: Mumbai 96.7, Delhi 90.0, Kuala Lumpur 83.3, Sydney 76.7, Auckland 70.0; Lisbon: Cartagena 99.26, Tokyo 97.8, Kuala Lumpur 96.3, San Diego 94.9, Seattle 93.4 |
| 4 | Gap combines taste with real arrivals | README | **VERIFIED, with honesty caveat** | `scoring/gap.py`; arrival source notes shown; bundled sample is `is_illustrative: true` |
| 5 | Audiences, angles, partners per market come from location-aware Qloo calls | docs | **VERIFIED** | Audience `source_call_id`; angle evidence chips; partner rows in `market_partners`; partner lists differ by market |
| 6 | Brands are global and labelled | docs | **VERIFIED** | `qloo/service.py` brand calls without location; UI "global brands" tab |
| 7 | Briefs contain only grounded numbers/names | README | **VERIFIED (mechanical)** | `grounding.py:203-244`; repair + template fallback; semantic entailment is not checked — labelled `template`/`model-written` |
| 8 | The agent chooses tools | README (before fix), `docs/judge.md` claim 8 | **FALSE (copy corrected)** | `executor.py:376-397` always deterministic; `orchestration` records `deterministic_fallback`; `LLM_TOOL_CALLING=false`; no fake-provider run exists |
| 9 | Ollama Cloud only, no local models, provider swappable | README, docs | **VERIFIED** | `llm/provider.py`; `LLM_PROVIDER` env; no other gateway in code |
| 10 | Sample works without keys | README | **VERIFIED** | `GET /v1/demo` unauthenticated; demo tests pass with blank keys; `/sample` exercised |
| 11 | Quoted evaluation numbers are reproducible | README/video | **N/A** | No evaluation-results file or quoted results; `docs/15-evaluation-and-backtest.md` is a plan only |

## Design walkthrough

Journeys checked: landing → wizard (destination, items, profile resolution, markets + arrivals) → live run with SSE progress and Qloo counter → results (quadrant, table, shortlist, deep dive, CSV) → market detail (score, gap, audience, angle evidence, partners) → plan (budget, locks, editable briefs, Markdown/CSV export) → trace. States implemented: loading, live, partial, failed, no arrivals, thin data, empty filters, reconnect, 404, demo read-only.

Screenshots: `assets/readme/01-landing.png` … `06-wizard.png`. Verification: `scripts/smoke-web.mjs` (6/6 routes, 0 console errors), `scripts/a11y-check.mjs` (axe: 0 violations), Lighthouse accessibility **100** on results and market detail; 360 px layout verified (table becomes cards, quadrant scrolls). Lighthouse performance 48 was measured against the dev server and is not representative of production.

Weaknesses: only one polished demo destination in-app (Lisbon); the Kyoto run was verified via API, not surfaced as a second sample; no dark mode (not required); the sample's illustrative arrivals are prominent and must be explained in the video.

## Impact and idea

User: marketing director at a city/regional DMO, choosing which 3–6 origin markets get next year's budget (`docs/00-product-brief.md:20`). Problem statistics were independently checked: median budget $1,772,250 and 92% public funding (Destinations International, Mar 8, 2022); Brand USA federal matching funds $100M → $20M (Brand USA statement, Jul 3, 2025; PAX News, Jul 4, 2025). Both now carry source links in `docs/00-product-brief.md`.

Nearest projects (searched Oct 19, 2026): GeoTaste (2025 grand prize, location → business insight, https://devpost.com/software/geotaste-your-agentic-qloo-taste-business-consultant); Transplant (2026 cohort, person → neighbourhood taste lift, https://github.com/mukeshkbj/transplant); Taste Transplant (2026 cohort, taste-matched places, https://devpost.com/software/taste-transplant-pfzsda); Cross Cultura Pro (2025, personas for marketers); commercial visitor-intelligence tools Arrivalist, Zartico, Mabrian, which measure observed behaviour rather than latent taste. No project found in the 120 gallery entries reviewed that combines cross-domain taste with DMO origin-market selection and an arrivals gap.

Novelty verdict: genuinely non-obvious B2B direction with a clear differentiator (the arrivals gap), but the core statistical move (taste lift over popularity) is shared with Transplant, and the gap hypothesis is unvalidated. Idea scores 4, not 5.

## Engineering and trust

- Build: `pnpm turbo lint build check-types` — 12/12 tasks. API: ruff, mypy strict (42 files), pytest **48 passed**; a dead-proxy run also passes 48 (no network).
- Secrets: clean working tree and history (no key-prefix hits); `.env` untracked and mode 600; browser bundle contains no Qloo/Ollama strings; browser calls only the API.
- Security: HMAC workspace tokens, constant-time compare, ownership checks, demo read-only 403s; arrivals 1 MB/500 rows; items ≤ 15; website reader blocks private hosts and re-validates every redirect (new test: redirect → 127.0.0.1 is blocked); rate limits per IP/workspace. Residual: DNS-rebinding TOCTOU, in-memory rate limiter, `Retry-After` ignored, limiter per client process.
- AI grounding: item names resolved through Qloo; unresolved items listed; briefs validated for numbers/names/evidence IDs with one repair then template fallback; source labelled. Residual: semantic entailment not checked; LLM path not exercised live (quota).
- Reliability: typed errors, retries with backoff, cache, budgets, fail-closed; `LLM_TOOL_CALLING` now separates "provider configured" from "tool calling enabled", and `/health` reports it.
- Honesty fixes during judging: sample trace now matches counters; README lift formula corrected; tool-choice overclaims removed from README, docs/03 and docs/17; novelty absolutes softened and dated; 40-market cap enforced in schema and route (was documented but unused).

## Devil's advocate and answers

| Criterion | Strongest case for −1 | Lead answer |
|---|---|---|
| C1 | "Thorough" Qloo use is a fixed chain; the theme is agentic, and the LLM never chooses a tool. Transplant used the same lift move. | The chain is dependent, contract quirks were discovered live and corrected, and every call is traced, cached and budgeted; the agentic gap is real but disclosed, and C1 asks about Qloo skill foremost. Keep 4. |
| C2 | One demo destination and no deployment; judges only see a local app or screenshots. | Seven complete routes, every failure state, exports, 100 accessibility, responsive layout. Deployment is a Stage 1 item, not a product gap. Keep 4. |
| C3 | No evidence that untapped markets convert; arrivals are illustrative; budget stats prove pressure, not the solution. | Specific role, costly recurring decision, verified statistics, and a credible complement to observed-behaviour tools; the backtest is specified but unrun. Keep 4, fragile. |
| C4 | Taste lift over popularity is not unique in the 2026 cohort, and "gap" is a simple overlay. | Direction reversal plus arrivals overlay plus cross-domain partner planning is a non-obvious B2B use; the team records and reacts to Qloo's real limits. Keep 4. |

## Fix list (ranked by score gain per hour)

1. **Deploy the demo** to a public URL (Fly/Render/Vercel + API host, SQLite volume) and verify the keyless `/sample` and a live run there. Stage 1 blocker; 2–4 h.
2. **Publish the repo** to a public GitHub remote; confirm LICENSE renders and no `.env` is tracked. Stage 1 blocker; 15 min.
3. **Record the 3-minute video** using the corrected `docs/17-judging.md` script: no "agent chooses tools" claim; show the trace failure→fix story and the kill switch. Stage 1 blocker; 2–3 h.
4. **Get an Ollama Cloud key with quota, verify tool calling, then enable `LLM_TOOL_CALLING`** and only then claim LLM tool choice. Raises the theme fit (C1) and removes the biggest honesty risk; 4–8 h plus key.
5. **Run one small validation** (blind review with 3 DMO-style judges or a holdout on one market) and quote it; otherwise keep every evaluation statement as a plan. Raises C3/C4 confidence; 4–6 h.
6. **Devpost text** with the two sourced statistics, the chain diagram and the limits section; 1 h.

## Rewritten one-line pitch and 20-second video opener

**Pitch:** TasteBound shows destination marketers which origin markets already share their destination's taste but are not visiting yet — Qloo supplies the taste, their arrivals supply the gap, and every campaign angle, partner and budget line is grounded in a Qloo call.

**20-second opener:** "Every tourism board can see who already visited. None can see who would love the place but has never considered it. TasteBound builds a taste profile of your destination with Qloo, finds the origin markets that over-index on it, and subtracts your real arrivals to show the untapped ones. Here is Lisbon."

## Five highest-leverage fixes

| Fix | Criterion | Expected gain | Hours |
|---|---|---|---|
| Public deployment + keyless sample verification | Stage 1 (eligibility) | Pass/fail | 2–4 |
| Public repo remote + licence check | Stage 1 | Pass/fail | 0.25 |
| English demo video with corrected script | Stage 1 + C2 | Pass/fail + polish | 2–3 |
| Verify Ollama tool calling; enable and demonstrate the tool-choice loop honestly | C1 | +0.5 | 4–8 |
| One validation result (blind review/holdout) quoted in README and video | C3/C4 | +0.5 | 4–6 |
