from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from tastebound_api.db.database import get_session_factory
from tastebound_api.db.tables import Market
from tastebound_api.schemas import MarketOut, MarketsResponse, PresetOut
from tastebound_api.security import WorkspaceId
from tastebound_api.settings import API_ROOT

router = APIRouter(prefix="/v1/markets", tags=["markets"])


def _load_presets() -> dict[str, str]:
    path = API_ROOT / "src/tastebound_api/data/markets.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    presets = payload.get("presets", {})
    if not isinstance(presets, dict):
        return {}
    return {str(key): str(value) for key, value in presets.items()}


@router.get("", response_model=MarketsResponse)
async def list_markets(
    workspace_id: WorkspaceId,
    region: Annotated[str | None, Query()] = None,
) -> MarketsResponse:
    session_factory = get_session_factory()
    async with session_factory() as session:
        statement = (
            select(Market)
            .where(Market.active.is_(True))
            .order_by(Market.population_band.desc(), Market.city)
        )
        if region:
            statement = statement.where(Market.region == region)
        rows = (await session.execute(statement)).scalars().all()

    presets_map = _load_presets()
    preset_ids: dict[str, list[str]] = {preset_id: [] for preset_id in presets_map}
    markets: list[MarketOut] = []
    for row in rows:
        markets.append(
            MarketOut(
                id=row.id,
                city=row.city,
                country_code=row.country_code,
                country_name=row.country_name,
                region=row.region,
                lat=row.lat,
                lon=row.lon,
                radius_km=row.radius_km,
                population_band=row.population_band,
                presets=list(row.presets or []),
            )
        )
        for preset_id in row.presets or []:
            preset_ids.setdefault(preset_id, []).append(row.id)

    presets = [
        PresetOut(id=preset_id, label=label, market_ids=preset_ids.get(preset_id, []))
        for preset_id, label in presets_map.items()
    ]
    return MarketsResponse(markets=markets, presets=presets)
