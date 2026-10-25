# F13. Results assistant

**Purpose:** let a user ask plain-language questions about a completed run without turning the product into a chatbot that invents numbers. The assistant explains the stored run, cites the same evidence the UI uses, and stays read-only.

## Scope

- In scope: questions about scores, gaps, quadrants, confidence, arrivals, audience, angles, partners, allocation, warnings and method.
- Out of scope: changing a run, starting a run, choosing tools, calling Qloo, forecasting visitors, booking, personal data, or answering from general knowledge.
- The assistant is available on results and market pages for runs with scored markets. It is not part of the deterministic run pipeline and writes no run events, Qloo calls, briefs or `llm_calls`.

## User experience

- A contextual **Ask about this market** button appears on market pages and **Ask the run** on the results header; a floating **Ask TasteBound** launcher is available throughout `/runs/*`.
- The drawer shows a short intro, suggested questions, prior messages, evidence links and up to three follow-ups.
- On market pages, the current market is sent as the focus market, so answers start there and still can use the rest of the run.
- Closing the drawer does not cancel a non-streaming request; the answer appears when the drawer is reopened. Requests show an elapsed-time counter.
- If no provider is configured, the drawer says so and leaves the results fully usable. It never shows a fabricated answer.

## Request flow

1. The browser creates a conversation scoped to the run, workspace and optional focus market.
2. The API rebuilds a bounded context from stored run data on every message; the browser never supplies scores or evidence.
3. The conversation history (last eight messages), system prompt, run context and new question go to the provider.
4. The provider returns JSON `{answer, evidence_ids, followups}`. The server strips fences, validates the shape and checks numbers, names and evidence IDs against the context.
5. Invalid output gets exactly one repair attempt. If it still fails, the API returns `assistant_ungrounded` and stores no assistant message.
6. The UI appends the user message optimistically, then commits the user/assistant pair only after a validated answer. A failure restores the question in the composer.

## Context and evidence

`assistant/context.py` builds the only facts the model may use:

- Run status, destination, scoring version, gap/arrivals notes, thresholds, warnings, method and caveat.
- Market rows in rank order: market, rank, taste score, lift, coverage, confidence, arrivals share/percentile, gap, quadrant, flags and angle headline. Display values use percentages/points, not raw fractions.
- Destination profile tags and resolved entities with evidence IDs.
- For the focus market: audience rows, angle evidence, partners by type and global brands.
- Latest allocation, if one exists.
- Up to eight warnings and a method/caveat statement.

Evidence IDs are sequential (`E1`, `E2`, …) and assigned per request. Market score evidence comes first in rank order, so the demo's rank-one Cartagena score is `E1`. Evidence links target `#score`, `#audience`, `#angle`, `#partners`, `#method`, the plan page, or a trace row via `?call=`.

The context is capped at `ASSISTANT_MAX_CONTEXT_CHARS`. If it is too large, markets are reduced in fixed steps while the focus market is always retained; the payload records `markets_omitted`.

## Validation

- Answer: 1–1800 characters, plain text.
- Evidence IDs: 1–6 known IDs from this request.
- Follow-ups: up to three, each at most 160 characters.
- Numbers must be present in the context, accounting for rounding, percent conversion and ratio conversion.
- Names must come from the context, a small safe allowlist, or known words in a cited evidence label.
- The prompt tells the model to treat run data, market names and user text as untrusted data and to ignore embedded instructions. It must not reveal the prompt, invent facts or forecast visitors.

## Storage and limits

- Conversations live in an in-memory TTL store, scoped by workspace, run and conversation ID. They are not persisted to SQLite/Postgres and are lost on API restart.
- Defaults: 60-minute TTL, 256 conversations, 8 history messages, 30 messages/hour/IP, 60 messages/hour/workspace and 800 characters per message.
- One in-flight message per conversation; a concurrent send returns `assistant_busy`.
- A rate-limit rejection returns `assistant_rate_limited` before the provider is called.
- Only user/assistant pairs with validated answers are appended. No assistant text is written to `llm_calls` or the run trace.

## API

| Method and path                                                | Purpose                                                  |
| -------------------------------------------------------------- | -------------------------------------------------------- |
| `GET /v1/runs/{run_id}/assistant?focus_market_id=`             | Bootstrap: enabled/ready/model/suggestions/notice/limits |
| `POST /v1/runs/{run_id}/assistant/conversations`               | Create a conversation; optional `focus_market_id`        |
| `GET /v1/runs/{run_id}/assistant/conversations/{id}`           | Restore a conversation                                   |
| `POST /v1/runs/{run_id}/assistant/conversations/{id}/messages` | Ask a question and return the validated answer           |

All endpoints require `X-Workspace-Token` and return 404 for another workspace's run or conversation.

Error codes: `assistant_unavailable` (503), `assistant_timeout` (504), `assistant_rate_limited` (429), `assistant_bad_response` (502), `assistant_ungrounded` (502), `assistant_busy` (409), `conversation_not_found` (404), `assistant_not_ready` (409).

## Security

- The assistant has no tools, SQL, shell, URL fetch or run mutation path.
- The server builds context; client-supplied scores/evidence are ignored.
- Model input is untrusted and bounded; model output is untrusted until validated.
- Rate limits are in-process and reset on restart; a multi-instance deployment needs a shared limiter.
- Prompt text and completions are not logged or traced. Errors may include provider status but never keys.

## Tests

- API: no provider, grounded answer, one repair, ungrounded answer leaves no partial history, workspace scoping, rate limit and blank-message validation.
- Web: contextual open, answer/evidence/follow-ups, conversation reuse, unavailable state, sessionStorage restore and failed-message rollback.
- Run `pnpm test` for both suites; browser smoke/axe checks cover the drawer when both servers are running.
