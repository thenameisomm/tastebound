# 10. Security and privacy

## Data handled

No personal data about travellers or users. Stored: destination names and items, uploaded arrivals (aggregate counts), run outputs, traces, a salted hash of client IPs for rate limiting (salt = `SESSION_SECRET`).

## Controls

| Area | Control |
|---|---|
| Secrets | Only in server env; `.env` git-ignored; never logged, traced, returned or bundled; secret scan in CI |
| Database | RLS on all tables, no policies; browser never connects to Supabase; workspace scoping on every query |
| Identity | HMAC-signed workspace token; tampered or missing → 401 |
| Website reader | SSRF guard (private, loopback, link-local, metadata ranges; every redirect), size and type limits, timeouts, robots.txt |
| Uploads | CSV only, 1 MB and 500 rows max, parsed as text, no formulas evaluated; values validated |
| Input | Pydantic validation, unknown fields rejected |
| Abuse | Rate limits on runs, intake and search; per-run and monthly Qloo caps |
| LLM | Website text treated as untrusted data; tool calls guarded so injected text cannot trigger extra calls; prompts and completions not logged in production |
| Dependencies | `pip-audit` and `pnpm audit` before submission |

## Honesty

UI and briefs always state: taste fit is not a visitor forecast; templates and inferences are labelled; arrivals sources are shown.

## Retention

See `06-data-model-supabase.md`.
