from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
import pytest
from httpx import ASGITransport

from tastebound_api.assistant import store
from tastebound_api.db.database import dispose_db, init_db
from tastebound_api.db.demo_seed import seed_demo
from tastebound_api.llm.fake import FakeProvider, text_response
from tastebound_api.main import app
from tastebound_api.ratelimit import reset as reset_rate_limits
from tastebound_api.routes import assistant as assistant_routes
from tastebound_api.settings import get_settings

DEMO_RUN = "demo-e5b2b8fd"
FOCUS = "co-cartagena"


@pytest.fixture
async def client(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "assistant-test.db"))  # type: ignore[operator]
    monkeypatch.setenv("OLLAMA_API_KEY", "")
    get_settings.cache_clear()
    store.reset()
    reset_rate_limits()
    await dispose_db()
    await init_db()
    await seed_demo()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
        yield api
    store.reset()
    reset_rate_limits()
    await dispose_db()
    get_settings.cache_clear()


async def _token(api: httpx.AsyncClient) -> str:
    response = await api.post("/v1/workspaces/session", json={})
    assert response.status_code == 200
    return str(response.json()["workspace_token"])


def _answer(
    *,
    text: str = (
        "Cartagena leads this run with a taste score of 99.26 and a gap of 98.17 points. "
        "The evidence is high confidence. Taste fit is not a visitor forecast."
    ),
    evidence: list[str] | None = None,
) -> str:
    return json.dumps(
        {
            "answer": text,
            "evidence_ids": evidence or ["E1"],
            "followups": ["What should we lead with in Cartagena?"],
        }
    )


def _use_fake(monkeypatch: pytest.MonkeyPatch, responses: list[str] | None = None) -> FakeProvider:
    fake = FakeProvider([text_response(item) for item in (responses or [_answer()])])
    monkeypatch.setattr(assistant_routes, "get_assistant_provider", lambda _settings: fake)
    return fake


async def _headers(api: httpx.AsyncClient) -> dict[str, str]:
    return {"X-Workspace-Token": await _token(api)}


async def _create_conversation(api: httpx.AsyncClient, headers: dict[str, str]) -> dict[str, str]:
    response = await api.post(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations",
        headers=headers,
        json={"focus_market_id": FOCUS},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_bootstrap_is_honest_without_a_provider(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(assistant_routes, "get_assistant_provider", lambda _settings: None)
    headers = await _headers(client)
    response = await client.get(
        f"/v1/runs/{DEMO_RUN}/assistant",
        headers=headers,
        params={"focus_market_id": FOCUS},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is False
    assert payload["ready"] is False
    assert payload["model"] is None
    assert payload["suggested_questions"]
    assert "model provider" in payload["notice"]

    create = await client.post(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations",
        headers=headers,
        json={"focus_market_id": FOCUS},
    )
    assert create.status_code == 503
    assert create.json()["code"] == "assistant_unavailable"


async def test_grounded_answer_and_evidence(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _use_fake(monkeypatch)
    headers = await _headers(client)

    bootstrap = await client.get(
        f"/v1/runs/{DEMO_RUN}/assistant",
        headers=headers,
        params={"focus_market_id": FOCUS},
    )
    assert bootstrap.status_code == 200, bootstrap.text
    payload = bootstrap.json()
    assert payload["enabled"] is True
    assert payload["ready"] is True
    assert payload["model"] == "fake-1"
    assert any("Cartagena" in question for question in payload["suggested_questions"])

    conversation = await _create_conversation(client, headers)
    assert conversation["messages"] == []
    conversation_id = conversation["conversation_id"]

    response = await client.post(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations/{conversation_id}/messages",
        headers=headers,
        json={"message": "Which market should we prioritise?", "focus_market_id": FOCUS},
    )
    assert response.status_code == 201, response.text
    answer = response.json()
    assert "Taste fit is not a visitor forecast" in answer["answer"]
    assert answer["model"] == "fake-1"
    assert answer["evidence"]
    assert answer["evidence"][0]["href"].endswith("#score")
    assert answer["followups"] == ["What should we lead with in Cartagena?"]
    assert len(fake.calls) == 1
    assert "RUN CONTEXT" in str(fake.calls[0][1].content)

    fetched = await client.get(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations/{conversation_id}",
        headers=headers,
    )
    assert fetched.status_code == 200, fetched.text
    messages = fetched.json()["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["evidence"]


async def test_invalid_evidence_gets_one_repair(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _use_fake(
        monkeypatch,
        [
            _answer(evidence=["E999"]),
            _answer(),
        ],
    )
    headers = await _headers(client)
    conversation = await _create_conversation(client, headers)
    response = await client.post(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations/{conversation['conversation_id']}/messages",
        headers=headers,
        json={"message": "Explain the top market."},
    )
    assert response.status_code == 201, response.text
    assert len(fake.calls) == 2
    assert response.json()["evidence"][0]["id"] == "E1"


async def test_ungrounded_answer_fails_without_partial_history(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_fake(
        monkeypatch,
        [
            _answer(evidence=["E999"]),
            _answer(evidence=["E998"]),
        ],
    )
    headers = await _headers(client)
    conversation = await _create_conversation(client, headers)
    response = await client.post(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations/{conversation['conversation_id']}/messages",
        headers=headers,
        json={"message": "Explain the top market."},
    )
    assert response.status_code == 502
    assert response.json()["code"] == "assistant_ungrounded"

    fetched = await client.get(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations/{conversation['conversation_id']}",
        headers=headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["messages"] == []


async def test_conversation_is_workspace_and_run_scoped(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_fake(monkeypatch)
    headers = await _headers(client)
    conversation = await _create_conversation(client, headers)

    other_headers = await _headers(client)
    other_workspace = await client.get(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations/{conversation['conversation_id']}",
        headers=other_headers,
    )
    assert other_workspace.status_code == 404
    assert other_workspace.json()["code"] == "conversation_not_found"

    missing = await client.get(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "conversation_not_found"


async def test_message_rate_limit_has_an_assistant_error(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "assistant_messages_per_workspace_per_hour", 1)
    _use_fake(monkeypatch, [_answer(), _answer()])
    headers = await _headers(client)
    conversation = await _create_conversation(client, headers)
    url = f"/v1/runs/{DEMO_RUN}/assistant/conversations/{conversation['conversation_id']}/messages"

    first = await client.post(url, headers=headers, json={"message": "First question."})
    assert first.status_code == 201, first.text
    second = await client.post(url, headers=headers, json={"message": "Second question."})
    assert second.status_code == 429
    assert second.json()["code"] == "assistant_rate_limited"


async def test_blank_message_is_rejected(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_fake(monkeypatch)
    headers = await _headers(client)
    conversation = await _create_conversation(client, headers)
    response = await client.post(
        f"/v1/runs/{DEMO_RUN}/assistant/conversations/{conversation['conversation_id']}/messages",
        headers=headers,
        json={"message": "   "},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
