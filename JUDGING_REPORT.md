# Judging report: TasteBound (2026-10-21)

Protocol: `docs/judge.md`. Live rules re-checked at `https://qloo.devpost.com/` and `/rules` on 2026-10-21: externally hosted demo required; demo video not required; current field 2,083 participants. No new live Qloo calls were made for this review; evidence is code, the stored fixture, the local stack, tests, and prior recorded live runs.

**This supersedes the 2026-10-19 report.** The earlier report marked Stage 1 AT RISK and marked the per-market audience claim VERIFIED. Code review shows there is no agent loop/framework, and the audience rows are one global demographic result duplicated across every market. Those findings change the verdict.

## Verdict

**Stage 1: FAIL.**

- No hosted demo URL exists. Local-only does not qualify (`docs/17-judging.md`; live Devpost page).
- The agentic requirement is not met on a strict reading. There is no agent framework, no LLM tool-choice loop, no planning loop. The run is a fixed deterministic sequence with two fixed LLM writing calls. The protocol explicitly says a single fixed LLM call is not agentic.
- Two material claims are not true as written: audiences are not per-market/location-aware, and the product copy says the tool-calling loop is "spec'd behind the provider layer" when `docs/18-risks-and-decisions.md:60` says the unreachable iterative-agent scaffolding was removed.

**Scores: C1 4.0/5 · C2 4.0/5 · C3 3.5/5 · C4 4.0/5 · Total 15.5/20.**

**Placement estimate: cannot place as submitted.** Stage 1 fails before Stage 2 scoring. If the team ships a hosted demo and a real, working agent loop, this is a credible top-3 contender, not the favourite: the Qloo chain and product are strong, but there is no validation that gap markets convert, the core lift move is shared with Transplant, and 15.5 is below the 16+ likely-winner band. No precise probability is justified.

## Stage 1 checklist

| # | Requirement | Result | Evidence |
|---|---|---|---|
| 1 | Working software integrating Qloo | **PASS** | Qloo chain in `apps/api/src/tastebound_api/qloo/`; local `/health` returns `qloo: configured`; stored live fixture; 48 tests pass |
| 2 | (a) agentic tool, (b) agent framework, or (c) existing-agent integration | **FAIL** | No framework dependency (`pyproject.toml`, `package.json`); no `agent/loop.py` (commit `9def945` removed it); `PlanGuard` used only in tests; fixed sequence `executor.py:403-425`; `_tool` is an internal method, not LLM-chosen (`executor.py:427-444`); `LLM_TOOL_CALLING=false` (`settings.py:53`); LLM only proposes item names (`destinations.py:104-149`) and writes briefs (`executor.py:1156`) |
| 3 | Hosted, fully published demo | **FAIL** | No URL in README, docs, or repo; `docs/progress.md` records "External deployment intentionally skipped"; local `:3000` is not a submission |
| 4 | Public repo with visible OSI licence | **PASS** | `https://github.com/thenameisomm/tastebound`; MIT `LICENSE`; public history |
| 5 | Text description | **PASS** | `README.md`; `docs/` pack |
| 6 | Demo video | **N/A** | Live Devpost page: videos are not required |
| 7 | Free, unrestricted testing | **PASS locally / UNKNOWN deployed** | Keyless read-only `/sample`; no login; live run needs the server Qloo key; must be re-verified on a deployment |
| 8 | Functions as depicted | **FAIL (material claim mismatch)** | Per-market audience claim is false; trace/counter claims are partly misleading; "tool-calling loop spec'd" is false |
| 9 | New work during submission period | **PASS** | Public history from 2026-10-19 onward |

## What Qloo wants vs what this project provides

