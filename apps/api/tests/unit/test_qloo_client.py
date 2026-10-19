from __future__ import annotations

import time
from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tastebound_api.db.database import dispose_db, get_session_factory, init_db
from tastebound_api.errors import QlooAuthError, QlooBudgetExceeded, QlooUnconfigured
from tastebound_api.qloo.client import QlooClient
from tastebound_api.settings import Settings, get_settings


@pytest.fixture
async def session_factory(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "qloo-test.db"))  # type: ignore[operator]
    get_settings.cache_clear()
    await dispose_db()
    await init_db()
    yield get_session_factory()
    await dispose_db()
    get_settings.cache_clear()


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "app_env": "test",
        "qloo_api_key": "test-key",
        "qloo_base_url": "https://qloo.test",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


async def test_unconfigured_client_fails_closed(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    client = QlooClient(session_factory, settings=_settings(qloo_api_key=""))
    with pytest.raises(QlooUnconfigured):
        await client.get("/search", {"query": "x"}, run_id=None, step="test")
    await client.aclose()


async def test_cache_reuse_avoids_second_http_call(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, json={"results": {"entities": [{"entity_id": "e1"}]}})

    client = QlooClient(
        session_factory,
        settings=_settings(),
        transport=httpx.MockTransport(handler),
    )
    first = await client.get("/search", {"query": "lisbon"}, run_id=None, step="search")
    second = await client.get("/search", {"query": "lisbon"}, run_id=None, step="search")
    assert calls["count"] == 1
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.data == first.data
    await client.aclose()


async def test_rate_limit_spaces_live_calls(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": {"entities": []}})

    client = QlooClient(
        session_factory,
        settings=_settings(qloo_rps=50),
        transport=httpx.MockTransport(handler),
    )
    started = time.monotonic()
    await client.get("/search", {"query": "a"}, run_id=None, step="s")
    await client.get("/search", {"query": "b"}, run_id=None, step="s")
    elapsed = time.monotonic() - started
    assert elapsed >= 1.0 / 50 - 0.002
    await client.aclose()


async def test_auth_error_is_not_retried(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(401, json={"error": "nope"})

    client = QlooClient(
        session_factory,
        settings=_settings(),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(QlooAuthError):
        await client.get("/search", {"query": "x"}, run_id=None, step="s")
    assert calls["count"] == 1
    await client.aclose()


async def test_per_run_budget_is_enforced(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": {"entities": []}})

    client = QlooClient(
        session_factory,
        settings=_settings(qloo_max_calls_per_run=1),
        transport=httpx.MockTransport(handler),
    )
    await client.get("/search", {"query": "one"}, run_id=None, step="s")
    with pytest.raises(QlooBudgetExceeded):
        await client.get("/search", {"query": "two"}, run_id=None, step="s")
    await client.aclose()


async def test_every_call_is_traced(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    from sqlalchemy import func, select

    from tastebound_api.db.tables import QlooCall

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": {"entities": []}})

    client = QlooClient(
        session_factory,
        settings=_settings(),
        transport=httpx.MockTransport(handler),
    )
    await client.get("/search", {"query": "x"}, run_id=None, step="search")
    async with session_factory() as session:
        count = await session.scalar(select(func.count(QlooCall.id)))
    assert count == 1
    await client.aclose()
