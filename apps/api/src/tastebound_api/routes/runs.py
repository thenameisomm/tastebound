from __future__ import annotations

import asyncio
import csv
import io
import json
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from tastebound_api.agent.executor import RunExecutor
from tastebound_api.db.database import get_session_factory
from tastebound_api.db.tables import (
    Allocation,
    ArrivalsDataset,
    Brief,
    Destination,
    LLMCall,
    Market,
    MarketAngle,
    MarketAudience,
    MarketPartner,
    MarketScore,
    ProfileEntity,
    ProfileTag,
    QlooCall,
    Run,
    RunEvent,
    RunMarket,
)
from tastebound_api.errors import AppError, NoMarketData, NotFound, ValidationProblem
from tastebound_api.ratelimit import check, hash_identifier
from tastebound_api.schemas import (
    AllocationRequest,
    AllocationResponse,
    AllocationShareOut,
    AngleEvidence,
    AngleOut,
    AudienceRow,
    BriefOut,
    BriefSectionOut,
    BriefUpdateRequest,
    MarketDetailResponse,
    MarketListResponse,
    MarketOut,
    MarketRow,
    PartnerOut,
    ProfileEntityOut,
    RunCounters,
    RunCreatedResponse,
    RunCreateRequest,
    RunOut,
    RunProfileResponse,
    TraceItem,
    TraceResponse,
)
from tastebound_api.scoring.allocation import AllocationInput, allocate
from tastebound_api.scoring.gap import compute_gap
from tastebound_api.scoring.markets import (
    DEFAULT_THRESHOLDS,
    MarketObservation,
    score_markets,
)
from tastebound_api.security import WorkspaceId
from tastebound_api.settings import DEMO_WORKSPACE_ID, get_settings

router = APIRouter(prefix="/v1/runs", tags=["runs"])
briefs_router = APIRouter(prefix="/v1/briefs", tags=["briefs"])

RUN_TASKS: set[asyncio.Task[None]] = set()

TERMINAL_STATUSES = {"done", "failed", "partial"}


def _spawn(coro: Any) -> None:
    task = asyncio.create_task(coro)
    RUN_TASKS.add(task)
    task.add_done_callback(RUN_TASKS.discard)


def _band_label(band: str) -> str:
    return band.replace("_", " ")


async def _get_run(run_id: str, workspace_id: str) -> Run:
    session_factory = get_session_factory()
    async with session_factory() as session:
        run = await session.get(Run, run_id)
        if run is None or (
            run.workspace_id != workspace_id and run.workspace_id != DEMO_WORKSPACE_ID
        ):
            raise NotFound("run")
    return run


def _require_owner(run: Run, workspace_id: str) -> None:
    if run.workspace_id == DEMO_WORKSPACE_ID and workspace_id != DEMO_WORKSPACE_ID:
        raise AppError(
            "demo_read_only",
            403,
            "Demo is read-only",
            "The bundled demo run cannot be modified. Create your own run to explore.",
        )


def _run_out(run: Run) -> RunOut:
    counters = run.counters or {}
    settings_payload = dict(run.settings or {})
    warnings = settings_payload.pop("warnings", [])
    if not isinstance(warnings, list):
        warnings = []
    return RunOut(
        run_id=run.id,
        status=run.status,
        phase=settings_payload.get("phase"),
        orchestration=run.orchestration,
        orchestration_reason=run.orchestration_reason,
        counters=RunCounters(
            qloo_live=int(counters.get("qloo_live", 0)),
            qloo_cached=int(counters.get("qloo_cached", 0)),
            llm=int(counters.get("llm", 0)),
            tools=int(counters.get("tools", 0)),
        ),
        warnings=warnings,
        shortlist=list(run.shortlist or []),
        settings=settings_payload,
        error_code=run.error_code,
        error_message=run.error_message,
        created_at=run.created_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )


async def _launch_run(run_id: str) -> None:
    executor = RunExecutor(get_session_factory(), get_settings())
    await executor.run(run_id)


