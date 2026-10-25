from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import httpx
import pytest
from httpx import ASGITransport

from tastebound_api.db.database import dispose_db, get_session_factory, init_db
from tastebound_api.db.demo_seed import seed_demo
from tastebound_api.db.tables import Run
from tastebound_api.main import app
from tastebound_api.settings import get_settings

SAMPLE_CSV = (
    "origin,arrivals,year\nLisbon,1200,2024\nParis,800,2024\nSpain,900,2024\nAtlantis,10,2024\n"
)


@pytest.fixture
async def client(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "api-test.db"))  # type: ignore[operator]
    get_settings.cache_clear()
    await dispose_db()
    await init_db()
    await seed_demo()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
        yield api
    await dispose_db()
    get_settings.cache_clear()


async def _token(api: httpx.AsyncClient) -> str:
    response = await api.post("/v1/workspaces/session", json={})
    assert response.status_code == 200
    return str(response.json()["workspace_token"])


async def test_workspace_token_is_required(client: httpx.AsyncClient) -> None:
    anonymous = await client.get("/v1/markets")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "invalid_workspace"

    token = await _token(client)
    authorized = await client.get("/v1/markets", headers={"X-Workspace-Token": token})
    assert authorized.status_code == 200
    payload = authorized.json()
    assert len(payload["markets"]) == 68
    assert any(preset["id"] == "europe20" for preset in payload["presets"])


