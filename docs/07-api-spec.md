# 07. API specification (FastAPI)

Base `/v1`, JSON, `snake_case`, problem-object errors `{type, title, status, detail, code}`. Pydantic models in `schemas.py` are the source of truth; `scripts/export_openapi.py` writes `apps/api/openapi.json`; `packages/contracts` is generated from it.

Every request sends `X-Workspace-Token` (from `POST /v1/workspaces/session`); SSE takes `?token=`. Missing or invalid → 401 `invalid_workspace`.

## Endpoints

| Method and path                                                         | Purpose                                                                       | Feature  |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------- | -------- |
| `GET /health`                                                           | `{status, db, qloo, llm: {provider, model, tools_ok}, version}`               | —        |
| `POST /v1/workspaces/session`                                           | Create or validate a workspace → `{workspace_token}`                          | —        |
| `GET /v1/markets?region=`                                               | Market catalogue and preset groups                                            | F03      |
| `POST /v1/destinations/intake`                                          | `{name, country_code, website_url?}` → proposed signature items (not saved)   | F01      |
| `POST /v1/destinations`                                                 | Save destination + confirmed items → `{destination_id}`                       | F01      |
| `GET/PATCH /v1/destinations/{id}`                                       | Read or edit                                                                  | F01      |
| `POST /v1/destinations/{id}/profile-preview`                            | Resolve items in Qloo before a run → entities, tags, unresolved               | F02      |
| `GET /v1/qloo/search?q=&type=`                                          | Manual entity search (cached, budgeted)                                       | F02      |
| `POST /v1/arrivals`                                                     | Multipart CSV + `source_note` → dataset with row errors                       | F04      |
| `GET /v1/arrivals/samples`                                              | Bundled public samples                                                        | F04      |
| `POST /v1/runs`                                                         | `{destination_id, market_ids (20–40), arrivals_dataset_id?}` → `202 {run_id}` | F11      |
| `GET /v1/runs/{id}`                                                     | Status, counters, orchestration, warnings                                     | F11      |
| `GET /v1/runs/{id}/events?token=`                                       | SSE with `Last-Event-ID` replay                                               | F11      |
| `GET /v1/runs/{id}/profile`                                             | Profile entities and tags                                                     | F02      |
| `GET /v1/runs/{id}/markets?region=&confidence=&quadrant=`               | Market table rows                                                             | F03, F04 |
| `GET /v1/runs/{id}/markets/{market_id}`                                 | Market detail: scores, audience, angle, partners, evidence                    | F05–F07  |
| `POST /v1/runs/{id}/deep-dive`                                          | `{market_ids (3–6)}` → `202`                                                  | F11      |
| `POST /v1/runs/{id}/allocation`                                         | `{total, currency, mode, locks?}` → shares                                    | F09      |
| `GET /v1/runs/{id}/briefs` / `PATCH /v1/briefs/{id}`                    | Read and edit briefs                                                          | F10      |
| `GET /v1/runs/{id}/export.csv` · `GET /v1/briefs/{id}/export.md`        | Exports                                                                       | F10      |
| `GET /v1/runs/{id}/trace?kind=qloo\|llm\|tool`                          | Ordered trace without secrets                                                 | F11      |
| `GET /v1/runs/{id}/assistant?focus_market_id=`                          | Assistant bootstrap: enabled, ready, model, suggestions, notice, limits       | F13      |
| `POST /v1/runs/{id}/assistant/conversations`                            | Create a workspace/run-scoped conversation                                    | F13      |
| `GET /v1/runs/{id}/assistant/conversations/{conversation_id}`           | Restore messages and evidence                                                 | F13      |
| `POST /v1/runs/{id}/assistant/conversations/{conversation_id}/messages` | Ask a question; returns a validated, evidence-cited answer                    | F13      |
| `POST /v1/runs/{id}/rescore`                                            | Recompute from stored responses with new thresholds (no calls)                | F03      |
| `POST /v1/runs/{id}/compare`                                            | `{rival_name, rival_country}` (stretch)                                       | F08      |
| `GET /v1/demo`                                                          | Demo run summary (no keys needed)                                             | F12      |

