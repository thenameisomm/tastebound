# 10. Security and privacy

## Data handled

No personal data about travellers or users. Persisted: destination names and items, uploaded arrivals (aggregate counts), run outputs, traces, a salted hash of client IPs for rate limiting (salt = `SESSION_SECRET`).

Results-assistant conversations are transient process memory, scoped by workspace/run and deleted after the TTL; they are not written to the database, `llm_calls` or the run trace. Question text and answers exist only for the conversation lifetime and disappear on API restart.

## Controls

| Area           | Control                                                                                                                                                                                                                                                        |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Secrets        | Only in server env; `.env` git-ignored; never logged, traced, returned or bundled; scan before release                                                                                                                                                         |
| Database       | Browser never connects to Supabase; workspace scoping on every query. Target Postgres RLS is documented in `06-data-model-supabase.md` but is not enabled in this snapshot.                                                                                    |
| Identity       | HMAC-signed workspace token; tampered or missing → 401                                                                                                                                                                                                         |
| Website reader | SSRF guard (private, loopback, link-local, metadata ranges; every redirect), size and type limits, timeouts, robots.txt                                                                                                                                        |
| Uploads        | CSV only, 1 MB and 500 rows max, parsed as text, no formulas evaluated; values validated                                                                                                                                                                       |
| Input          | Pydantic validation, unknown fields rejected                                                                                                                                                                                                                   |
| Abuse          | Rate limits on runs, intake, search and assistant messages; per-run and monthly Qloo caps; bounded assistant history/context                                                                                                                                   |
| LLM            | Website and user text treated as untrusted data; the model cannot select tools or call Qloo; model output is validated; prompts and completions are not logged                                                                                                 |
| Assistant      | Read-only; no tools, SQL, URL fetch or run mutation; context rebuilt server-side; answer numbers/names/evidence validated; maximum message, history, context and output sizes; per-IP and per-workspace message limits; one in-flight message per conversation |
| Dependencies   | Run `pip-audit` and `pnpm audit` before a release                                                                                                                                                                                                              |

## Honesty

UI and briefs always state: taste fit is not a visitor forecast; templates and inferences are labelled; arrivals sources are shown. The assistant is described as read-only and evidence-bound; an unavailable or ungrounded answer is shown as an error, never as a fallback opinion.

## Retention

See `06-data-model-supabase.md`. Assistant conversations are not covered by that retention policy because they are never persisted; they expire after `ASSISTANT_CONVERSATION_TTL_MINUTES` (default 60) or on API restart.
