# F11. Deterministic orchestration, progress and trace

**Purpose:** make the run reproducible, keep Qloo authoritative, and show every step without claiming an LLM tool-choice loop that is not shipped.

## Execution model

The shipped executor is a fixed pipeline in `agent/executor.py`:

| Step              | Phase     | Does                                                                | Feature |
| ----------------- | --------- | ------------------------------------------------------------------- | ------- |
| `build_profile`   | scoring   | Resolve destination items, collect tags                             | F02     |
| `score_markets`   | scoring   | Target + baseline affinity per market; lift, percentile, confidence | F03     |
| `compute_gaps`    | scoring   | Join arrivals, gaps, quadrants                                      | F04     |
| `market_audience` | deep dive | Qloo demographic signal for the shortlist                           | F05     |
| `market_angles`   | deep dive | Angle evidence per market                                           | F06     |
| `media_partners`  | deep dive | Cross-domain partners per market                                    | F07     |
| `write_briefs`    | deep dive | Deterministic template briefs; optional gated model prose           | F10     |
| `finish_phase`    | both      | Records the phase summary                                           | —       |

Intake item suggestions are one LLM prompt-and-validate call before the run. Allocation is pure code. The post-run results assistant is a separate read-only surface (F13): it does not execute tools, call Qloo or write run events.

## Safety boundaries

- The model never chooses a tool and never supplies Qloo entity IDs, scores, gaps, audience figures or partner rankings.
- `agent/plan_guard.py` validates ordering, allowed steps, market ownership and repeated calls; the deterministic executor uses the same argument/data constraints.
- `LLM_TOOL_CALLING=false` in the shipped configuration. `/health` reports `tools_ok` from that switch. No planner variant or LLM tool loop is claimed.
- A model failure cannot corrupt a run: briefs fall back to templates labelled `template`.

## Events and trace

The run event stream carries phase/tool/Qloo/warning/progress events over SSE. The trace page lists Qloo calls (endpoint, parameters without keys, cache hit, status, duration) and tool steps in order. Model-written brief rows also record provider, model and prompt version when that gated path is used. Results-assistant calls are intentionally not part of the run trace and are documented in F13.

Replay uses the stored event sequence rather than re-running Qloo. The demo fixture seeds Qloo trace rows so `/trace` and the call counters agree.

## Tests

- Plan-guard ordering, unknown market, duplicate call and step-limit tests.
- Scoring and grounding tests prove Qloo numbers are computed, not narrated.
- API tests cover workspace scoping, read-only demo, kill switch and market caps.
- Browser checks cover smoke routes, trace rendering and axe accessibility.

## Acceptance

See `12-acceptance-criteria.md`. The agent-loop criteria (AGT-01..03, AGT-06) are marked deferred; the shipped implementation does not provide them.