@router.post("", response_model=RunCreatedResponse, status_code=202)
async def create_run(
    payload: RunCreateRequest, workspace_id: WorkspaceId, request: Request
) -> RunCreatedResponse:
    settings = get_settings()
    ip_hash = hash_identifier(request.client.host if request.client else "unknown")
    check(
        "runs_ip",
        ip_hash,
        limit=settings.public_runs_per_ip_per_day,
        window_seconds=86400,
    )
    check(
        "runs_workspace",
        workspace_id,
        limit=settings.public_runs_per_ip_per_day,
        window_seconds=86400,
    )
    if len(payload.market_ids) > settings.max_markets_per_run:
        raise ValidationProblem(f"Select at most {settings.max_markets_per_run} markets per run")
    session_factory = get_session_factory()
    async with session_factory() as session:
        destination = await session.get(Destination, payload.destination_id)
        if destination is None or destination.workspace_id != workspace_id:
            raise NotFound("destination")
        markets = (
            (
                await session.execute(
                    select(Market).where(Market.id.in_(payload.market_ids), Market.active.is_(True))
                )
            )
            .scalars()
            .all()
        )
        found_ids = {market.id for market in markets}
        missing = [market_id for market_id in payload.market_ids if market_id not in found_ids]
        if missing:
            raise ValidationProblem(f"Unknown or inactive markets: {', '.join(missing[:5])}")
        if payload.arrivals_dataset_id:
            dataset = await session.get(ArrivalsDataset, payload.arrivals_dataset_id)
            if dataset is None or dataset.workspace_id != workspace_id:
                raise NotFound("arrivals dataset")
        run = Run(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            destination_id=destination.id,
            arrivals_dataset_id=payload.arrivals_dataset_id,
            status="queued",
            settings={},
            counters={},
            shortlist=[],
            client_ip_hash=ip_hash,
        )
        session.add(run)
        for market_id in payload.market_ids:
            session.add(RunMarket(run_id=run.id, market_id=market_id))
        await session.commit()
        run_id = run.id
    _spawn(_launch_run(run_id))
    return RunCreatedResponse(run_id=run_id, status="queued")


