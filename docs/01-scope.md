# 01. Scope

## MVP (must ship by Oct 29, 2026)

| ID | Capability | Feature |
|---|---|---|
| S1 | Destination intake from a name and optional website; editable list of 5–15 signature items | F01 |
| S2 | Taste profile: resolve signature items to Qloo entities and tags | F02 |
| S3 | Market scoring for 20–40 origin cities with baseline lift and confidence | F03 |
| S4 | Arrivals import (CSV) and gap analysis with a quadrant view | F04 |
| S5 | Market audience (age, gender skew) per shortlisted market | F05 |
| S6 | Campaign angle per market (Qloo tags and explanations, template + grounded LLM brief) | F06 |
| S7 | Media partners per market (podcasts, artists, films, books) | F07 |
| S8 | Budget allocator with slider | F09 |
| S9 | Market briefs and CSV export | F10 |
| S10 | Deterministic orchestration, live progress, full trace | F11 |
| S11 | Demo mode, cache and budget guard | F12 |

## Stretch (only after every MVP criterion passes)

| ID | Capability | Feature |
|---|---|---|
| X1 | Competitor positioning: compare our destination's profile with a rival destination | F08 |
| X2 | Backtest page showing the year Y−3 gap versus later growth | `15-evaluation-and-backtest.md` |
| X3 | Trending entities per market for timing (only if the endpoint is verified) | F06 |
| X4 | Second LLM provider (Gemini) documented and exercisable by env change | `05-agent-and-llm.md` |

## Out of scope

- Visitor forecasts, flight capacity, prices, visas, booking engines.
- Ad buying or campaign execution.
- Personal data of travellers; everything is aggregate.
- User accounts and teams (anonymous workspaces only).
- Running any model locally; OpenRouter or other gateways.
- More than one destination per run (users can start more runs).

## Constraints

- Qloo hackathon API: 5 requests per second, 10,000 calls per month.
- Judges must be able to test the app free and without restriction: demo mode with a stored run (F12).
- Public repo with an open-source licence file.
- Arrivals data must be the user's own upload or a public dataset whose licence allows use (see `09-data-sources.md`).

## Definition of done

All MVP criteria in `12-acceptance-criteria.md` pass, the pre-submit checklist in `14-checks.md` is complete, and the evaluation in `15-evaluation-and-backtest.md` has been run and reported honestly.
