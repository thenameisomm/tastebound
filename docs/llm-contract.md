# LLM contract (Ollama Cloud, provider layer)

Status: **partially verified**. The provider transport and JSON parsing are verified; live tool calling is unverified because the Ollama Cloud key hit its free usage limit during Phase 0. Everything below states exactly what is verified and what is not.

## Provider

| Fact | Value |
|---|---|
| Provider | Ollama Cloud (`https://ollama.com`), OpenAI-compatible `/v1/chat/completions` |
| Model | `gemma4:31b-cloud` (`OLLAMA_MODEL`) |
| Auth | `Authorization: Bearer <OLLAMA_API_KEY>` |
| Isolation | only `apps/api/src/tastebound_api/llm/` may name a provider; everything else uses the `LLMProvider` protocol |
| Implementations | `openai_compat.py` (Ollama Cloud), `fake.py` (tests, deterministic), `provider.py` (singleton factory) |

## Verified

- `POST /v1/chat/completions` with `messages`, `temperature`, `stream: false` returns `choices[0].message.content` and `usage`. Verified live before the quota was exhausted.
- Non-200 responses raise typed errors (`LLMUnavailable`, `LLMAuthError`, `LLMRateLimited`) with the body truncated.
- Models sometimes wrap JSON in prose or code fences. `llm/parsing.py::extract_json_object` extracts the first balanced JSON object and is covered by unit tests. All structured outputs (destination items, tool arguments) go through it.
- With no key configured, `get_provider()` returns `None`; `/health` reports `tools_ok: false`. `tools_ok` also stays `false` while `LLM_TOOL_CALLING` is disabled (the default), because the tool-choice loop is not enabled in this build. Endpoints that need the LLM degrade:
  - Destination intake returns `"The writing model is unavailable; add items manually."` and the UI falls back to manual item entry.
  - Brief writing falls back to deterministic templates (`brief.source = "template"`).

## Unverified (needs a working key)

- **Tool calling**: request shape `tools: [{type: "function", function: {name, description, parameters}}]`, `tool_choice: "auto"`, and response `choices[0].message.tool_calls[]`. The provider layer (`llm/base.py`, `llm/openai_compat.py`) already serialises and parses this shape and has unit tests; no live response has been observed.
- Multi-step agent behaviour (`LLM_MAX_STEPS_PER_PHASE`), parallel tool calls, and how the model handles our error envelopes.
- The tool-choice loop itself is not enabled: `LLM_TOOL_CALLING` stays `false` until the tool-call shape above is verified against a live key. Orchestration is deterministic and records `orchestration` on every run.
- Whether `gemma4:31b-cloud` honours `temperature` in tool mode.

Until verified, every run executes with the **deterministic fallback planner**: the same tool set runs in a fixed order and orchestration events are labelled `deterministic_fallback`. The UI shows this label honestly. A true LLM planner loop is not implemented yet; when a key is available, re-run `scripts/spike_phase0.py --llm` and update this file before building the planner.

## Grounding

- Briefs are written from a grounded payload (scores, gap, audience rows, angle evidence ids, partner rows). `grounding.py` rejects any sentence that cites an evidence id not present in the run, and any numeric claim that does not match a run value. Violations replace the brief with the template version and add a run warning.
- Prompt versions live in `llm/prompts/*.md` and are recorded per `llm_calls` row (`prompt_version`).

## Budget

- `LLM_MAX_CALLS_PER_RUN=40`, `LLM_TIMEOUT_SECONDS=90`.
- Every call writes an `llm_calls` row (provider, model, prompt_version, status, tokens).
