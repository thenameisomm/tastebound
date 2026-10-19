from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile
from sqlalchemy import select

from tastebound_api.arrivals.matching import MarketRef, match_arrivals
from tastebound_api.arrivals.parser import parse_arrivals_csv
from tastebound_api.db.database import get_session_factory
from tastebound_api.db.tables import ArrivalsDataset, ArrivalsRow, Market
from tastebound_api.errors import ArrivalsInvalid, NotFound
from tastebound_api.ratelimit import check, hash_identifier
from tastebound_api.schemas import (
    ArrivalsResponse,
    ArrivalsRowErrorOut,
    ArrivalsSampleOut,
)
from tastebound_api.security import WorkspaceId
from tastebound_api.settings import API_ROOT

router = APIRouter(prefix="/v1/arrivals", tags=["arrivals"])

SAMPLES_DIR = API_ROOT / "src/tastebound_api/data/samples"
MAX_UPLOAD_BYTES = 1_000_000


def _market_refs(markets: Sequence[Market]) -> list[MarketRef]:
    return [
        MarketRef(
            id=market.id,
            city=market.city,
            country_code=market.country_code,
            country_name=market.country_name,
            population_band=market.population_band,
        )
        for market in markets
    ]


@router.get("/samples", response_model=list[ArrivalsSampleOut])
async def list_samples(workspace_id: WorkspaceId) -> list[ArrivalsSampleOut]:
    samples: list[ArrivalsSampleOut] = []
    if not SAMPLES_DIR.exists():
        return samples
    for path in sorted(SAMPLES_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        stem = path.stem
        year = payload.get("year")
        samples.append(
            ArrivalsSampleOut(
                id=stem,
                name=stem.replace("-", " ").title(),
                year=int(year) if year else None,
                source_name=str(payload.get("source_name", "Unknown source")),
                source_url=str(payload.get("url", "")),
                level=str(payload.get("level", "country")),
                notes=str(payload.get("notes", "")),
            )
        )
    return samples


@router.post("", response_model=ArrivalsResponse, status_code=201)
async def upload_arrivals(
    workspace_id: WorkspaceId,
    request: Request,
    file: Annotated[UploadFile, File()],
    source_note: Annotated[str, Form(min_length=3, max_length=500)],
    name: Annotated[str | None, Form()] = None,
    destination_id: Annotated[str | None, Form()] = None,
    sample_id: Annotated[str | None, Form()] = None,
) -> ArrivalsResponse:
    check(
        "arrivals_upload",
        hash_identifier(request.client.host if request.client else "unknown"),
        limit=20,
        window_seconds=3600,
    )
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise ArrivalsInvalid("The file is larger than the 1 MB limit.")
    parsed = parse_arrivals_csv(content)

    session_factory = get_session_factory()
    async with session_factory() as session:
        markets = (
            (await session.execute(select(Market).where(Market.active.is_(True)))).scalars().all()
        )
        matched = match_arrivals(parsed.rows, _market_refs(markets))
        dataset = ArrivalsDataset(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            destination_id=destination_id,
            name=name or (file.filename or "Uploaded arrivals"),
            year=max((row.year or 0 for row in parsed.rows), default=0) or None,
            level="city" if not matched.by_country else "mixed",
            source_note=source_note,
            is_sample=bool(sample_id),
        )
        session.add(dataset)
        for row in parsed.rows:
            session.add(
                ArrivalsRow(
                    dataset_id=dataset.id,
                    origin_raw=row.origin_raw,
                    arrivals=row.arrivals,
                    year=row.year,
                )
            )
        await session.commit()
        dataset_id = dataset.id

    response = ArrivalsResponse(
        dataset_id=dataset_id,
        name=name or (file.filename or "Uploaded arrivals"),
        level="city" if not matched.by_country else "mixed",
        source_note=source_note,
        is_sample=bool(sample_id),
        rows=len(parsed.rows),
        matched_markets=matched.matched_market_count,
        matched_countries=sorted(matched.by_country.keys()),
        errors=[
            ArrivalsRowErrorOut(line=error.line, message=error.message) for error in parsed.errors
        ],
        unmatched=list(matched.unmatched_rows),
        notes=list(matched.notes),
    )
    return response


@router.get("/{dataset_id}", response_model=ArrivalsResponse)
async def get_arrivals(dataset_id: str, workspace_id: WorkspaceId) -> ArrivalsResponse:
    session_factory = get_session_factory()
    async with session_factory() as session:
        dataset = await session.get(ArrivalsDataset, dataset_id)
        if dataset is None or dataset.workspace_id != workspace_id:
            raise NotFound("arrivals dataset")
        rows = (
            (await session.execute(select(ArrivalsRow).where(ArrivalsRow.dataset_id == dataset_id)))
            .scalars()
            .all()
        )
    matched_markets = {row.matched_market_id for row in rows if row.matched_market_id}
    matched_countries = {row.matched_country for row in rows if row.matched_country}
    return ArrivalsResponse(
        dataset_id=dataset.id,
        name=dataset.name,
        level=dataset.level,
        source_note=dataset.source_note,
        is_sample=dataset.is_sample,
        rows=len(rows),
        matched_markets=len(matched_markets),
        matched_countries=sorted(matched_countries),
        errors=[],
        unmatched=[],
        notes=[],
    )
