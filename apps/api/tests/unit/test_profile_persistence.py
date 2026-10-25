from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tastebound_api.agent.executor import RunContext, RunExecutor
from tastebound_api.db.database import dispose_db, get_session_factory, init_db
from tastebound_api.db.tables import Destination, ProfileEntity, Run, SignatureItem, Workspace
from tastebound_api.qloo.service import DestinationMatch, QlooService, ResolvedItem
from tastebound_api.settings import get_settings


class _StubService(QlooService):
    def __init__(self, match: DestinationMatch, resolved: dict[str, ResolvedItem]) -> None:
        self._match = match
        self._resolved = resolved

    async def resolve_destination(
        self,
        name: str,
        *,
        country_code: str | None,
        run_id: str | None,
        step: str = "destination_search",
    ) -> DestinationMatch:
        return self._match

    async def resolve_item(
        self,
        *,
        item_id: str | None,
        name: str,
        kind: str,
        destination: DestinationMatch,
        run_id: str | None,
        position: int = 0,
    ) -> ResolvedItem:
        resolved = self._resolved[name]
        return ResolvedItem(
            item_id=item_id,
            name=resolved.name,
            kind=kind,
            role="requested",
            entity_id=resolved.entity_id,
            entity_name=resolved.entity_name,
            entity_type=resolved.entity_type,
            similarity=resolved.similarity,
            status="resolved",
            note=None,
            tags=[],
            call_id=resolved.call_id,
        )


@pytest.fixture
async def session_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "profile-test.db"))
    get_settings.cache_clear()
    await dispose_db()
    await init_db()
    yield get_session_factory()
    await dispose_db()
    get_settings.cache_clear()


async def test_profile_insert_dedupes_duplicate_entity_ids(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    workspace_id = "workspace-1"
    destination_id = "destination-row-1"
    run_id = "run-1"
    item_names = ["CN Tower", "CN Tower tour", "Royal Ontario Museum", "St. Lawrence Market"]

    async with session_factory() as session:
        session.add(Workspace(id=workspace_id))
        await session.flush()
        session.add(
            Destination(
                id=destination_id,
                workspace_id=workspace_id,
                name="Toronto",
                country_code="CA",
            )
        )
        session.add(Run(id=run_id, workspace_id=workspace_id, destination_id=destination_id))
        for position, name in enumerate(item_names):
            session.add(
                SignatureItem(
                    id=f"item-{position}",
                    workspace_id=workspace_id,
                    destination_id=destination_id,
                    name=name,
                    kind="landmark",
                    position=position,
                )
            )
        await session.commit()

    async with session_factory() as session:
        run = await session.get(Run, run_id)
        destination = await session.get(Destination, destination_id)
        items = (
            (
                await session.execute(
                    select(SignatureItem)
                    .where(SignatureItem.destination_id == destination_id)
                    .order_by(SignatureItem.position)
                )
            )
            .scalars()
            .all()
        )
    assert run is not None
    assert destination is not None

    match = DestinationMatch(
        query="Toronto",
        name="Toronto",
        entity_id="destination-toronto",
        entity_type="destination",
        lat=43.6532,
        lon=-79.3832,
        country_code="CA",
        country_name="Canada",
        tags=[],
        call_id="call-destination",
    )
    resolved = {
        "CN Tower": ResolvedItem(
            item_id="item-0",
            name="CN Tower",
            kind="landmark",
            role="requested",
            entity_id="place-cn-tower",
            entity_name="CN Tower",
            entity_type="place",
            similarity=1.0,
            status="resolved",
            note=None,
            tags=[],
            call_id="call-cn-tower",
        ),
        "CN Tower tour": ResolvedItem(
            item_id="item-1",
            name="CN Tower tour",
            kind="landmark",
            role="requested",
            entity_id="place-cn-tower",
            entity_name="CN Tower",
            entity_type="place",
            similarity=0.95,
            status="resolved",
            note=None,
            tags=[],
            call_id="call-cn-tower-tour",
        ),
        "Royal Ontario Museum": ResolvedItem(
            item_id="item-2",
            name="Royal Ontario Museum",
            kind="landmark",
            role="requested",
            entity_id="place-rom",
            entity_name="Royal Ontario Museum",
            entity_type="place",
            similarity=1.0,
            status="resolved",
            note=None,
            tags=[],
            call_id="call-rom",
        ),
        "St. Lawrence Market": ResolvedItem(
            item_id="item-3",
            name="St. Lawrence Market",
            kind="landmark",
            role="requested",
            entity_id="place-st-lawrence",
            entity_name="St. Lawrence Market",
            entity_type="place",
            similarity=1.0,
            status="resolved",
            note=None,
            tags=[],
            call_id="call-st-lawrence",
        ),
    }

    executor = RunExecutor(session_factory)
    executor.service = _StubService(match, resolved)
    executor.context = RunContext(run=run, destination=destination, items=list(items))

    summary = await executor.tool_build_profile()

    assert summary["resolved"] == 3
    assert executor.context.profile is not None
    assert "Merged duplicate profile matches: CN Tower tour" in executor.context.profile.warnings

    async with session_factory() as session:
        rows = (
            (await session.execute(select(ProfileEntity).where(ProfileEntity.run_id == run_id)))
            .scalars()
            .all()
        )
    entity_ids = [row.qloo_entity_id for row in rows]
    assert len(entity_ids) == len(set(entity_ids))
    assert set(entity_ids) == {
        "destination-toronto",
        "place-cn-tower",
        "place-rom",
        "place-st-lawrence",
    }