| Qloo wants | This project provides | Evidence | Gap |
|---|---|---|---|
| Thorough, skilful Qloo use | Dependent chain: search, tags, per-market target + baseline insights, explainability, demographics, cross-domain partners, global brands; cache, 4 rps, budgets, fail-closed | `qloo/service.py:416-858`; `executor.py:448-1049`; trace | Audience is one global call duplicated; no evaluation; chain is fixed |
| Impossible without Qloo | No ranking without Qloo; kill switch fails closed | `test_api.py:122-157`; `docs/04-qloo-integration.md` | Strong |
| Agentic | Fixed pipeline; LLM writes item names and briefs; no tool choice | `executor.py:403-444`; `destinations.py:104-149` | Fails the theme requirement |
| Complete product | Seven routes, full states, exports, accessibility, responsive | smoke 6/6; axe 0; `apps/web` | No hosted demo; one polished destination |
| Real problem, real audience | DMO marketing director; sourced budget pressure | `docs/00-product-brief.md` | No DMO interview, pilot, or conversion evidence |
| Non-obvious use | Destination → origin markets + arrivals gap + cross-domain partners | `scoring/gap.py`; fixture | Core lift shared with Transplant; gap is an overlay |
| Genuine understanding | Baseline, coverage, brands-global handling, limits | `docs/qloo-contract.md`; UI labels | Some copy overstates what was built |

## Qloo integration audit

**Inventory:** `GET /search` for destination and items; `/v2/tags`; `POST /v2/insights` for per-market target and baseline, profile demographics, cross-domain partners, and global brands. Explainability is requested on the target call. Six capabilities in a dependent chain.

**Call chain:** destination search → item search/resolve → tags → per-market target insight → per-market baseline insight → lift/percentile score → arrivals gap → demographics → angle evidence from explainability → per-market partners → global brands → briefs.

**Decision weight:** Scores and gaps are pure functions over stored Qloo affinities (`scoring/markets.py`, `scoring/gap.py`). Angles are deterministic templates over Qloo explainability/tags. Partners are Qloo rows. Briefs are template or validated LLM prose; the LLM cannot change numbers. Audience is Qloo, but **one global demographics call is copied to every shortlisted market**.

**Audience finding (material):** `tool_market_audience` calls `service.demographics(...)` once without market coordinates, then writes the same rows for every market (`executor.py:787-826`). The fixture has 48 audience rows = 6 markets × 8 identical bands, all with source call `5eea55aa-bf53-4514-9da0-727f07c4eedb`. Cartagena, Tokyo, and Seattle show identical age/gender values. `service.demographics` supports `market_lat`/`market_lon` (`qloo/service.py:811-858`), but the executor does not pass them. This contradicts "audiences per market" and "location-aware Qloo calls."

**Source attribution finding:** Angle tag evidence takes `tag.entity_count` from the profile build but stamps it with the per-market target call id (`executor.py:828-955`). That call did not produce the tag count. The claim "every number links back to the Qloo call that produced it" is therefore only partly true.

**Swap test:** Strong. Removing Qloo fails closed with `qloo_unconfigured` and zero partial ranking; the test asserts zero live calls. This is the best possible answer to "would this work without Qloo?"

**Kill switch:** Code and API test pass. I did not run a live invalid-key run to avoid touching the team key/state.

**Verification:** Stored fixture and `docs/qloo-contract.md` record live parameters and results; 48 tests; no evaluation script/results.

**C1 score: 4.0.** The Qloo chain is deep, guarded, cached, budgeted, and traced, which is exactly the "Qloo drives most decisions through a dependent chain" anchor. It is not 4.5/5 because the audience chain is not per-market, tag evidence attribution is wrong, and there is no evaluation or live agent-tool verification.

## Claims tested

