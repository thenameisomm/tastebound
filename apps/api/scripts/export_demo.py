from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from tastebound_api.db.database import get_session_factory, init_db
from tastebound_api.db.tables import (
    Allocation,
    ArrivalsDataset,
    ArrivalsRow,
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
)

OUTPUT = Path("data/demo/lisbon-run.json")


def _dump(model: Any, row: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for column in model.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        payload[column.name] = value
    return payload


def _remap(value: str | None, mapping: dict[str, str]) -> str | None:
    if value is None:
        return None
    return mapping.get(value, value)


async def export(run_id: str) -> dict[str, Any]:
    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as session:
        run = await session.get(Run, run_id)
        if run is None:
            raise SystemExit(f"run {run_id} not found")
        destination = await session.get(Destination, run.destination_id)
        items = (
            (
                await session.execute(
                    select(SignatureItem)
                    .where(SignatureItem.destination_id == run.destination_id)
                    .order_by(SignatureItem.position)
                )
            )
            .scalars()
            .all()
        )
        dataset = None
        arrivals_rows: list[ArrivalsRow] = []
        if run.arrivals_dataset_id:
            dataset = await session.get(ArrivalsDataset, run.arrivals_dataset_id)
            arrivals_rows = list(
                (
                    await session.execute(
                        select(ArrivalsRow).where(ArrivalsRow.dataset_id == run.arrivals_dataset_id)
                    )
                )
                .scalars()
                .all()
            )
        run_markets = (
            (await session.execute(select(RunMarket).where(RunMarket.run_id == run_id)))
            .scalars()
            .all()
        )
        profile_entities = (
            (await session.execute(select(ProfileEntity).where(ProfileEntity.run_id == run_id)))
            .scalars()
            .all()
        )
        profile_tags = (
            (await session.execute(select(ProfileTag).where(ProfileTag.run_id == run_id)))
            .scalars()
            .all()
        )
        scores = (
            (await session.execute(select(MarketScore).where(MarketScore.run_id == run_id)))
            .scalars()
            .all()
        )
        audience = (
            (await session.execute(select(MarketAudience).where(MarketAudience.run_id == run_id)))
            .scalars()
            .all()
        )
        angles = (
            (await session.execute(select(MarketAngle).where(MarketAngle.run_id == run_id)))
            .scalars()
            .all()
        )
        partners = (
            (await session.execute(select(MarketPartner).where(MarketPartner.run_id == run_id)))
            .scalars()
            .all()
        )
        briefs = (
            (await session.execute(select(Brief).where(Brief.run_id == run_id))).scalars().all()
        )
        allocations = (
            (await session.execute(select(Allocation).where(Allocation.run_id == run_id)))
            .scalars()
            .all()
        )
        events = (
            (
                await session.execute(
                    select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.seq)
                )
            )
            .scalars()
            .all()
        )

    prefix = "demo-"
    id_map: dict[str, str] = {}
    if destination is not None:
        id_map[destination.id] = prefix + destination.id[:8]
    id_map[run.id] = prefix + run.id[:8]
    if dataset is not None:
        id_map[dataset.id] = prefix + dataset.id[:8]
    for item in items:
        id_map[item.id] = prefix + item.id[:8]
    for brief in briefs:
        id_map[brief.id] = prefix + brief.id[:8]
    for allocation in allocations:
        id_map[allocation.id] = prefix + allocation.id[:8]
    for partner in partners:
        id_map[partner.id] = prefix + partner.id[:8]

    run_payload = _dump(Run, run)
    run_payload["id"] = id_map[run.id]
    run_payload["destination_id"] = _remap(run.destination_id, id_map)
    run_payload["arrivals_dataset_id"] = _remap(run.arrivals_dataset_id, id_map)
    destination_payload = _dump(Destination, destination) if destination else None
    if destination_payload is not None:
        destination_payload["id"] = id_map[destination.id]
    items_payload = []
    for item in items:
        row = _dump(SignatureItem, item)
        row["id"] = id_map[item.id]
        row["destination_id"] = _remap(item.destination_id, id_map)
        items_payload.append(row)
    dataset_payload = None
    if dataset is not None:
        dataset_payload = _dump(ArrivalsDataset, dataset)
        dataset_payload["id"] = id_map[dataset.id]
        dataset_payload["destination_id"] = _remap(dataset.destination_id, id_map)
    arrivals_payload = []
    for row in arrivals_rows:
        payload = _dump(ArrivalsRow, row)
        payload.pop("id", None)
        payload["dataset_id"] = _remap(row.dataset_id, id_map)
        arrivals_payload.append(payload)
    events_payload = []
    for event in events:
        payload = _dump(RunEvent, event)
        payload.pop("id", None)
        payload["run_id"] = id_map[run.id]
        events_payload.append(payload)
    briefs_payload = []
    for brief in briefs:
        payload = _dump(Brief, brief)
        payload["id"] = id_map[brief.id]
        payload["run_id"] = id_map[run.id]
        briefs_payload.append(payload)
    allocations_payload = []
    for allocation in allocations:
        payload = _dump(Allocation, allocation)
        payload["id"] = id_map[allocation.id]
        payload["run_id"] = id_map[run.id]
        allocations_payload.append(payload)
    partners_payload = []
    for partner in partners:
        payload = _dump(MarketPartner, partner)
        payload["id"] = id_map[partner.id]
        payload["run_id"] = id_map[run.id]
        partners_payload.append(payload)

    def _remap_run(rows: list[Any]) -> list[dict[str, Any]]:
        remapped: list[dict[str, Any]] = []
        for row in rows:
            payload = _dump(type(row), row)
            payload["run_id"] = id_map[run.id]
            remapped.append(payload)
        return remapped

    return {
        "exported_at": datetime.now().isoformat(),
        "source_run_id": run.id,
        "run": run_payload,
        "destination": destination_payload,
        "signature_items": items_payload,
        "arrivals_dataset": dataset_payload,
        "arrivals_rows": arrivals_payload,
        "run_markets": _remap_run(list(run_markets)),
        "profile_entities": [
            {
                **payload,
                "id": prefix + str(payload["id"])[:8],
                "item_id": _remap(payload.get("item_id"), id_map),
            }
            for payload in _remap_run(list(profile_entities))
        ],
        "profile_tags": _remap_run(list(profile_tags)),
        "market_scores": _remap_run(list(scores)),
        "market_audience": _remap_run(list(audience)),
        "market_angles": _remap_run(list(angles)),
        "market_partners": partners_payload,
        "briefs": briefs_payload,
        "allocations": allocations_payload,
        "run_events": events_payload,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    bundle = asyncio.run(export(args.run_id))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, indent=1, ensure_ascii=False), encoding="utf-8")
    counts = {
        "markets": len(bundle["market_scores"]),
        "audience": len(bundle["market_audience"]),
        "angles": len(bundle["market_angles"]),
        "partners": len(bundle["market_partners"]),
        "briefs": len(bundle["briefs"]),
    }
    print(f"wrote {args.output} · {counts}")


if __name__ == "__main__":
    main()
