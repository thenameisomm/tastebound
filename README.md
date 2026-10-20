<p align="center">
  <img src="assets/readme/hero.svg" alt="TasteBound — find the markets that already share your taste. A Lisbon demo card shows Cartagena, Tokyo and Bogotá in the untapped quadrant." width="900">
</p>

<p align="center">
  <sub><strong>Qloo Agentic Hackathon 2026</strong> · Next.js · FastAPI · Supabase · Ollama Cloud · MIT</sub>
</p>

**TasteBound** finds the origin markets that already share a destination's taste but are not visiting yet. It builds a Qloo taste profile, scores every origin market by **taste lift over a popularity baseline**, subtracts **your visitor arrivals**, and turns the gap into audiences, campaign angles, media partners, a budget split and grounded briefs.

**Taste fit, not a visitor forecast.** Qloo decides; the LLM narrates. Scores, gaps, audiences, angle evidence and partners are pure functions over Qloo responses. The LLM only proposes item names and writes prose that passes a grounding validator, and every fallback is labelled.

<p align="center">
  <a href="#quickstart"><strong>Run the local sample</strong></a> ·
  <a href="docs/17-judging.md">Judging notes</a> ·
  <a href="docs/16-runbook.md">Runbook</a> ·
  <a href="docs/DESIGN.md">Design system</a>
</p>

## The gap quadrant

Taste score on one axis, arrivals share on the other. **Untapped** markets sit top-left: strong taste fit, few visitors today. Click any point to open the full market brief.

**Sample run:** 68 markets scored, 12 in the untapped quadrant. Cartagena ranks #1 with a taste score of **99.26** and a **+98.2-point** arrivals gap.

<p align="center">
  <img src="assets/readme/02-results.png" alt="Gap quadrant for the Lisbon demo run. Cartagena, Tokyo and Bogotá sit in the untapped quadrant; San Diego, Austin and Los Angeles sit in core." width="900">
</p>

## What a market gives you

Taste score, lift, coverage and a plain-language confidence explainer; arrivals share, percentile and gap; a Qloo demographics audience chart; a campaign angle where each claim carries an evidence chip; partner tabs; global brands.

<p align="center">
  <img src="assets/readme/03-market.png" alt="Cartagena market brief: taste score 99.26, lift +0.0299, 100% coverage, high confidence, an arrivals gap of +98.2 points, and a Qloo audience breakdown." width="900">
</p>

## Plan the spend

Split a budget across markets with locks; each market's share is weighted by taste score, confidence and the untapped gap. Briefs are editable, labelled `template` or `model-written`, and export as Markdown. The full run exports as CSV.

<p align="center">
  <img src="assets/readme/04-plan.png" alt="Budget and briefs screen: €250,000 allocated across six markets, with Cartagena receiving 24.05% and a per-market lock control." width="900">
</p>

## Audit every call

Every run writes an ordered, timestamped trace of Qloo, tool and LLM rows, with parameters and cache status; every number links back to the Qloo calls that produced it. The stored demo is deterministic, so its 268 events are Qloo and tool calls; live runs record LLM rows when quota is available.

<p align="center">
  <img src="assets/readme/05-trace.png" alt="Trace audit log for the Lisbon demo: 252 Qloo calls, 16 tool calls, 0 LLM calls, 268 total events, with filterable rows showing build_profile and destination_search." width="900">
</p>

## How it works

1. **Profile** — name a destination and add its signature items, or let TasteBound suggest them from the official website. Each item resolves to a real Qloo entity; unresolved items are listed, not hidden.
2. **Score** — for each origin market, fetch Qloo affinity for the destination's entity and its top explainability entities, then query the same markets again **without** the destination signals to get a per-market baseline. **Lift = target affinity − baseline affinity.** The taste score is the percentile of lift across the run — a ranking, not an absolute.
3. **Gap** — match your arrivals CSV (or the bundled sample) to markets. The gap quadrant and table compare taste percentile against arrivals percentile. Population correlation is checked and flagged when the ranking may track market size.
4. **Deep dive** — build audiences, angle evidence and media partners for the shortlist, then split a budget weighted by taste score, confidence and the untapped gap.

