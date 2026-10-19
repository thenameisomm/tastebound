from __future__ import annotations

import json
from typing import Any

import httpx

from tastebound_api.errors import (
    LLMAuthError,
    LLMBadResponseError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailable,
)
from tastebound_api.llm.base import ChatMessage, LLMResult, ToolCall, ToolSpec


class OpenAICompatibleProvider:
    """Any OpenAI-compatible chat completions endpoint (Ollama Cloud, Gemini compat, ...)."""

    name = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 90.0,
        label: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.name = label or self.name
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [message.to_openai() for message in messages],
            "temperature": temperature,
            "stream": False,
        }
        if tools:
            payload["tools"] = [tool.to_openai() for tool in tools]
        if response_format:
            payload["response_format"] = response_format
        try:
            response = await self._client.post("/chat/completions", json=payload, follow_redirects=True)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError() from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailable(str(exc)) from exc
        if response.status_code == 401:
            raise LLMAuthError()
        if response.status_code == 429:
            raise LLMRateLimitError(response.text[:200])
        if response.status_code >= 500:
            raise LLMUnavailable(f"Provider returned HTTP {response.status_code}.")
        if response.status_code >= 400:
            raise LLMUnavailable(f"Provider returned HTTP {response.status_code}: {response.text[:200]}")
        try:
            body = response.json()
        except ValueError as exc:
            raise LLMUnavailable("Provider returned non-JSON content (likely auth redirect).") from exc
        try:
            message = body["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMBadResponseError("Provider returned an unexpected response shape.") from exc
        tool_calls: list[ToolCall] = []
        for index, call in enumerate(message.get("tool_calls") or []):
            function = call.get("function") or {}
            arguments = function.get("arguments") or "{}"
            if isinstance(arguments, str):
                try:
                    parsed = json.loads(arguments)
                except json.JSONDecodeError:
                    parsed = {}
            else:
                parsed = arguments
            tool_calls.append(
                ToolCall(
                    id=str(call.get("id") or f"call_{index}"),
                    name=str(function.get("name") or ""),
                    arguments=parsed if isinstance(parsed, dict) else {},
                )
            )
        usage = body.get("usage") or {}
        return LLMResult(
            content=message.get("content"),
            tool_calls=tool_calls,
            model=str(body.get("model") or self.model),
            usage={
                "input_tokens": int(usage.get("prompt_tokens") or 0),
                "output_tokens": int(usage.get("completion_tokens") or 0),
            },
            reasoning=message.get("reasoning"),
        )
