from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from tastebound_api.errors import LLMUnavailable
from tastebound_api.llm.base import ChatMessage, LLMResult, ToolCall, ToolSpec


class FakeProvider:
    """Deterministic provider for tests and offline demos."""

    name = "fake"
    model = "fake-1"

    def __init__(self, responses: Iterable[LLMResult] | None = None) -> None:
        self._responses = list(responses or [])
        self.calls: list[list[ChatMessage]] = []

    async def aclose(self) -> None:
        return None

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResult:
        self.calls.append(messages)
        if not self._responses:
            raise LLMUnavailable("FakeProvider has no scripted response left.")
        return self._responses.pop(0)


def text_response(content: str, *, model: str = "fake-1") -> LLMResult:
    return LLMResult(content=content, tool_calls=[], model=model)


def tool_response(name: str, arguments: dict[str, Any], *, call_id: str = "call_1") -> LLMResult:
    return LLMResult(
        content=None,
        tool_calls=[ToolCall(id=call_id, name=name, arguments=arguments)],
        model="fake-1",
    )