## Market row

```json
{
  "market_id": "gb-london",
  "city": "London",
  "country_code": "GB",
  "region": "Europe",
  "rank": 3,
  "taste_score": 81.0,
  "lift": 0.18,
  "coverage": 0.73,
  "confidence": "high",
  "arrivals_share": 0.021,
  "gap": 0.42,
  "quadrant": "untapped",
  "flags": [],
  "angle_headline": null
}
```

## Results assistant

The assistant is read-only and scoped to a completed run. The server builds the model context from stored rows on every message; clients send only question text and an optional focus market.

```json
// POST .../messages request
{"message": "Why is Cartagena first?", "focus_market_id": "co-cartagena"}

// validated response
{
  "conversation_id": "…", "message_id": "…", "model": "gemma4:31b-cloud",
  "answer": "Cartagena ranks first with a taste score of 99.26 and a gap of 98.17 points…",
  "evidence": [
    {"id": "E1", "kind": "market_score", "label": "Cartagena score",
     "detail": "rank 1 · taste 99.26 · gap 98.17 points · quadrant untapped",
     "href": "/runs/demo-e5b2b8fd/markets/co-cartagena#score", "source_call_id": "…"}
  ],
  "followups": ["What supports this score?"],
  "created_at": "2026-10-25T09:01:00Z"
}
```

- Bootstrap always returns 200; `enabled=false` with a notice when no provider is configured. A message then returns `503 assistant_unavailable`.
- Conversation and run ownership is rechecked on every request; another workspace gets 404.
- Messages are 1–800 characters. The server keeps the last 8 messages, caps context at 30,000 characters, and retains the focus market when market rows are truncated.
- Answers are 1–1800 characters and must cite 1–6 known evidence IDs. Numbers and names are validated against the context; one repair retry is allowed.
- Conversations live in process memory for 60 minutes. There is no database row, trace event or `llm_calls` record.
- `assistant_busy` (409) means a message is already in flight for that conversation.
- Rate limits: 30 messages/hour/IP and 60/hour/workspace. Creating and reading conversations is not separately rate-limited.

## SSE events

`phase_started {phase, orchestration}` · `tool_call {tool, args_summary}` · `qloo_call {call_id, endpoint, cache_hit, status, duration_ms}` · `step_done {tool, summary}` · `warning {code, message}` · `phase_done {phase, summary}` · `failed {code, message}`.

## Validation

Name ≤ 120 chars; ISO country code; URL public http(s) only; items ≤ `MAX_SIGNATURE_ITEMS`; markets 20–`MAX_MARKETS_PER_RUN` from the catalogue (fewer allowed in the sample); shortlist 3–`MAX_SHORTLIST`; CSV ≤ 500 rows and 1 MB; unknown fields rejected.

## Error codes

`invalid_workspace`, `url_not_allowed`, `website_unreadable`, `profile_too_thin`, `qloo_unconfigured`, `qloo_auth`, `qloo_unavailable`, `qloo_rate_limited`, `qloo_budget_exceeded`, `qloo_contract_violation`, `no_market_data`, `arrivals_invalid`, `llm_unavailable` (non-fatal), `rate_limited`, `validation_error`, `not_found`.

Assistant: `assistant_unavailable` (503), `assistant_timeout` (504), `assistant_rate_limited` (429), `assistant_bad_response` (502), `assistant_ungrounded` (502), `assistant_busy` (409), `conversation_not_found` (404), `assistant_not_ready` (409).

## Rate limits

Runs: `PUBLIC_RUNS_PER_IP_PER_DAY` per IP hash and workspace. Intake: 20/hour/IP. Qloo search proxy: 30/min/IP. Assistant messages: 30/hour/IP and 60/hour/workspace (in-process).