| Claim | Source | Result | Evidence |
|---|---|---|---|
| Scores come from Qloo, not the LLM | README, docs | **VERIFIED** | `scoring/markets.py`; LLM has no score path; kill-switch test |
| Taste score is percentile of lift over a per-market baseline | README §How it works | **VERIFIED** | Target vs no-interest baseline in `qloo/service.py:627-685`; raw lift in `scoring/markets.py`; fixture population corr `0.026` |
| Different destinations produce different rankings | README, docs | **VERIFIED** | Prior live Lisbon vs Kyoto/APAC-15 runs; top fives differ |
| Gap combines taste with real arrivals | README | **VERIFIED with caveat** | `scoring/gap.py`; fixture arrivals are explicitly illustrative; country split by population band |
| Audiences, angles and partners per market come from location-aware Qloo calls | README, docs, `docs/judge.md` claim 5 | **FALSE for audiences; PARTLY overall** | Audience duplicated across all 6 markets from one no-location call; partners are location-scoped; angles use per-market explainability |
| Brands are global and labelled | docs | **VERIFIED** | `global_brands` has no location filter; UI labels global |
| Briefs contain only grounded numbers/names | README | **PARTLY** | `grounding.py` is mechanical: numbers, names, evidence ids; no semantic entailment; template fallback; LLM path unexercised live |
| The agent chooses tools | README before correction, `docs/judge.md` claim 8 | **FALSE** | Fixed sequence; no tool loop; `LLM_TOOL_CALLING=false`; `PlanGuard` unused outside tests |
| Ollama Cloud, no local model, provider swappable | README, docs | **PARTLY** | Provider isolation is real; `/health` shows Ollama configured; tool calling unverified; live brief path not exercised |
| Sample works without keys | README | **VERIFIED locally** | `/sample` 200; smoke 6/6; read-only tests; hosted URL unknown |
| Evaluation numbers are quoted and reproducible | README/docs | **N/A / UNSUPPORTED** | No `docs/evaluation-results.md`; no `scripts/evaluate.py` or `backtest.py`; `docs/15` is a plan |
| Every number links back to the Qloo call that produced it | README | **PARTLY** | Audience and tag evidence source ids are misleading; cache vs live counts not distinguished in copy |
| Trace shows 252 Qloo calls, 16 tools, 0 LLM, 268 total | README alt text, UI | **PARTLY** | Trace items = 268 (252 Qloo + 16 tool); fixture counters = 152 live + 100 cached Qloo, 12 tools; `run_events` total 291, including 4 `failed` events; trace API hides non-qloo/llm/tool events |
| Tool-calling loop is "spec'd behind the provider layer" | README | **FALSE** | `docs/18:60` says the iterative-agent scaffolding was removed; no loop exists |
| "Deterministic agent tools" | Trace UI | **MISLEADING** | They are deterministic pipeline steps; no LLM chooses them |

## Design walkthrough

Automated verification passed: `48 passed`, smoke 6/6 routes, axe 0 violations on all six routes, 360 px screenshots generated. The seven-route flow (landing → wizard → results → market → plan → trace → sample) is coherent and the market screen is visually strong. The audience screen is the weak point: it presents the same global demographic bars under every market, with a note that says the baseline is not location-supported but not that the rows are identical across markets. The trace screen calls 16 internal steps "Deterministic agent tools," which invites the agentic question.

**C2 score: 4.0.** Complete, coherent, accessible product experience; deductions for the misleading audience presentation, the unhosted state, and one polished destination.

## Impact and idea

**User:** marketing director at a city/regional DMO choosing 3–6 origin markets for the next campaign budget. This is specific and costly. The budget-pressure statistics are sourced in `docs/00-product-brief.md`; the bundled arrivals are illustrative and labelled. There is no DMO interview, pilot, letter, or backtest showing that taste-gap markets convert. The closest commercial tools (Zartico, Arrivalist, Mabrian, ForwardKeys) measure observed behaviour; TasteBound is a credible complement, not a replacement.

**Novelty:** GeoTaste (2025 grand prize) analysed a location for a business; TasteBound reverses to destination → origin markets and adds an arrivals gap. Transplant (2026 cohort) already uses taste lift over popularity. The reversal and gap are non-obvious; the core statistical move is not unique. No project found in the reviewed gallery combines this exact DMO workflow.

**C3 score: 3.5.** Specific role and sourced problem, but no evidence the target user wants this or that the gap predicts anything. The illustrative arrivals and missing validation keep it below 4.0.

**C4 score: 4.0.** Creative B2B use with genuine Qloo understanding (baseline, coverage, brands-global, limits). Not 5: shared lift core, simple gap overlay, unvalidated central hypothesis.

## Engineering and trust

