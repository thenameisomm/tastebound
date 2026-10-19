# F03. Market scoring (taste lift over baseline)

**Purpose:** score each candidate origin market by how strongly its residents over-index on the destination's taste profile, with plain popularity removed.

## Inputs

Profile entities and tags (F02); 20–40 markets from `data/markets.json` (id, city, country code, lat, lon, radius_km, region, population band).

## How it works

1. Use the strategy chosen in Phase 0 (`04-qloo-integration.md`: D destination affinity, P profile affinity, or H heatmap). The strategy is configuration (`SCORING_STRATEGY`, copied into each run's settings), not code branches scattered around.
2. For each market, run the **target** query (taste signal + market location) and the **baseline** query (no taste signal + same location), or the two heatmaps for H.
3. Apply guards (type, radius, contract). Count coverage: share of profile entities (or the destination entity) found for the market.
4. Compute percentiles, **lift**, **taste score** (0–100 percentile of lift across the run's markets) and **confidence** exactly as defined in `04-qloo-integration.md`.
5. Flag `thin_data` when coverage < 40% and `population_suspect` when the market's taste score correlates with its population band across the run beyond a threshold (shown as a run-level warning).
6. Sort by taste score; store everything with `scoring_version`.

## Storage

`market_scores` (run_id, market_id, target_pct, baseline_pct, lift, taste_score, coverage, confidence, flags, rank, source_call_ids).

## Failure handling

Qloo auth/unavailable → phase fails (fail closed). A single market failing after retries → that market `error` and excluded, with a warning. All markets empty → `no_market_data`.

## UI

Market table: rank, market, country, taste score, lift ("+0.21 vs typical"), coverage, confidence badge, arrivals share and gap (if F04), quadrant label. Filters by region and confidence. Tooltips explain each number.

## Tests

Percentile, lift and taste-score maths; confidence boundaries; a crafted fixture where lift order differs from raw target order (baseline matters); guard drops; single-market failure isolation; identical scores across LLM providers and orchestration paths; rescore from stored responses makes zero calls.

Acceptance: MKT-01 to MKT-06, QLO-01 to QLO-05.
