from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import select

from tastebound_api.db.database import get_session_factory
from tastebound_api.db.tables import Brief, Market, MarketScore, Run
from tastebound_api.errors import AppError, NotFound
from tastebound_api.schemas import DemoResponse
from tastebound_api.settings import API_ROOT

router = APIRouter(prefix="/v1/demo", tags=["demo"])

DEMO_RUN_PATH = API_ROOT / "data/demo/lisbon-run.json"


def _active_run_id() -> str | None:
    active = API_ROOT / "data/demo/active.json"
    if not active.exists():
        return None
    try:
        payload = json.loads(active.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    run_id = payload.get("run_id")
    return str(run_id) if run_id else None


@router.get("", response_model=DemoResponse)
async def demo() -> DemoResponse:
    run_id = _active_run_id()
    if not run_id:
        raise AppError(
            "demo_not_seeded",
            503,
            "Demo not ready",
            "The bundled demo run has not been seeded yet.",
        )
    session_factory = get_session_factory()
    async with session_factory() as session:
        run = await session.get(Run, run_id)
        if run is None:
            raise NotFound("demo run")
        destination_id = run.destination_id
        briefs = (
            (await session.execute(select(Brief).where(Brief.run_id == run.id))).scalars().all()
        )
        top_score = (
            (
                await session.execute(
                    select(MarketScore)
                    .where(MarketScore.run_id == run.id, MarketScore.rank == 1)
                    .limit(1)
                )
            )
            .scalars()
            .first()
        )
        destination_name = ""
        if destination_id:
            from tastebound_api.db.tables import Destination

            destination = await session.get(Destination, destination_id)
            if destination is not None:
                destination_name = destination.name
        top_city = ""
        if top_score is not None:
            market = await session.get(Market, top_score.market_id)
            if market is not None:
                top_city = market.city
    headline = ""
    if briefs:
        headline = str((briefs[0].content or {}).get("title", ""))
    if not headline and top_score is not None:
        headline = f"{top_city} leads on taste fit."
    return DemoResponse(
        run_id=run.id,
        destination=destination_name,
        status=run.status,
        shortlist=list(run.shortlist or []),
        headline=headline,
        sample=True,
    )


def export_path() -> Path | None:
    return DEMO_RUN_PATH if DEMO_RUN_PATH.exists() else None
