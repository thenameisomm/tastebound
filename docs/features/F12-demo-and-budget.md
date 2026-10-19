# F12. Demo mode, cache and budget guard

**Purpose:** let judges test freely (a hackathon rule) without exhausting the Qloo allowance.

## Demo mode

1. `scripts/seed_demo.py` runs once with real keys for the demo destination with the bundled arrivals sample, a 5-market shortlist and a budget; stores everything in a read-only demo workspace; prints `DEMO_RUN_ID`.
2. `/sample` and the landing button load that run: table, quadrant, market details, briefs, trace. Label: "Stored run from <date>".
3. Visitors may move budget sliders and edit briefs locally; nothing is saved to the demo run.

## Live runs

Anyone can start a live run (no login), limited by `PUBLIC_RUNS_PER_IP_PER_DAY` per IP hash and per workspace. Live runs share the cache.

## Cache and budget

- Qloo responses cached by normalised request key for `QLOO_CACHE_TTL_HOURS` (default 7 days); cache hits create trace rows with `cache_hit = true`.
- Per-run cap `QLOO_MAX_CALLS_PER_RUN`; per-run LLM cap `LLM_MAX_CALLS_PER_RUN`.
- Monthly guard: when live calls in the last 30 days reach 80% of `QLOO_MONTHLY_CALL_LIMIT`, new live runs are refused with a friendly message pointing to the sample run.
- Hitting a cap stops the current tool, keeps partial results and shows a warning.

## Tests

Sample loads with all keys unset; limits per IP and workspace; zero live calls for an identical cached run; monthly guard; partial results on cap.

Acceptance: DMO-01 to DMO-05, QLO-06.
