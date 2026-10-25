# 05. LLM, grounding and provider portability

## Role of the model

TasteBound is deliberately not a model-ranked product. Qloo supplies the taste data, and the scoring, gap, audience, angle, allocation and partner logic is deterministic code. The model has two narrow jobs:

| Use | Shipped behaviour | Can change numbers? |
|---|---|---|
| Destination item suggestions | One prompt-and-validate call; Qloo resolves or rejects each proposed name | No |
| Market brief prose | Gated behind `LLM_TOOL_CALLING=false`; the shipped demo and default path use templates | No; the grounding validator rejects unsupported numbers/names |
| Tool selection | **Not used.** The executor runs a fixed sequence | No |

If the model is unavailable, intake still works with manual items and briefs remain labelled `template`.

## Provider and model

- **Ollama Cloud over HTTPS with an API key.** No local Ollama, no gateway and no OpenRouter.
- Endpoint: `POST {OLLAMA_BASE_URL}/chat/completions` with `OLLAMA_BASE_URL=https://ollama.com/v1`, header `Authorization: Bearer {OLLAMA_API_KEY}`.
- Request: `{model, messages, stream: false, temperature, response_format?}`. The reply text is `choices[0].message.content`.
- Default model: **Gemma 4 31B** (`gemma4:31b-cloud` in this repository). Model names must exist in the account's Ollama library; `/health` shows the configured provider and model.
- Requests are non-streaming. There is no token-streaming UI or fake streaming.
- JSON is prompt-and-validate. Do not assume provider-native JSON-schema support.

## Portability

Only files under `apps/api/src/tastebound_api/llm/` may name a provider.

```python
class LLMProvider(Protocol):
    name: str
    model: str

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResult: ...

    async def aclose(self) -> None: ...
```

| Component | File | Notes |
|---|---|---|
| Factory | `llm/provider.py` | Builds the configured provider once; returns `None` when unconfigured |
| OpenAI-compatible adapter | `llm/openai_compat.py` | Used for Ollama Cloud, Gemini's OpenAI-compatible endpoint and custom direct APIs |
| Fake adapter | `llm/fake.py` | Scripted replies for tests; never used in production |
| Parsing | `llm/parsing.py` | Extracts and validates JSON without trusting fences or extra text |

Switching providers means changing `LLM_PROVIDER` plus that provider's base URL, key and model. Prompts contain no provider-specific syntax. Provider errors are normalised to `LLMAuthError`, `LLMRateLimitError`, `LLMTimeoutError`, `LLMBadResponseError` and `LLMUnavailable`.

## Grounding

The model never supplies Qloo IDs, scores, gaps, audience numbers or partner rankings.

- Destination items are names only. Qloo search resolves them, and unresolved names are returned to the user with a reason.
- Brief output is checked against the evidence bundle: every number must occur in the supplied evidence, every cited name must come from the bundle, and evidence IDs must be known.
- Invalid brief output gets one repair attempt. If it still fails, the deterministic template brief is used and labelled `template`.

## Prompts

| File | Output | Used |
|---|---|---|
| `destination_items.md` | `{"items":[{"name": str, "kind": enum}]}` | Yes |
| `market_brief.md` | Brief JSON with cited evidence IDs | Only when the gated model-writing path is enabled |
| `repair_json.md` | Corrected JSON after a validation failure | Yes, for briefs |
| `agent_scoring.md`, `agent_deep_dive.md` | Legacy tool-choice instructions | No; the shipped executor is deterministic |

All prompts wrap untrusted website or user text in clear delimiters and instruct the model to ignore embedded instructions. Prompt text is not logged or traced.

## Limits and privacy

- `LLM_TIMEOUT_SECONDS` (90), `LLM_MAX_CALLS_PER_RUN` (40), one repair attempt and bounded output.
- `LLM_TOOL_CALLING` stays `false`; `/health` reports `tools_ok` from this switch.
- Every model call is recorded in `llm_calls` with purpose, provider, model, prompt version, status, duration and token counts — never prompt text.
- Keys are read only by the API process and are never returned, traced, logged or bundled into the browser.

## Current limitations

- Live tool calling on Ollama Cloud was not verified because the free key exhausted its quota. No tool-choice loop is shipped.
- The model-writing path is disabled by default. Template briefs are the reliable, tested output.
- Model output is prose. All quantitative claims in the product come from deterministic code and stored Qloo evidence.
