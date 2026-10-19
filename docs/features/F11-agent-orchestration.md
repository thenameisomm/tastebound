# F11. Agent orchestration, progress and trace

**Purpose:** meet the hackathon's agentic requirement with a real tool-using agent, while guaranteeing the same correct numbers every time, and show judges every step.

## Tools

| Tool | Phase | Does | Feature |
|---|---|---|---|
| `build_profile` | scoring | Resolve items, collect tags | F02 |
| `score_markets` | scoring | Target + baseline per market, lift, confidence | F03 |
| `compute_gaps` | scoring | Join arrivals, gaps, quadrants | F04 |
| `market_audience` | deep dive | Demographics per shortlisted market | F05 |
| `market_angles` | deep dive | Angle evidence per market | F06 |
| `media_partners` | deep dive | Cross-domain partners per market | F07 |
| `write_briefs` | deep dive | Grounded briefs | F10 |
| `finish_phase` | both | Ends the phase with a short summary | — |

Intake (F01) is a single LLM call before the agent. Allocation (F09) is code.

## Loop

1. System prompt per phase states the goal, current state, tools, ordering rules and limits.
2. Ollama `/api/chat` with `tools`; the model returns `tool_calls`; each passes the **plan guard** (allowed tools per phase, required order: `build_profile` → `score_markets` → `compute_gaps`; `market_audience`/`market_angles`/`media_partners` before `write_briefs`; arguments validated; ids must belong to the run; repeated identical calls refused).
3. Tool results are compact JSON summaries (counts, top 5 names, warnings) sent back as `role: "tool"` with `tool_name`.
4. Ends at `finish_phase` or `LLM_MAX_STEPS_PER_PHASE`.
5. **Planner variant:** if native tool calls are unavailable, the model returns `{"tool": ..., "arguments": ...}` JSON per step, validated the same way.
6. **Deterministic fallback:** after two invalid steps, an LLM error, or no tool support, the fixed plan runs the same tools in order. The run records `orchestration` = `agent`, `planner` or `deterministic_fallback` with the reason.

## Events and trace

SSE events: `phase_started`, `tool_call`, `qloo_call`, `step_done`, `warning`, `phase_done`, `failed`; replay with `Last-Event-ID`. The trace page lists LLM steps (no prompt text), tool calls, Qloo calls (endpoint, params without key, cache hit, status, duration) in order.

## Tests

Guard refusals; step limit; fallback after two invalid steps; agent/planner/deterministic paths give identical scores; SSE replay; no secrets in trace.

Acceptance: AGT-01 to AGT-06, LLM-03.
