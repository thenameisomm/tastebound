from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import delete

from tastebound_api.db.database import get_session_factory, utcnow
from tastebound_api.db.tables import (
    Allocation,
    ArrivalsDataset,
    ArrivalsRow,
    Base,
    Brief,
    Destination,
    MarketAngle,
    MarketAudience,
    MarketPartner,
    MarketScore,
    ProfileEntity,
    ProfileTag,
    Run,
    RunEvent,
    RunMarket,
    SignatureItem,
    Workspace,
)
from tastebound_api.settings import API_ROOT, DEMO_WORKSPACE_ID

DEMO_RUN_PATH = API_ROOT / "data/demo/lisbon-run.json"
DEMO_ACTIVE_PATH = API_ROOT / "data/demo/active.json"


def _parse_datetimes(model: type[Base], payload: dict[str, Any]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str) and key.endswith("_at"):
            try:
                parsed[key] = datetime.fromisoformat(value)
                continue
            except ValueError:
                parsed[key] = utcnow()
                continue
        parsed[key] = value
    return parsed


def _row(model: type[Base], data: dict[str, Any], overrides: dict[str, Any]) -> Base:
    columns = {column.name for column in model.__table__.columns}
    payload = {key: value for key, value in data.items() if key in columns}
    payload.update(overrides)
    return model(**_parse_datetimes(model, payload))


async def seed_demo() -> bool:
    if not DEMO_RUN_PATH.exists():
        return False
    try:
        payload = json.loads(DEMO_RUN_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    run_data = payload.get("run")
    if not isinstance(run_data, dict) or not run_data.get("id"):
        return False
    run_id = str(run_data["id"])
    session_factory = get_session_factory()
    async with session_factory() as session:
        run_scoped: list[Any] = [
            RunEvent,
            MarketScore,
            MarketAudience,
            MarketAngle,
            MarketPartner,
            ProfileEntity,
            ProfileTag,
            Brief,
            Allocation,
            RunMarket,
        ]
        for model in run_scoped:
            await session.execute(delete(model).where(model.run_id == run_id))
        await session.execute(delete(Run).where(Run.id == run_id))
        destination_data = payload.get("destination") or {}
        destination_id = destination_data.get("id")
        if destination_id:
            await session.execute(
                delete(SignatureItem).where(SignatureItem.destination_id == destination_id)
            )
            await session.execute(
                delete(ArrivalsRow).where(
                    ArrivalsRow.dataset_id.in_(select_dataset_ids(payload.get("arrivals_dataset")))
                )
            )
            await session.execute(
                delete(ArrivalsDataset).where(ArrivalsDataset.destination_id == destination_id)
            )
            await session.execute(delete(Destination).where(Destination.id == destination_id))
        await session.commit()
        workspace = await session.get(Workspace, DEMO_WORKSPACE_ID)
        if workspace is None:
            session.add(Workspace(id=DEMO_WORKSPACE_ID, kind="demo"))
            await session.commit()
        if destination_id:
            session.add(_row(Destination, destination_data, {"workspace_id": DEMO_WORKSPACE_ID}))
        for item in payload.get("signature_items", []):
            session.add(_row(SignatureItem, item, {"workspace_id": DEMO_WORKSPACE_ID}))
        await session.flush()
        arrivals_dataset = payload.get("arrivals_dataset")
        if isinstance(arrivals_dataset, dict) and arrivals_dataset.get("id"):
            session.add(
                _row(ArrivalsDataset, arrivals_dataset, {"workspace_id": DEMO_WORKSPACE_ID})
            )
            await session.flush()
        for row_data in payload.get("arrivals_rows", []):
            session.add(_row(ArrivalsRow, row_data, {}))
        for row_data in payload.get("run_markets", []):
            session.add(_row(RunMarket, row_data, {}))
        session.add(_row(Run, run_data, {"workspace_id": DEMO_WORKSPACE_ID}))
        await session.commit()
        for row_data in payload.get("profile_entities", []):
            session.add(_row(ProfileEntity, row_data, {}))
        for row_data in payload.get("profile_tags", []):
            session.add(_row(ProfileTag, row_data, {}))
        for row_data in payload.get("market_scores", []):
            session.add(_row(MarketScore, row_data, {}))
        for row_data in payload.get("market_audience", []):
            session.add(_row(MarketAudience, row_data, {}))
        for row_data in payload.get("market_angles", []):
            session.add(_row(MarketAngle, row_data, {}))
        for row_data in payload.get("market_partners", []):
            session.add(_row(MarketPartner, row_data, {}))
        for row_data in payload.get("briefs", []):
            session.add(_row(Brief, row_data, {"workspace_id": DEMO_WORKSPACE_ID}))
        for row_data in payload.get("allocations", []):
            session.add(_row(Allocation, row_data, {"workspace_id": DEMO_WORKSPACE_ID}))
        for row_data in payload.get("run_events", []):
            session.add(_row(RunEvent, row_data, {}))
        await session.commit()
    DEMO_ACTIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEMO_ACTIVE_PATH.write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
    return True


def select_dataset_ids(arrivals_dataset: Any) -> list[str]:
    if isinstance(arrivals_dataset, dict) and arrivals_dataset.get("id"):
        return [str(arrivals_dataset["id"])]
    return []