- Build/tests: `48 passed`; smoke 6/6; axe 0; prior `pnpm turbo lint check-types build` pass. Tests do not cover location-aware audiences or a real agent loop, because neither exists.
- Secrets: prior audit found no key-prefix hits in working tree/history; `.env` untracked; browser bundle clean. I did not re-scan secrets.
- Security/reliability: typed errors, retries, cache, budgets, SSRF guard, HMAC workspace tokens, demo read-only. Residual: in-memory rate limiter, DNS-rebinding TOCTOU, `Retry-After` ignored.
- Demo fixture quality: 291 run events include four `failed` events (`internal_error`, `Deep dive failed` twice, `AssertionError`) from a retried run. The trace API filters them out, so the "audit every call" screen hides failures. Counters say 12 tools; trace says 16. The stored fixture should be regenerated from a clean run or the retries should be shown and explained.
- Acceptance gaps: `AGT-01/02/03/06` (agent loop, step limit, fallback, identical paths), `LLM-06` (real tool-calling exchange), `EVL-01` (evaluation), `REP-04` (hosted demo) are not met. The 48 green tests do not change that.
- AI trust: grounding is mechanical and useful, but not semantic; `template`/`model-written` labels are honest. The LLM path is unexercised live.

## Devil's advocate and answers

| Criterion | Strongest case for lower | Lead answer |
|---|---|---|
| C1 | Fixed chain, no agent, global audience, no evaluation | Chain depth, baseline, guards, cache, budgets, and fail-closed justify 4.0; not 4.5+ |
| C2 | No hosted demo, one destination, misleading audience screen | Seven coherent routes, states, exports, accessibility justify 4.0; deployment is Stage 1, not design |
| C3 | No proof of demand or conversion, illustrative arrivals | Named DMO role and sourced budget pressure justify 3.5; not 4.0 |
| C4 | Transplant shares lift; gap is a simple overlay | Reversal, arrivals overlay, and cross-domain partner planning justify 4.0; not 5 |

## Fix list (ranked by score gain per hour)

1. **Ship the hosted demo.** Deploy web + API (Fly/Render/Vercel + managed Postgres or persistent SQLite), verify `/sample` logged out with no keys, then run one live flow and the invalid-key kill switch on the deployed URL. Stage 1 pass/fail; 2–4 h. Without this, nothing else matters.
2. **Build a real agent loop.** Wire the existing `ToolSpec`/`ToolCall` types, `PlanGuard`, and agent prompts into a genuine LLM tool-choice loop; record each step; test with `FakeProvider`; then verify live with Ollama Cloud. Stage 1 + C1 (+0.5); 4–8 h plus a working quota/key. Do not claim it until it runs. If quota is impossible, Stage 1 remains failed.
3. **Fix per-market audiences or stop claiming them.** Pass `market.lat`/`market.lon` to `service.demographics` per shortlisted market and store separate rows; if Qloo returns identical/unsupported data, label the chart "global profile audience, not market-specific" and remove "per market" from README/docs. C1/C2 honesty (+0.25–0.5); 1–2 h.
4. **Clean the trace and claims.** Regenerate the demo fixture from a clean run; reconcile 12 vs 16 tools; show or explain the four failed events; label 252 Qloo trace rows as 152 live + 100 cached; fix tag evidence source ids; change "agent tools" to "pipeline steps" unless the loop is real. C1/C2 trust (+0.25); 1–2 h.
5. **Run one small validation.** Add `scripts/evaluate.py` and at minimum report sensitivity (Lisbon vs Kyoto top-10 Jaccard), population correlation, and a blind review or holdout. Quote the result honestly, including if it is weak. C3 (+0.5) and C4 (+0.25); 4–6 h.

Do 1, 2, 3, and 4 first. Skip 5 only if you also remove every implied validation claim.

## Rewritten one-line pitch

TasteBound shows destination marketers which origin markets already share their destination's taste but are not visiting yet — Qloo supplies the taste, their arrivals supply the gap, and every campaign angle, partner, and budget line is grounded in a Qloo call.