@router.get("/{run_id}", response_model=RunOut)
async def get_run(run_id: str, workspace_id: WorkspaceId) -> RunOut:
    run = await _get_run(run_id, workspace_id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        fresh = await session.get(Run, run.id)
    return _run_out(fresh or run)


@router.get("/{run_id}/events")
async def run_events(
    run_id: str,
    workspace_id: WorkspaceId,
    request: Request,
    last_event_id: Annotated[str | None, Query(alias="after")] = None,
) -> StreamingResponse:
    await _get_run(run_id, workspace_id)
    try:
        after = int(last_event_id) if last_event_id else 0
    except ValueError:
        after = 0

    async def stream() -> AsyncIterator[str]:
        nonlocal after
        session_factory = get_session_factory()
        while True:
            if await request.is_disconnected():
                break
            async with session_factory() as session:
                events = (
                    (
                        await session.execute(
                            select(RunEvent)
                            .where(RunEvent.run_id == run_id, RunEvent.seq > after)
                            .order_by(RunEvent.seq)
                        )
                    )
                    .scalars()
                    .all()
                )
                run = await session.get(Run, run_id)
            for event in events:
                after = event.seq
                payload = json.dumps(event.payload, default=str)
                yield f"id: {event.seq}\nevent: {event.type}\ndata: {payload}\n\n"
            if run is None or run.status in TERMINAL_STATUSES:
                if not events:
                    break
                continue
            if not events:
                await asyncio.sleep(0.4)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{run_id}/deep-dive", status_code=202)
async def deep_dive(
    run_id: str,
    workspace_id: WorkspaceId,
    payload: dict[str, list[str]],
) -> dict[str, Any]:
    run = await _get_run(run_id, workspace_id)
    _require_owner(run, workspace_id)
    market_ids = payload.get("market_ids", [])
    settings = get_settings()
    if not 3 <= len(market_ids) <= settings.max_shortlist:
        raise ValidationProblem(f"Pick between 3 and {settings.max_shortlist} shortlisted markets.")
    session_factory = get_session_factory()
    async with session_factory() as session:
        known = {
            row.market_id
            for row in (await session.execute(select(RunMarket).where(RunMarket.run_id == run.id)))
            .scalars()
            .all()
        }
    unknown = [market_id for market_id in market_ids if market_id not in known]
    if unknown:
        raise ValidationProblem(f"Markets not part of this run: {', '.join(unknown[:5])}")

    async def _launch() -> None:
        executor = RunExecutor(session_factory, get_settings())
        await executor.run_deep_dive(run.id, market_ids)

    _spawn(_launch())
    return {"run_id": run.id, "status": "deep_dive", "market_ids": market_ids}


@router.get("/{run_id}/profile", response_model=RunProfileResponse)
async def run_profile(run_id: str, workspace_id: WorkspaceId) -> RunProfileResponse:
    run = await _get_run(run_id, workspace_id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        entities = (
            (
                await session.execute(
                    select(ProfileEntity)
                    .where(ProfileEntity.run_id == run.id)
                    .order_by(ProfileEntity.role, ProfileEntity.name)
                )
            )
            .scalars()
            .all()
        )
        tags = (
            (
                await session.execute(
                    select(ProfileTag)
                    .where(ProfileTag.run_id == run.id)
                    .order_by(ProfileTag.entity_count.desc())
                )
            )
            .scalars()
            .all()
        )
    destination_entity = next((row for row in entities if row.role == "destination"), None)
    if not entities:
        raise NoMarketData()
    warnings = (run.settings or {}).get("warnings", [])
    return RunProfileResponse(
        destination_entity_id=destination_entity.qloo_entity_id if destination_entity else None,
        entities=[
            ProfileEntityOut(
                entity_id=row.qloo_entity_id,
                name=row.name,
                entity_type=row.entity_type,
                role=row.role,
                similarity=row.similarity,
                tags=list(row.tags or []),
            )
            for row in entities
        ],
        tags=[{"id": row.tag_id, "label": row.label, "count": row.entity_count} for row in tags],
        warnings=warnings if isinstance(warnings, list) else [],
    )


async def _market_rows(run: Run) -> list[MarketRow]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        scores = (
            (
                await session.execute(
                    select(MarketScore)
                    .where(MarketScore.run_id == run.id)
                    .order_by(MarketScore.rank.is_(None), MarketScore.rank)
                )
            )
            .scalars()
            .all()
        )
        market_ids = [row.market_id for row in scores]
        markets = {
            market.id: market
            for market in (await session.execute(select(Market).where(Market.id.in_(market_ids))))
            .scalars()
            .all()
        }
        angles = {
            row.market_id: row
            for row in (
                await session.execute(select(MarketAngle).where(MarketAngle.run_id == run.id))
            )
            .scalars()
            .all()
        }
    rows: list[MarketRow] = []
    for score in scores:
        market = markets.get(score.market_id)
        if market is None:
            continue
        angle = angles.get(score.market_id)
        rows.append(
            MarketRow(
                market_id=market.id,
                city=market.city,
                country_code=market.country_code,
                country_name=market.country_name,
                region=market.region,
                rank=score.rank,
                taste_score=score.taste_score,
                lift=score.lift,
                target_affinity=score.target_affinity,
                baseline_affinity=score.baseline_affinity,
                coverage=score.coverage or 0.0,
                confidence=score.confidence or "low",  # type: ignore[arg-type]
                arrivals_share=score.arrivals_share,
                arrivals_pct=score.arrivals_pct,
                gap=score.gap,
                quadrant=score.quadrant,  # type: ignore[arg-type]
                flags=list(score.flags or []),
                angle_headline=angle.headline if angle else score.angle_headline,
                population_band=market.population_band,
            )
        )
    return rows


@router.get("/{run_id}/markets", response_model=MarketListResponse)
async def run_markets(
    run_id: str,
    workspace_id: WorkspaceId,
    region: Annotated[str | None, Query()] = None,
    confidence: Annotated[str | None, Query()] = None,
    quadrant: Annotated[str | None, Query()] = None,
) -> MarketListResponse:
    run = await _get_run(run_id, workspace_id)
    rows = await _market_rows(run)
    if region:
        rows = [row for row in rows if row.region == region]
    if confidence:
        rows = [row for row in rows if row.confidence == confidence]
    if quadrant:
        rows = [row for row in rows if row.quadrant == quadrant]
    settings_payload = dict(run.settings or {})
    thresholds = {
        key: float(value)
        for key, value in (settings_payload.get("thresholds") or DEFAULT_THRESHOLDS).items()
        if isinstance(value, int | float)
    }
    return MarketListResponse(
        markets=rows,
        gap_enabled=bool(settings_payload.get("gap_enabled", False)),
        gap_note=settings_payload.get("gap_note"),
        thresholds=thresholds,
        population_correlation=settings_payload.get("population_correlation"),
        population_suspect=bool(settings_payload.get("population_suspect", False)),
    )


def _partner_out(row: MarketPartner) -> PartnerOut:
    return PartnerOut(
        partner_type=row.partner_type,
        entity_id=row.qloo_entity_id,
        name=row.name,
        lift=row.lift,
        rank=row.rank,
        market_specific=row.market_id is not None,
    )


@router.get("/{run_id}/markets/{market_id}", response_model=MarketDetailResponse)
async def run_market_detail(
    run_id: str, market_id: str, workspace_id: WorkspaceId
) -> MarketDetailResponse:
    run = await _get_run(run_id, workspace_id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        market = await session.get(Market, market_id)
        if market is None:
            raise NotFound("market")
        score = await session.get(MarketScore, {"run_id": run.id, "market_id": market_id})
        if score is None:
            raise NotFound("market score")
        audience = (
            (
                await session.execute(
                    select(MarketAudience)
                    .where(
                        MarketAudience.run_id == run.id,
                        MarketAudience.market_id == market_id,
                    )
                    .order_by(MarketAudience.dimension, MarketAudience.band)
                )
            )
            .scalars()
            .all()
        )
        angle = await session.get(MarketAngle, {"run_id": run.id, "market_id": market_id})
        partners = (
            (
                await session.execute(
                    select(MarketPartner)
                    .where(MarketPartner.run_id == run.id)
                    .order_by(MarketPartner.partner_type, MarketPartner.rank)
                )
            )
            .scalars()
            .all()
        )
        allocation = (
            (
                await session.execute(
                    select(Allocation)
                    .where(Allocation.run_id == run.id)
                    .order_by(Allocation.created_at.desc())
                    .limit(1)
                )
            )
            .scalars()
            .first()
        )
        market_rows = await _market_rows(run)
    score_row = next((row for row in market_rows if row.market_id == market_id), None)
    if score_row is None:
        raise NotFound("market score")
    market_partners = [row for row in partners if row.market_id == market_id]
    brands = [row for row in partners if row.market_id is None and row.partner_type == "brand"]
    partners_by_type: dict[str, list[PartnerOut]] = {}
    for row in market_partners:
        partners_by_type.setdefault(row.partner_type, []).append(_partner_out(row))
    share: float | None = None
    amount: float | None = None
    if allocation is not None:
        for entry in allocation.shares or []:
            if entry.get("market_id") == market_id:
                share = float(entry.get("share", 0.0))
                amount = float(entry.get("amount", 0.0))
                break
    settings_payload = dict(run.settings or {})
    return MarketDetailResponse(
        market=MarketOut(
            id=market.id,
            city=market.city,
            country_code=market.country_code,
            country_name=market.country_name,
            region=market.region,
            lat=market.lat,
            lon=market.lon,
            radius_km=market.radius_km,
            population_band=market.population_band,
            presets=list(market.presets or []),
        ),
        score=score_row,
        audience=[
            AudienceRow(
                dimension=row.dimension,
                band=row.band,
                label=_band_label(row.band),
                share=row.share,
                baseline_share=row.baseline_share,
                over_index=row.over_index,
                source_call_id=row.source_call_id,
            )
            for row in audience
        ],
        audience_note=settings_payload.get("audience_note"),
        angle=AngleOut(
            headline=angle.headline,
            evidence=[
                AngleEvidence(
                    id=str(item.get("id", "")),
                    kind=str(item.get("kind", "")),
                    label=str(item.get("label", "")),
                    value=item.get("value"),
                    source_call_id=item.get("source_call_id"),
                )
                for item in (angle.evidence or [])
            ],
        )
        if angle
        else None,
        partners=partners_by_type,
        brands=[_partner_out(row) for row in brands],
        arrivals_source_note=settings_payload.get("arrivals_source_note"),
        allocation_share=share,
        budget_amount=amount,
    )


@router.post("/{run_id}/allocation", response_model=AllocationResponse)
async def run_allocation(
    run_id: str, workspace_id: WorkspaceId, payload: AllocationRequest
) -> AllocationResponse:
    run = await _get_run(run_id, workspace_id)
    rows = await _market_rows(run)
    shortlist = list(run.shortlist or [])
    if shortlist:
        selected = [row for row in rows if row.market_id in shortlist]
    else:
        selected = [row for row in rows if row.taste_score is not None][:6]
    if not selected:
        raise NoMarketData()
    locks = payload.locks or {}
    items = [
        AllocationInput(
            market_id=row.market_id,
            city=row.city,
            taste_pct=(row.taste_score or 0.0) / 100.0,
            gap=row.gap,
            arrivals_pct=row.arrivals_pct,
            confidence=row.confidence,
            locked=row.market_id in locks,
            locked_amount=locks.get(row.market_id),
        )
        for row in selected
    ]
    lines, _ = allocate(
        items,
        total=payload.total,
        mode=payload.mode,
        minimum_share=payload.minimum_share,
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            Allocation(
                id=str(uuid.uuid4()),
                run_id=run.id,
                workspace_id=workspace_id,
                total=payload.total,
                currency=payload.currency,
                mode=payload.mode,
                shares=[
                    {
                        "market_id": line.market_id,
                        "city": line.city,
                        "share": line.share,
                        "amount": line.amount,
                        "weight": line.weight,
                        "locked": line.locked,
                    }
                    for line in lines
                ],
            )
        )
        await session.commit()
    return AllocationResponse(
        total=payload.total,
        currency=payload.currency,
        mode=payload.mode,
        shares=[
            AllocationShareOut(
                market_id=line.market_id,
                city=line.city,
                share=line.share,
                amount=line.amount,
                weight=line.weight,
                locked=line.locked,
            )
            for line in lines
        ],
    )


@router.post("/{run_id}/rescore", response_model=MarketListResponse)
async def rescore(
    run_id: str,
    workspace_id: WorkspaceId,
    payload: dict[str, float] | None = None,
) -> MarketListResponse:
    run = await _get_run(run_id, workspace_id)
    _require_owner(run, workspace_id)
    thresholds = dict(DEFAULT_THRESHOLDS)
    if payload:
        for key in thresholds:
            if key in payload:
                thresholds[key] = float(payload[key])
    session_factory = get_session_factory()
    async with session_factory() as session:
        scores = (
            (await session.execute(select(MarketScore).where(MarketScore.run_id == run.id)))
            .scalars()
            .all()
        )
        markets = {
            market.id: market
            for market in (
                await session.execute(
                    select(Market).where(Market.id.in_([row.market_id for row in scores]))
                )
            )
            .scalars()
            .all()
        }
        observations = [
            MarketObservation(
                market_id=row.market_id,
                target_affinity=row.target_affinity,
                baseline_affinity=row.baseline_affinity,
                contribution_count=len(row.contributions or []),
                population_band=(
                    markets[row.market_id].population_band if row.market_id in markets else 1
                ),
                source_call_ids=list(row.source_call_ids or []),
                contributions=list(row.contributions or []),
            )
            for row in scores
            if row.market_id in markets
        ]
        if not observations:
            raise NoMarketData()
        rescored = score_markets(observations, thin_coverage=thresholds["thin_coverage"])
        arrivals = {
            row.market_id: (row.arrivals_share, row.arrivals_pct)
            for row in scores
            if row.arrivals_share is not None
        }
        if arrivals:
            gap_results = compute_gap(
                rescored,
                {
                    market_id: round(share * 1_000_000)
                    for market_id, (share, _) in arrivals.items()
                    if share is not None
                },
                taste_threshold=thresholds["gap_taste"],
                arrivals_threshold=thresholds["gap_arrivals"],
            )
        else:
            gap_results = {}
        by_id = {row.market_id: row for row in scores}
        for row in rescored:
            target = by_id.get(row.market_id)
            if target is None:
                continue
            target.taste_score = row.taste_score
            target.rank = row.rank
            target.flags = list(row.flags)
            target.confidence = row.confidence
            if row.market_id in gap_results:
                result = gap_results[row.market_id]
                target.gap = result.gap
                target.quadrant = result.quadrant
        settings_payload = dict(run.settings or {})
        settings_payload["thresholds"] = thresholds
        rows = await session.execute(select(Run).where(Run.id == run.id))
        run_row = rows.scalars().first()
        if run_row is not None:
            run_row.settings = settings_payload
        await session.commit()
    fresh = await _get_run(run_id, workspace_id)
    return MarketListResponse(
        markets=await _market_rows(fresh),
        gap_enabled=bool((fresh.settings or {}).get("gap_enabled", False)),
        gap_note=(fresh.settings or {}).get("gap_note"),
        thresholds=thresholds,
        population_correlation=(fresh.settings or {}).get("population_correlation"),
        population_suspect=bool((fresh.settings or {}).get("population_suspect", False)),
    )


@router.get("/{run_id}/briefs", response_model=list[BriefOut])
async def list_briefs(run_id: str, workspace_id: WorkspaceId) -> list[BriefOut]:
    run = await _get_run(run_id, workspace_id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        briefs = (
            (
                await session.execute(
                    select(Brief).where(Brief.run_id == run.id).order_by(Brief.market_id)
                )
            )
            .scalars()
            .all()
        )
        markets = {
            market.id: market
            for market in (
                await session.execute(
                    select(Market).where(Market.id.in_([row.market_id for row in briefs]))
                )
            )
            .scalars()
            .all()
        }
    return [_brief_out(row, markets.get(row.market_id)) for row in briefs]


def _brief_out(row: Brief, market: Market | None) -> BriefOut:
    content = dict(row.content or {})
    sections = content.get("sections", [])
    return BriefOut(
        id=row.id,
        market_id=row.market_id,
        city=market.city if market else row.market_id,
        source=row.source,
        edited=row.edited,
        model=row.model,
        title=str(content.get("title", "")),
        summary=str(content.get("summary", "")),
        sections=[
            BriefSectionOut(
                heading=str(section.get("heading", "")),
                body=str(section.get("body", "")),
                cited_evidence_ids=[str(item) for item in section.get("cited_evidence_ids", [])],
            )
            for section in sections
            if isinstance(section, dict)
        ],
        evidence_ids=[str(item) for item in content.get("evidence_ids", [])],
    )


@briefs_router.patch("/{brief_id}", response_model=BriefOut)
async def update_brief(
    brief_id: str, workspace_id: WorkspaceId, payload: BriefUpdateRequest
) -> BriefOut:
    session_factory = get_session_factory()
    async with session_factory() as session:
        brief = await session.get(Brief, brief_id)
        if brief is None or (
            brief.workspace_id != workspace_id and brief.workspace_id != DEMO_WORKSPACE_ID
        ):
            raise NotFound("brief")
        if brief.workspace_id == DEMO_WORKSPACE_ID and workspace_id != DEMO_WORKSPACE_ID:
            raise AppError(
                "demo_read_only",
                403,
                "Demo is read-only",
                "Briefs in the bundled demo cannot be edited.",
            )
        content = dict(brief.content or {})
        if payload.title is not None:
            content["title"] = payload.title
        if payload.summary is not None:
            content["summary"] = payload.summary
        if payload.sections is not None:
            content["sections"] = [
                {
                    "heading": section.heading,
                    "body": section.body,
                    "cited_evidence_ids": section.cited_evidence_ids,
                }
                for section in payload.sections
            ]
        brief.content = content
        brief.edited = True
        await session.commit()
        market = await session.get(Market, brief.market_id)
    return _brief_out(brief, market)


@briefs_router.get("/{brief_id}/export.md")
async def export_brief_markdown(brief_id: str, workspace_id: WorkspaceId) -> Response:
    session_factory = get_session_factory()
    async with session_factory() as session:
        brief = await session.get(Brief, brief_id)
        if brief is None or (
            brief.workspace_id != workspace_id and brief.workspace_id != DEMO_WORKSPACE_ID
        ):
            raise NotFound("brief")
        market = await session.get(Market, brief.market_id)
    out = _brief_out(brief, market)
    lines = [f"# {out.title}", "", out.summary, ""]
    for section in out.sections:
        lines.extend([f"## {section.heading}", "", section.body, ""])
    lines.append(
        f"_Evidence ids: {', '.join(out.evidence_ids)}. Source: {out.source}"
        + (
            f" (edited, model {out.model})"
            if out.edited and out.model
            else " (edited)"
            if out.edited
            else f", model {out.model}"
        )
        + "._"
    )
    return Response(
        "\n".join(lines),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="brief-{out.market_id}.md"'},
    )


@router.get("/{run_id}/export.csv")
async def export_csv(run_id: str, workspace_id: WorkspaceId) -> Response:
    run = await _get_run(run_id, workspace_id)
    rows = await _market_rows(run)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "market_id",
            "city",
            "country_code",
            "region",
            "rank",
            "taste_score",
            "lift",
            "coverage",
            "confidence",
            "arrivals_share",
            "gap",
            "quadrant",
            "angle_headline",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.market_id,
                row.city,
                row.country_code,
                row.region,
                row.rank if row.rank is not None else "",
                row.taste_score if row.taste_score is not None else "",
                row.lift if row.lift is not None else "",
                row.coverage,
                row.confidence,
                row.arrivals_share if row.arrivals_share is not None else "",
                row.gap if row.gap is not None else "",
                row.quadrant or "",
                row.angle_headline or "",
            ]
        )
    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="tastebound-{run.id}.csv"'},
    )


@router.get("/{run_id}/trace", response_model=TraceResponse)
async def run_trace(
    run_id: str,
    workspace_id: WorkspaceId,
    kind: Annotated[str | None, Query()] = None,
) -> TraceResponse:
    run = await _get_run(run_id, workspace_id)
    if kind not in {None, "qloo", "llm", "tool"}:
        raise ValidationProblem("kind must be qloo, llm or tool")
    session_factory = get_session_factory()
    items: list[TraceItem] = []
    async with session_factory() as session:
        if kind in {None, "qloo"}:
            calls = (
                (
                    await session.execute(
                        select(QlooCall)
                        .where(QlooCall.run_id == run.id)
                        .order_by(QlooCall.created_at)
                    )
                )
                .scalars()
                .all()
            )
            for call in calls:
                items.append(
                    TraceItem(
                        kind="qloo",
                        at=call.created_at,
                        step=call.step,
                        summary=(
                            f"{call.endpoint} "
                            f"{'cache hit' if call.cache_hit else 'live'} "
                            f"status {call.status} · {call.duration_ms} ms"
                        ),
                        detail={
                            "call_id": call.id,
                            "endpoint": call.endpoint,
                            "params": call.params,
                            "cache_key": call.cache_key,
                            "cache_hit": call.cache_hit,
                            "status": call.status,
                            "duration_ms": call.duration_ms,
                            "result_count": call.result_count,
                            "warnings": call.warnings,
                        },
                    )
                )
        if kind in {None, "llm"}:
            llm_calls = (
                (
                    await session.execute(
                        select(LLMCall).where(LLMCall.run_id == run.id).order_by(LLMCall.created_at)
                    )
                )
                .scalars()
                .all()
            )
            for llm_call in llm_calls:
                summary = (
                    f"{llm_call.provider}/{llm_call.model} "
                    f"{llm_call.status} · {llm_call.duration_ms} ms"
                )
                items.append(
                    TraceItem(
                        kind="llm",
                        at=llm_call.created_at,
                        step=llm_call.purpose,
                        summary=summary,
                        detail={
                            "call_id": llm_call.id,
                            "provider": llm_call.provider,
                            "model": llm_call.model,
                            "prompt_version": llm_call.prompt_version,
                            "status": llm_call.status,
                            "input_tokens": llm_call.input_tokens,
                            "output_tokens": llm_call.output_tokens,
                        },
                    )
                )
        if kind in {None, "tool"}:
            events = (
                (
                    await session.execute(
                        select(RunEvent)
                        .where(RunEvent.run_id == run.id, RunEvent.type == "tool_call")
                        .order_by(RunEvent.seq)
                    )
                )
                .scalars()
                .all()
            )
            for event in events:
                payload = dict(event.payload or {})
                items.append(
                    TraceItem(
                        kind="tool",
                        at=event.created_at,
                        step=str(payload.get("tool", "")),
                        summary=f"{payload.get('tool', '')} {payload.get('args_summary', '')}",
                        detail=payload,
                    )
                )
    items.sort(key=lambda item: item.at)
    return TraceResponse(items=items)
