# 05. Agent and LLM (Ollama Cloud now, portable later)

## Provider and model

- **Ollama Cloud over HTTPS with an API key.** No local Ollama, ever.
- Endpoint: `POST {OLLAMA_BASE_URL}/chat/completions` with `OLLAMA_BASE_URL=https://ollama.com/v1`, header `Authorization: Bearer {OLLAMA_API_KEY}`, body `{model, messages, tools?, stream: false, temperature}`. The reply text is `choices[0].message.content`; tool calls are `choices[0].message.tool_calls[].function.{name, arguments}`; tool results go back as `{"role": "tool", "tool_call_id": "...", "content": "<string>"}`.
- Default model **Gemma 4 31B**. The Ollama library lists `gemma4:31b` and `gemma4:31b-cloud` with native function calling, 256K context and configurable thinking. Ollama's docs say API calls use names listed at `https://ollama.com/api/tags`. **Phase 0 confirms the exact name** and sets `OLLAMA_MODEL`.
- **Tool calling on the cloud model is not explicitly documented.** Phase 0 proves it (5 successful two-tool round trips) or the planner variant is used.
- **Structured outputs (`format` with a JSON schema) are documented as not supported on Ollama Cloud.** All JSON uses prompt-and-validate (below).
- Gemma's recommended sampling is temperature 1.0, top_p 0.95, top_k 64. Use `LLM_TEMPERATURE_TOOLS=0.2` for tool choice and JSON, `LLM_TEMPERATURE_WRITING=0.7` for briefs. Never send earlier turns' thinking back in history.

## Portability (Gemini or any other direct API; no OpenRouter)

```python
class LLMProvider(Protocol):
    name: str
    supports_tools: bool
    supports_native_schema: bool
    async def chat(self, messages: list[dict], *, tools: list[dict] | None = None,
                   temperature: float, max_tokens: int, timeout: float) -> LLMResult: ...
    async def aclose(self) -> None: ...

@dataclass
class LLMResult:
    content: str
    tool_calls: list[ToolCall]     # normalised: id, name, arguments (dict)
    model: str
    provider: str
    usage: dict[str, int] | None
```

| Adapter | File | Notes |
|---|---|---|
| `OllamaCloudProvider` | `llm/ollama_cloud.py` | Default |
| `GeminiProvider` | `llm/gemini.py` | Direct Google REST; map system → system instruction, tools → function declarations; native JSON schema where supported. **Verify request fields against current Google docs before coding.** |
| `OpenAICompatProvider` | `llm/openai_compat.py` | Any direct provider with an OpenAI-style `/chat/completions` (base URL + key + model) |
| `FakeProvider` | `llm/fake.py` | Scripted replies and tool calls for tests; blocked in production |

Rules: only files in `llm/` may name a provider; switching is `LLM_PROVIDER` plus that provider's env vars; prompts contain no provider-specific syntax; errors normalise to `LLMAuthError`, `LLMRateLimitError`, `LLMTimeoutError`, `LLMBadResponseError`.

## Where the LLM is used

| Use | Mode | Can change numbers? |
|---|---|---|
| Signature item names (F01) | One structured call | No: Qloo resolves or drops |
| Agent tool choice (F11) | Tool loop with guard | No: tools are deterministic |
| Market briefs (F10) | One structured call per market, validated | No: grounding validator |
| Rival items (F08, stretch) | One structured call | No |

## Tool schemas (simplified)

```json
[
 {"type":"function","function":{"name":"build_profile","description":"Resolve the destination's signature items to Qloo entities and collect profile tags.","parameters":{"type":"object","properties":{"item_ids":{"type":"array","items":{"type":"string"}}},"required":["item_ids"]}}},
 {"type":"function","function":{"name":"score_markets","description":"Score candidate origin markets by taste lift over a popularity baseline.","parameters":{"type":"object","properties":{"market_ids":{"type":"array","items":{"type":"string"}}},"required":["market_ids"]}}},
 {"type":"function","function":{"name":"compute_gaps","description":"Join arrivals data and compute gaps and quadrants.","parameters":{"type":"object","properties":{"arrivals_dataset_id":{"type":["string","null"]}},"required":[]}}},
 {"type":"function","function":{"name":"market_audience","description":"Get audience demographics for shortlisted markets.","parameters":{"type":"object","properties":{"market_ids":{"type":"array","items":{"type":"string"}}},"required":["market_ids"]}}},
 {"type":"function","function":{"name":"market_angles","description":"Build campaign angle evidence for shortlisted markets.","parameters":{"type":"object","properties":{"market_ids":{"type":"array","items":{"type":"string"}}},"required":["market_ids"]}}},
 {"type":"function","function":{"name":"media_partners","description":"Find podcasts, artists, films and books the market's matching audience over-indexes on.","parameters":{"type":"object","properties":{"market_ids":{"type":"array","items":{"type":"string"}},"types":{"type":"array","items":{"type":"string","enum":["podcast","artist","movie","book"]}}},"required":["market_ids"]}}},
 {"type":"function","function":{"name":"write_briefs","description":"Write grounded market briefs.","parameters":{"type":"object","properties":{"market_ids":{"type":"array","items":{"type":"string"}}},"required":["market_ids"]}}},
 {"type":"function","function":{"name":"finish_phase","description":"End the phase with a short summary for the user.","parameters":{"type":"object","properties":{"summary":{"type":"string","maxLength":500}},"required":["summary"]}}}
]
```

## Prompts (`llm/prompts/`, versioned)

| File | Output |
|---|---|
| `destination_items.md` | `{"items":[{"name":str,"kind":enum}]}` up to 15 |
| `agent_scoring.md` | Tool calls, then `finish_phase` |
| `agent_deep_dive.md` | Tool calls, then `finish_phase` |
| `market_brief.md` | Brief JSON with cited evidence ids |
| `repair_json.md` | Corrected JSON |

Each prompt: role, goal, rules ("never invent markets, numbers, partners or facts; use only provided data"), the JSON Schema as text when JSON is expected, and "return only one JSON object". Website text is wrapped in clear delimiters as untrusted data.

## Structured output helper

Prompt with schema → extract the outermost JSON object (strip fences) → Pydantic validate → one repair call with errors → `LLMBadResponseError` → caller's fallback (manual list, template brief, deterministic plan).

## Limits

`LLM_MAX_STEPS_PER_PHASE` (12), `LLM_MAX_CALLS_PER_RUN` (40), timeout `LLM_TIMEOUT_SECONDS`, one retry on 5xx/timeout. Every call logged in `llm_calls` (purpose, provider, model, prompt version, status, duration, tokens), never with prompt text in production.