> **Qloo decides; the LLM narrates.** Scores, gaps, audiences, angle evidence and partners are pure functions over Qloo responses. The LLM proposes item names and writes prose that passes a grounding validator.
>
> **Verify before building.** Every Qloo parameter and response field was recorded from live calls in Phase 0 (`docs/qloo-contract.md`), not guessed.
>
> **Fail closed.** Without Qloo the run fails with `qloo_unconfigured` and zero partial ranking — a tested feature, not an error path.

## Quickstart

Requires Node 24+, pnpm, Python 3.12+ and uv, plus a Qloo key for live runs.

```bash
pnpm install
(cd apps/api && uv sync)

# apps/api/.env
#   QLOO_API_KEY=...            # required for real runs
#   OLLAMA_API_KEY=...          # optional; without quota, briefs stay labelled templates

pnpm turbo dev                   # web :3000, api :8000 (SQLite, auto-migrated and seeded)
```

Open **http://localhost:3000/sample** — a stored, read-only Lisbon run that needs no keys and spends no Qloo quota. Or start a live run at `/start`.

Key-by-key setup, run and deploy instructions: [`docs/19-setup.md`](docs/19-setup.md).

```bash
(cd apps/api && uv run pytest -m "not live")   # 48 tests, no network
pnpm turbo lint check-types build
```

## Project layout

```
apps/api            FastAPI: Qloo client (rate limit, cache, budgets), scoring, arrivals, agent, HTTP API
apps/web            Next.js: landing, 4-step wizard, results, market detail, plan, trace, sample
packages/contracts  TypeScript types generated from the API's OpenAPI schema
assets/readme       README hero and screenshots
docs/               the full documentation pack (product, Qloo integration, API, tests, runbook)
scripts/            screenshot, smoke and accessibility checks (Playwright + axe)
```

## Honest by default

- "Taste fit", never "demand" or "will visit".
- Arrivals source notes are shown wherever arrivals appear; bundled samples are labelled.
- Briefs carry their source: `template` when the LLM is unavailable, `model-written` when it is.
- Thin-data markets are flagged, not dropped; coverage and confidence are always visible.
- The trace page lists every LLM step, tool call and Qloo call in order, parameters included.

## Documentation

| Start here                                                                   | Then                                                        |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------- |
| [Product brief](docs/00-product-brief.md)                                    | Problem, users, value, metrics                              |
| [Qloo integration](docs/04-qloo-integration.md)                              | Multi-call chain, strategies, baseline, budget, kill switch |
| [Agent & LLM](docs/05-agent-and-llm.md)                                      | Agent tools, Ollama Cloud, provider portability             |
| [API & frontend](docs/07-api-spec.md) · [screens](docs/08-frontend-spec.md)  | Endpoints · screens and states                              |
| [Acceptance](docs/12-acceptance-criteria.md) · [tests](docs/13-test-plan.md) | Numbered criteria · how they are tested                     |
| [Runbook](docs/16-runbook.md) · [judging](docs/17-judging.md)                | Setup, run, deploy · judging rules and demo script          |
| [Status](docs/progress.md) · [decisions](docs/18-risks-and-decisions.md)     | Live status · decisions and risks                           |

## Limits

- Taste scores rank markets **within a run**; they are percentiles of Qloo affinity lift, not calibrated demand estimates.
- Audience demographics come from Qloo and need a taste signal; they are affinity deltas, not census data.
- The bundled arrivals sample is illustrative (Statista/INE-informed), labelled as such everywhere it appears.
- Orchestration is deterministic by design: tool choice stays in code, and the LLM proposes item names and writes grounded briefs when quota is available. The Ollama Cloud tool-calling loop is spec'd behind the provider layer but disabled (`LLM_TOOL_CALLING=false`) until tool calling is verified live; `/health` reports `tools_ok` accordingly.
- The free Ollama key hit its quota during the build, so the stored demo's briefs are templates. The sample remains fully usable without keys.

## License

MIT — see [`LICENSE`](LICENSE).
