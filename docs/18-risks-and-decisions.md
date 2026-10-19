# 18. Risks, Day 0 spikes and decisions

## Risks

| # | Risk | Likelihood | Impact | Mitigation | Spike |
|---|---|---|---|---|---|
| R1 | Qloo location signals don't differentiate origin markets (rankings flat or population-driven) | Medium | High | Three strategies, baseline lift, correlation check | S1, S2 |
| R2 | Coverage outside the US is thin | Medium | High | Measure per market; flag thin data; choose markets and destination with coverage | S3 |
| R3 | Destination not a Qloo entity | Medium | Medium | Strategy P/H use profile entities instead | S1 |
| R4 | Demographics with location unsupported | Medium | Medium | Show target shares without baseline; label | S4 |
| R5 | Partners per market not location-sensitive | Medium | Medium | Lift over baseline; show global if needed and say so | S5 |
| R6 | No suitable open arrivals dataset | Medium | High | Choose demo destination by data availability; labelled illustrative CSV as last resort | S7 |
| R7 | Gemma 4 Cloud tool calling unreliable | Medium | Medium | Planner variant, deterministic fallback | S6 |
| R8 | Silent 200 with ignored params | Medium | High | Guards on type, radius, tags | S1 |
| R9 | Qloo monthly allowance exhausted | Medium | High | Cache, fixtures, monthly guard, demo mode | — |
| R10 | Judges see "taste ≠ travel" | High | Medium | Present as complement; gap view; blind review/backtest; honest copy | — |
| R11 | Too much scope | High | High | Cut list; one polished demo case; no features in the last 48 h | — |
| R12 | Design file late | Medium | Medium | Backend first; UI waits on `DESIGN.md` | — |
| R13 | Supabase pooler + asyncpg | Medium | Low | `statement_cache_size=0` or direct connection | — |

## Day 0 spikes

| ID | Question | Pass condition |
|---|---|---|
| S1 | Which scoring strategy (D, P, H) works, and is the destination an entity? | One strategy returns usable results for ≥ 80% of 20 markets |
| S2 | Does taste change the answer and remove size? | Top-10 Jaccard between two destinations ≤ 0.5; Spearman with population ≤ 0.6 |
| S3 | Coverage outside the US | ≥ 60% of non-US markets usable |
| S4 | Demographics with location (with and without signal) | Known either way; record behaviour |
| S5 | Partners per market with location: do lists differ by market? | Top-10 overlap between two markets ≤ 0.6 for at least two types |
| S6 | Gemma 4 Cloud tool calling | 5 of 5 two-tool round trips succeed |
| S7 | Open arrivals dataset for the demo destination | ≥ 15 origin markets overlapping the catalogue, reuse allowed |

**Go/no-go:** S1, S2 and S3 must pass (after at most one change of destination pair). Otherwise switch to the fallback project (the TasteRoute/Stockist Scout pack).

## Decisions log (append only)

| Date | Decision | Reason |
|---|---|---|
| 2026-10-19 | Build TasteBound (tourism source-market gap finder) | Independent judge agent and own review: 14.5/20 base, ~16 with the gap angle; no 2025 rival among ~343 projects |
| 2026-10-19 | Gap view (taste vs arrivals) is the headline | Answers "taste ≠ travel" and separates from GeoTaste |
| 2026-10-19 | Turborepo + Next.js + FastAPI + Supabase | User's stack |
| 2026-10-19 | Ollama Cloud with Gemma 4 31B default; provider layer; no gateways | User requirement; portability to Gemini or others |
| 2026-10-19 | Prompt-and-validate JSON | Ollama docs: cloud models lack structured outputs |
| 2026-10-19 | Deterministic tools + guarded agent + fallback | Identical numbers regardless of LLM; reliable demo |
| 2026-10-19 | Angles' evidence and headline by template; LLM only phrases briefs under a validator | Prevents invented claims |
| 2026-10-19 | Anonymous workspaces with header token | Free unrestricted judging; cross-site deploy |
| 2026-10-19 | Fail closed on Qloo; kill switch tested | Proves the app is impossible without Qloo |
| 2026-10-19 | Scoring strategy decided in Phase 0 (D, P or H) | Qloo behaviour unverified |
| 2026-10-19 | **Strategy P chosen** (profile affinity per market, destination scoped via `filter.results.entities`) | Live spikes: destination entity is resolvable, per-market coverage 68/68, population correlation 0.026 |
| 2026-10-19 | **Lift = raw affinity difference**, not percentile difference | Verified live: percentiles of target vs baseline are rank-identical within a response, so percentile differences collapse to ~0. Raw `target_affinity − baseline_affinity` preserves the signal; taste score is the percentile of lift. `docs/04` updated by `docs/qloo-contract.md` |
| 2026-10-19 | Destination entity excluded from `signal.interests.entities` | Including it makes explainability return an empty entity list and flattens lift |
| 2026-10-19 | Demographics require a taste signal; location-only is rejected (400) | Verified live |
| 2026-10-19 | Demo run is seeded from an exported fixture and is read-only for non-demo workspaces | Free logged-out demo must not spend Qloo calls or mutate demo data |
| 2026-10-19 | SQLite locally (`aiosqlite`), Postgres/Supabase unchanged for deploy | Docker unavailable on the build machine; SQLAlchemy layer stays portable |