async def test_destination_create_update_and_get(client: httpx.AsyncClient) -> None:
    token = await _token(client)
    headers = {"X-Workspace-Token": token}
    created = await client.post(
        "/v1/destinations",
        headers=headers,
        json={
            "name": "Porto",
            "country_code": "pt",
            "items": [
                {"name": "Livraria Lello", "kind": "landmark", "origin": "user"},
                {"name": "Fado", "kind": "music", "origin": "user"},
            ],
        },
    )
    assert created.status_code == 201, created.text
    destination = created.json()
    assert destination["country_code"] == "PT"
    assert len(destination["items"]) == 2

    updated = await client.patch(
        f"/v1/destinations/{destination['destination_id']}",
        headers=headers,
        json={"items": [{"name": "Livraria Lello", "kind": "landmark", "origin": "user"}]},
    )
    assert updated.status_code == 200
    assert len(updated.json()["items"]) == 1

    fetched = await client.get(f"/v1/destinations/{destination['destination_id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Porto"


async def test_arrivals_upload_matches_sample(client: httpx.AsyncClient) -> None:
    token = await _token(client)
    response = await client.post(
        "/v1/arrivals",
        headers={"X-Workspace-Token": token},
        data={"source_note": "Unit test upload"},
        files={"file": ("arrivals.csv", SAMPLE_CSV.encode(), "text/csv")},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["rows"] == 4
    assert payload["matched_markets"] >= 2
    assert "ES" in payload["matched_countries"]
    assert len(payload["unmatched"]) == 1


async def test_arrivals_bundled_sample_upload(client: httpx.AsyncClient) -> None:
    token = await _token(client)
    samples = await client.get("/v1/arrivals/samples", headers={"X-Workspace-Token": token})
    assert samples.status_code == 200
    sample_id = samples.json()[0]["id"]

    response = await client.post(
        "/v1/arrivals",
        headers={"X-Workspace-Token": token},
        data={"source_note": "Bundled sample", "sample_id": sample_id},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["is_sample"] is True
    assert payload["rows"] >= 15
    assert payload["matched_markets"] >= 20


async def test_run_fails_closed_without_qloo_key(client: httpx.AsyncClient) -> None:
    token = await _token(client)
    headers = {"X-Workspace-Token": token}
    created = await client.post(
        "/v1/destinations",
        headers=headers,
        json={
            "name": "Porto",
            "country_code": "PT",
            "items": [{"name": "Livraria Lello", "kind": "landmark", "origin": "user"}],
        },
    )
    destination_id = created.json()["destination_id"]
    run = await client.post(
        "/v1/runs",
        headers=headers,
        json={
            "destination_id": destination_id,
            "market_ids": ["es-madrid", "fr-paris", "pt-lisbon"],
        },
    )
    assert run.status_code == 202, run.text
    run_id = run.json()["run_id"]

    status = "queued"
    for _ in range(100):
        detail = await client.get(f"/v1/runs/{run_id}", headers=headers)
        assert detail.status_code == 200
        status = detail.json()["status"]
        if status in {"done", "failed", "partial"}:
            break
        await asyncio.sleep(0.05)
    payload = detail.json()
    assert status == "failed"
    assert payload["error_code"] == "qloo_unconfigured"
    assert payload["counters"]["qloo_live"] == 0


async def test_run_rejects_more_than_forty_markets(client: httpx.AsyncClient) -> None:
    token = await _token(client)
    headers = {"X-Workspace-Token": token}
    created = await client.post(
        "/v1/destinations",
        headers=headers,
        json={
            "name": "Porto",
            "country_code": "PT",
            "items": [{"name": "Livraria Lello", "kind": "landmark", "origin": "user"}],
        },
    )
    destination_id = created.json()["destination_id"]
    run = await client.post(
        "/v1/runs",
        headers=headers,
        json={
            "destination_id": destination_id,
            "market_ids": [f"xx-market-{index}" for index in range(41)],
        },
    )
    assert run.status_code == 422, run.text
    assert run.json()["code"] == "validation_error"


async def test_demo_is_public_and_read_only(client: httpx.AsyncClient) -> None:
    demo = await client.get("/v1/demo")
    assert demo.status_code == 200
    payload = demo.json()
    assert payload["sample"] is True
    assert payload["run_id"] == "demo-e5b2b8fd"
    assert payload["destination"] == "Lisbon"

    token = await _token(client)
    headers = {"X-Workspace-Token": token}
    markets = await client.get("/v1/runs/demo-e5b2b8fd/markets", headers=headers)
    assert markets.status_code == 200
    assert len(markets.json()["markets"]) == 68

    briefs = await client.get("/v1/runs/demo-e5b2b8fd/briefs", headers=headers)
    assert briefs.status_code == 200
    assert len(briefs.json()) == 6

    trace = await client.get("/v1/runs/demo-e5b2b8fd/trace", headers=headers)
    assert trace.status_code == 200
    items = trace.json()["items"]
    qloo_ids = {item["detail"]["call_id"] for item in items if item["kind"] == "qloo"}
    assert len(qloo_ids) == 252
    assert {item["kind"] for item in items} == {"qloo", "tool"}

    patch = await client.patch(
        "/v1/briefs/demo-3123cce6",
        headers=headers,
        json={"title": "Hacked"},
    )
    assert patch.status_code == 403
    assert patch.json()["code"] == "demo_read_only"

    deep_dive = await client.post(
        "/v1/runs/demo-e5b2b8fd/deep-dive",
        headers=headers,
        json={"market_ids": ["co-cartagena", "jp-tokyo", "my-kuala-lumpur"]},
    )
    assert deep_dive.status_code == 403


async def test_demo_profile_returns_structured_warnings(client: httpx.AsyncClient) -> None:
    token = await _token(client)
    headers = {"X-Workspace-Token": token}
    session_factory = get_session_factory()
    async with session_factory() as session:
        run = await session.get(Run, "demo-e5b2b8fd")
        assert run is not None
        settings = dict(run.settings or {})
        settings["warnings"] = [
            {"code": "no_arrivals", "message": "No arrivals uploaded; gap view disabled."}
        ]
        run.settings = settings
        await session.commit()

    response = await client.get("/v1/runs/demo-e5b2b8fd/profile", headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["warnings"][0]["code"] == "no_arrivals"
    assert len(payload["entities"]) > 0
