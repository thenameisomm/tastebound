# Qloo contract (verified live)

Recorded in Phase 0 with a live key against `https://hackathon.api.qloo.com`. Raw responses are replayed in tests via `respx` fixtures. If this file disagrees with live behaviour, trust live behaviour, update this file, and log the change in `docs/18-risks-and-decisions.md`.

## Auth and limits

| Fact | Verified value |
|---|---|
| Base URL | `https://hackathon.api.qloo.com` |
| Auth header | `X-Api-Key: <key>` (no bearer) |
| Rate limit | 4 req/s enforced client-side (`QLOO_RPS`); server tolerated bursts at 4/s |
| `take` | client never requests more than 10; docs claim a max of 50 |
| Location format | WKT point `POINT(lon lat)` |

## Endpoints used

### `GET /search`

- Params: `query`, `type` (e.g. `urn:entity:place`), `take`.
- Returns `results.entities[]` with `entity_id`, `name`, `type`, and per-type fields.
- Used for resolving signature items (F01/F02) and media partner candidates (F07).
- Quirk: a genre-like string ("Tram 28") can resolve to a genre entity, not a place. The resolver checks the returned `type` and rejects mismatches; unresolved items stay in the profile as text only.

### `GET /v2/insights`

- `filter.type=urn:entity:destination&filter.results.entities=<DEST_ID>` scopes the query to one destination entity.
- `signal.interests.entities=<comma-separated entity ids>` sets the taste signal. Omit entirely for the popularity baseline.
- `signal.location` accepts a WKT point, e.g. `POINT(-9.1393 38.7223)` (lon lat). One query per origin market.
- `feature.explainability=true` adds `entity.query.explainability` keyed by the signal dimension, e.g. `entity.query.explainability["signal.interests.entities"]` with `{entities: [...], weight: ...}` entries.
- Response shape: `results.entities[]`, each with `entity_id`, `query.affinity`, `query.popularity`, optional `query.explainability`.

### Demographics

- `filter.type=urn:demographics` with `signal.location` (market WKT point) and `signal.interests.entities` (first 15 profile entities).
- Affinity deltas are returned relative to a base group; absolute values are not comparable across markets.
- Location-only demographic queries (no taste signal) are rejected with 400. A taste signal is always required.

## Scoring strategy actually chosen: P (profile affinity per market)

For each origin market and each run:

1. **Target query**: `filter.type=urn:entity:destination`, `filter.results.entities=<DEST_ID>`, `signal.interests.entities=<profile entity ids>`, `feature.explainability=true`.
2. **Baseline query**: identical but with `signal.interests.entities` omitted.
3. **Lift** = `target_affinity − baseline_affinity` (raw difference).

### Critical finding: percentiles of target vs baseline are rank-identical

Within a single insights response, converting `affinity` to percentiles produces the same ordering as raw affinity. Comparing target percentile minus baseline percentile therefore collapses to ~0 for most markets and loses the signal. We use the **raw affinity difference** as lift:

- `lift(market) = target_affinity(market) − baseline_affinity(market)`
- `taste_score(market) = percentile_of(lift) × 100` across the run's markets

This deviation from `docs/04-qloo-integration.md` (which specified percentile differences) is deliberate and logged in `docs/18-risks-and-decisions.md`.

### Destination entity must be excluded from the taste signal

Including the destination's own entity id in `signal.interests.entities` makes the explainability block return an empty entity list and flattens the lift. The destination is used only in `filter.results.entities`; profile entities never include it.

### Verified numbers (Lisbon run, 68 markets, profile of 8 items)

- Lift spread: Cartagena `+0.0299` (rank 1, taste score 99.26), Tokyo `+0.0257`, Kuala Lumpur `+0.0243`, San Diego `+0.0218`, Seattle `+0.0196`, Taipei `+0.0184` … Lisbon `−0.0123` (last).
- Population correlation of lift across 68 markets: `≈ 0.026` (popularity removed successfully).
- Calls per full run: 68 markets × 2 (target + baseline) = 136, plus 8 resolves, tags, deep-dive queries; the exported demo run spent 152 live calls.

## Partners (F07)

- Insights per market with `filter.type=urn:entity:<artist|podcast|movie|book>`, `signal.interests.entities=<profile ids>`, `signal.location=<market WKT point>`, then a second query with `filter.results.entities=<candidate ids>` to read affinity for the specific candidates.
- Partner lift = `target_affinity − baseline_affinity` for the same entity in the same market.
- Brands (`filter.type=urn:entity:brand`) do not accept location; they are queried globally and shown as global brand partners, not per-market rows.

## Explainability → angles (F06)

- Shared tags between the destination entity and each market come from `query.explainability` entries and entity `tags`.
- Angle headlines are deterministic templates in `scoring/`; the LLM only narrates and cites evidence ids that exist in the run.

## Error behaviour observed

| Case | Behaviour |
|---|---|
| Missing/invalid key | 401, no body detail beyond status |
| Rate limit | 429 with `Retry-After` sometimes absent |
| Invalid parameter combinations | 400 with a short message; occasionally 200 with empty results — the client treats empty results on a non-empty filter as a contract warning |
| Unknown entity id in filter | 200 with empty `results.entities` |

## Caching and budget

- Cache key: SHA-256 of `method + path + sorted(params)` (no key material). TTL `QLOO_CACHE_TTL_HOURS` (168h default).
- Every call (live or cached) writes a `qloo_calls` trace row.
- Per-run cap `QLOO_MAX_CALLS_PER_RUN=200`; monthly guard at 80% of `QLOO_MONTHLY_CALL_LIMIT`.
- Outside `APP_ENV=test` the client fails closed when the key is missing.
