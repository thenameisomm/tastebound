# 11. Plan

Today: **Mon Oct 19, 2026**. Deadline: **Fri Oct 30, 11:45pm EDT (Sat Oct 31, 9:15am IST)**. Target feature-complete **Tue Oct 27**, submitted **Thu Oct 29**.

## Phases

| Phase | Dates (IST) | Goal | Gate |
|---|---|---|---|
| 0. Spikes | Oct 19–20 | Prove Qloo strategies, coverage outside the US, demographics, partners, tool calling on Gemma 4 Cloud; pick demo destination and arrivals dataset | Go/no-go in `18-risks-and-decisions.md`; `docs/qloo-contract.md`, `docs/llm-contract.md` written |
| 1. Foundations | Oct 20–21 | API scaffold, settings, Supabase migration, workspace token, Qloo client (rate limit, cache, budget, trace, guards), market catalogue | Unit + contract tests pass; `supabase db reset` works |
| 2. Scoring engine | Oct 21–22 | F02, F03, F04 as tools + deterministic plan + run lifecycle + SSE | Fixture run gives table and quadrant data; MKT, GAP, QLO criteria pass |
| 3. Agent + intake | Oct 22–23 | F01, F11 (agent loop, guard, planner, fallback), LLM provider layer | Identical scores across paths; AGT, LLM criteria pass |
| 4. Deep dive | Oct 23–24 | F05, F06, F07, F09, F10 | AUD, ANG, PAR, BUD, BRF criteria pass |
| 5. Frontend | Oct 22–26 (parallel once `DESIGN.md` arrives) | All screens, quadrant, states | UI criteria pass |
| 6. Demo + evaluation | Oct 26–27 | Seed demo run, evaluation and backtest, deploy | DMO, EVL criteria pass; demo works logged out |
| 7. Submission | Oct 28–29 | Video, README, Devpost text, final checks, run `docs/judge.md` | Pre-submit checklist complete |
| Buffer | Oct 30 | Fixes only | — |

## Phase 0 tasks (about 8 hours)

1. Scaffold `apps/api` (uv, settings, `/health`, `scripts/spike_qloo.py`).
2. **Destinations:** two contrasting demo candidates (for example Lisbon and Kyoto). Resolve 12 signature items each. Check whether the destinations exist as `destination` or `locality` entities.
3. **Strategies D, P, H** for both destinations over 20 markets in at least 3 regions. Record result counts per market (coverage), rankings, Spearman with population band, and top-10 Jaccard between the two destinations.
4. **Coverage outside the US:** share of non-US markets with usable results for each strategy.
5. **Demographics** with location and with/without signal for 3 markets.
6. **Partners:** podcasts, artists, films, books with location for 3 markets; check lift vs raw.
7. **Explainability** availability and cost.
8. **Gemma 4 Cloud tool calling** (`scripts/spike_llm_tools.py`): 5 two-tool round trips; record in `docs/llm-contract.md`.
9. **Arrivals dataset** for the demo destination meeting `09-data-sources.md`.
10. Choose strategy and demo destination; log decisions with numbers.

**Go/no-go:** go if one strategy gives (a) top-10 Jaccard between the two destinations ≤ 0.5, (b) Spearman with population band ≤ 0.6, (c) usable data for ≥ 80% of markets, including ≥ 60% of non-US markets. If not, try one more destination pair; if still failing, switch to the fallback project.

## Task list

| ID | Task | Phase | Depends on |
|---|---|---|---|
| T01 | API scaffold, settings, errors, health | 1 | — |
| T02 | Supabase migration 0001, asyncpg pool, repositories | 1 | — |
| T03 | Workspace token + scoping | 1 | T02 |
| T04 | Qloo client (rate limit, retries, cache, budget, trace, guards) | 1 | Phase 0 |
| T05 | Market catalogue load + endpoint | 1 | T02 |
| T06 | build_profile (F02) | 2 | T04 |
| T07 | score_markets + scoring module (F03) | 2 | T04, T05 |
| T08 | Arrivals upload, matching, compute_gaps (F04) | 2 | T07 |
| T09 | Deterministic plan, run lifecycle, events, SSE | 2 | T06–T08 |
| T10 | LLM provider layer, structured helper, prompts | 3 | Phase 0 |
| T11 | Intake (F01) with SSRF guard | 3 | T10 |
| T12 | Agent loop, guard, planner, fallback (F11) | 3 | T09, T10 |
| T13 | market_audience (F05) | 4 | T07 |
| T14 | market_angles (F06) | 4 | T07 |
| T15 | media_partners (F07) | 4 | T07 |
| T16 | Allocation (F09) | 4 | T08 |
| T17 | Briefs + grounding + exports (F10) | 4 | T13–T16 |
| T18 | OpenAPI export + contracts | 3 | T09 |
| T19 | Frontend wizard | 5 | T18, DESIGN.md |
| T20 | Frontend results: quadrant + table + progress | 5 | T18 |
| T21 | Frontend market detail, plan, trace, sample | 5 | T18 |
| T22 | Demo seed, limits, monthly guard (F12) | 6 | T17 |
| T23 | Evaluation + backtest scripts and report | 6 | T09 |
| T24 | Deploy (Vercel, API host, Supabase prod) | 6 | All |
| T25 | Video, README, Devpost, LICENSE, judge run | 7 | T24 |

## Cut list (in order)

1. F08 competitor positioning. 2. Trending (X3). 3. Planner variant (keep native tools + deterministic fallback). 4. Leave-one-out confidence (use coverage only). 5. Markdown export (keep CSV and print view).

Never cut: baseline lift, gap quadrant, evidence chips, kill switch, grounding validator, trace page, demo mode.
