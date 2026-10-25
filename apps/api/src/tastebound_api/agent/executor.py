from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tastebound_api.arrivals.matching import MarketRef, match_arrivals
from tastebound_api.db.tables import (
    ArrivalsDataset,
    ArrivalsRow,
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
    Run,
    RunEvent,
    RunMarket,
    SignatureItem,
)
from tastebound_api.errors import (
    AppError,
    LLMError,
    NoMarketData,
    ProfileTooThin,
    QlooAuthError,
    QlooBudgetExceeded,
    QlooError,
    QlooUnconfigured,
)
from tastebound_api.grounding import (
    BriefContent,
    build_bundle,
    validate_brief,
)
from tastebound_api.llm.base import ChatMessage, LLMProvider
from tastebound_api.llm.prompts import PROMPT_VERSION, load_prompt
from tastebound_api.llm.provider import get_provider
from tastebound_api.qloo.client import QlooClient
from tastebound_api.qloo.service import (
    DestinationMatch,
    ProfileBuild,
    QlooService,
    ResolvedItem,
)
from tastebound_api.scoring.gap import compute_gap
from tastebound_api.scoring.markets import (
    DEFAULT_THRESHOLDS,
    SCORING_VERSION,
    MarketObservation,
    ScoredMarket,
    population_correlation,
    score_markets,
)
from tastebound_api.settings import Settings, get_settings

logger = logging.getLogger("tastebound.agent")


@dataclass
class RunContext:
    run: Run
    destination: Destination
    items: list[SignatureItem] = field(default_factory=list)
    market_ids: list[str] = field(default_factory=list)
    arrivals_dataset: ArrivalsDataset | None = None
    destination_match: DestinationMatch | None = None
    profile: ProfileBuild | None = None
    observations: list[MarketObservation] = field(default_factory=list)
    scored: list[ScoredMarket] = field(default_factory=list)
    shortlist: list[str] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)


def _now() -> datetime:
    return datetime.now(UTC)


def _band_label(band: str) -> str:
    return band.replace("_", " ")


def _extract_json(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


# --- database retry helper ---
async def _with_retry(
    session_factory: async_sessionmaker[AsyncSession],
    operation: Callable[[AsyncSession], Awaitable[Any]],
    max_retries: int = 5,
    base_delay: float = 0.2,
) -> Any:
    """Execute a database operation with retry on OperationalError (e.g., SQLite locked)."""
    for attempt in range(max_retries):
        async with session_factory() as session:
            try:
                return await operation(session)
            except OperationalError as exc:
                if "locked" in str(exc).lower() and attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2**attempt))
                    continue
                raise


class RunExecutor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings | None = None,
        provider: LLMProvider | None = None,
        qloo_client: QlooClient | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings or get_settings()
        self.provider = provider if provider is not None else get_provider(self.settings)
        self.context: RunContext | None = None
        self.service: QlooService | None = None
        self.counters = {
            "qloo_live": 0,
            "qloo_cached": 0,
            "llm": 0,
            "tools": 0,
        }
        self._qloo_client = qloo_client
        self._owns_client = qloo_client is None

    # ------------------------------------------------------------- plumbing

    async def _emit(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        async def _op(session: AsyncSession) -> None:
            current = await session.scalar(
                select(func.max(RunEvent.seq)).where(RunEvent.run_id == run_id)
            )
            seq = int(current or 0) + 1
            session.add(
                RunEvent(
                    run_id=run_id,
                    seq=seq,
                    type=event_type,
                    payload=payload,
                )
            )
            await session.commit()

        await _with_retry(self.session_factory, _op)

    async def _save_counters(self, run_id: str) -> None:
        async def _op(session: AsyncSession) -> None:
            row = await session.get(Run, run_id)
            if row is not None:
                row.counters = dict(self.counters)
                await session.commit()

        await _with_retry(self.session_factory, _op)

    async def _set_status(self, run_id: str, status: str) -> None:
        async def _op(session: AsyncSession) -> None:
            row = await session.get(Run, run_id)
            if row is not None:
                row.status = status
                if status != "failed":
                    row.error_code = None
                    row.error_message = None
                if status == "scoring" and row.started_at is None:
                    row.started_at = _now()
                if status == "done":
                    row.finished_at = _now()
                await session.commit()

        await _with_retry(self.session_factory, _op)

    async def _add_warning(self, run_id: str, code: str, message: str) -> None:
        context = self.context
        if context is not None:
            context.warnings.append({"code": code, "message": message})

            async def _op(session: AsyncSession) -> None:
                row = await session.get(Run, run_id)
                if row is not None:
                    settings = dict(row.settings or {})
                    settings["warnings"] = context.warnings
                    row.settings = settings
                    await session.commit()

            await _with_retry(self.session_factory, _op)
        await self._emit(run_id, "warning", {"code": code, "message": message})

    def _qloo_sink(self, run_id: str) -> Callable[[str, dict[str, Any]], Awaitable[None]]:
        async def sink(event_type: str, payload: dict[str, Any]) -> None:
            if event_type == "qloo_call":
                if payload.get("cache_hit"):
                    self.counters["qloo_cached"] += 1
                else:
                    self.counters["qloo_live"] += 1
            await self._emit(run_id, event_type, payload)

        return sink

    # ---------------------------------------------------------------- run

    async def run(self, run_id: str) -> None:
        try:
            context = await self._load_context(run_id)
        except AppError as exc:
            await self._fail(run_id, exc)
            return
        self.context = context
        client = self._qloo_client or QlooClient(
            self.session_factory,
            self.settings,
            event_sink=self._qloo_sink(run_id),
        )
        self.service = QlooService(client)
        try:
            await self._execute(run_id)
            await self._set_status(run_id, "done")
            await self._emit(
                run_id, "phase_done", {"phase": "deep_dive", "summary": "Run complete."}
            )
        except QlooBudgetExceeded as exc:
            await self._add_warning(run_id, "qloo_budget_exceeded", str(exc))
            await self._set_status(run_id, "partial")
            await self._emit(run_id, "phase_done", {"phase": "partial", "summary": str(exc)})
        except AppError as exc:
            await self._fail(run_id, exc)
        except Exception as exc:
            logger.exception("run %s failed", run_id)
            await self._fail(
                run_id,
                AppError("internal_error", 500, "Run failed", f"{type(exc).__name__}: {exc}"),
            )
        finally:
            if self._owns_client:
                await client.aclose()

    async def run_deep_dive(self, run_id: str, market_ids: list[str]) -> None:
        try:
            context = await self._load_context(run_id)
        except AppError as exc:
            await self._fail(run_id, exc)
            return
        context.shortlist = list(market_ids)
        self.context = context
        client = self._qloo_client or QlooClient(
            self.session_factory,
            self.settings,
            event_sink=self._qloo_sink(run_id),
        )
        self.service = QlooService(client)
        try:
            await self._set_status(run_id, "deep_dive")
            await self._emit(
                run_id,
                "phase_started",
                {"phase": "deep_dive", "orchestration": "deterministic_fallback"},
            )
            await self._run_deep_dive_tools(run_id, list(market_ids))
            async with self.session_factory() as session:
                row = await session.get(Run, run_id)
                if row is not None:
                    row.shortlist = list(market_ids)
                    await session.commit()
            await self._set_status(run_id, "done")
            await self._emit(
                run_id, "phase_done", {"phase": "deep_dive", "summary": "Deep dive complete."}
            )
        except QlooBudgetExceeded as exc:
            await self._add_warning(run_id, "qloo_budget_exceeded", str(exc))
            await self._set_status(run_id, "partial")
            await self._emit(run_id, "phase_done", {"phase": "partial", "summary": str(exc)})
        except AppError as exc:
            await self._fail(run_id, exc)
        except Exception as exc:
            logger.exception("deep dive %s failed", run_id)
            await self._fail(
                run_id,
                AppError("internal_error", 500, "Deep dive failed", f"{type(exc).__name__}: {exc}"),
            )
        finally:
            if self._owns_client:
                await client.aclose()

    async def _run_deep_dive_tools(self, run_id: str, shortlist: list[str]) -> None:
        await self._tool(
            run_id,
            "market_audience",
            {"market_ids": shortlist},
            lambda: self.tool_market_audience(shortlist),
        )
        await self._tool(
            run_id,
            "market_angles",
            {"market_ids": shortlist},
            lambda: self.tool_market_angles(shortlist),
        )
        await self._tool(
            run_id,
            "media_partners",
            {"market_ids": shortlist},
            lambda: self.tool_media_partners(shortlist),
        )
        await self._tool(
            run_id,
            "write_briefs",
            {"market_ids": shortlist},
            lambda: self.tool_write_briefs(shortlist),
        )
        await self._tool(
            run_id, "finish_phase", {"summary": "Deep dive complete."}, self.tool_finish_phase
        )

    async def _load_context(self, run_id: str) -> RunContext:
        async with self.session_factory() as session:
            run = await session.get(Run, run_id)
            if run is None:
                raise AppError("not_found", 404, "Run not found", f"Run {run_id} does not exist.")
            destination = await session.get(Destination, run.destination_id)
            if destination is None:
                raise AppError(
                    "not_found", 404, "Destination not found", "The destination was deleted."
                )
            items = (
                (
                    await session.execute(
                        select(SignatureItem)
                        .where(SignatureItem.destination_id == destination.id)
                        .order_by(SignatureItem.position)
                    )
                )
                .scalars()
                .all()
            )
            market_ids = (
                (
                    await session.execute(
                        select(Market.id)
                        .join(RunMarket, RunMarket.market_id == Market.id)
                        .where(RunMarket.run_id == run_id)
                        .order_by(Market.region, Market.population_band.desc())
                    )
                )
                .scalars()
                .all()
            )
            arrivals_dataset = None
            if run.arrivals_dataset_id:
                arrivals_dataset = await session.get(ArrivalsDataset, run.arrivals_dataset_id)
            self.counters = {
                **self.counters,
                **(run.counters or {}),
            }
            return RunContext(
                run=run,
                destination=destination,
                items=list(items),
                market_ids=list(market_ids),
                arrivals_dataset=arrivals_dataset,
            )

    async def _fail(self, run_id: str, exc: AppError) -> None:
        async with self.session_factory() as session:
            row = await session.get(Run, run_id)
            if row is not None:
                row.status = "failed"
                row.error_code = exc.code
                row.error_message = exc.detail
                row.finished_at = _now()
                await session.commit()
        await self._emit(run_id, "failed", {"code": exc.code, "message": exc.detail})

    # ------------------------------------------------------------ phases

    async def _execute(self, run_id: str) -> None:
        await self._set_status(run_id, "scoring")
        await self._emit(
            run_id, "phase_started", {"phase": "scoring", "orchestration": "deterministic_fallback"}
        )
        await self._tool(run_id, "build_profile", {}, self.tool_build_profile)
        await self._tool(run_id, "score_markets", {}, self.tool_score_markets)
        await self._set_status(run_id, "scored")
        await self._tool(run_id, "compute_gaps", {}, self.tool_compute_gaps)
        await self._tool(
            run_id, "finish_phase", {"summary": "Scoring complete."}, self.tool_finish_phase
        )
        await self._set_status(run_id, "deep_dive")
        await self._emit(
            run_id,
            "phase_started",
            {"phase": "deep_dive", "orchestration": "deterministic_fallback"},
        )
        shortlist = self.context.shortlist if self.context else []
        if not shortlist and self.context:
            shortlist = self.context.market_ids[: self.settings.max_shortlist]
        await self._run_deep_dive_tools(run_id, shortlist)

    async def _tool(
        self, run_id: str, name: str, arguments: dict[str, Any], handler: Any
    ) -> dict[str, Any]:
        await self._emit(run_id, "tool_call", {"tool": name, "args_summary": arguments})
        started = time.monotonic()
        summary: dict[str, Any] = await handler()
        self.counters["tools"] += 1
        await self._save_counters(run_id)
        await self._emit(
            run_id,
            "step_done",
            {
                "tool": name,
                "summary": summary,
                "duration_ms": int((time.monotonic() - started) * 1000),
            },
        )
        return summary

    # ------------------------------------------------------------- tools

    async def tool_build_profile(self) -> dict[str, Any]:
        assert self.context is not None and self.service is not None
        context = self.context
        run = context.run
        destination = context.destination
        match = await self.service.resolve_destination(
            destination.name,
            country_code=destination.country_code,
            run_id=run.id,
            step="destination_search",
        )
        context.destination_match = match
        async with self.session_factory() as session:
            row = await session.get(Destination, destination.id)
            if row is not None:
                row.qloo_entity_id = match.entity_id
                row.lat = match.lat
                row.lon = match.lon
                await session.commit()

        resolved: list[ResolvedItem] = []
        for index, signature_item in enumerate(context.items):
            resolved_item = await self.service.resolve_item(
                item_id=signature_item.id,
                name=signature_item.name,
                kind=signature_item.kind,
                destination=match,
                run_id=run.id,
                position=index,
            )
            resolved.append(resolved_item)
        profile = self.service.build_profile(destination=match, resolved_items=resolved)
        context.profile = profile
        if profile.resolved_count < 3:
            raise ProfileTooThin()
        async with self.session_factory() as session:
            await session.execute(delete(ProfileEntity).where(ProfileEntity.run_id == run.id))
            await session.execute(delete(ProfileTag).where(ProfileTag.run_id == run.id))
            session.add(
                ProfileEntity(
                    id=str(uuid.uuid4()),
                    run_id=run.id,
                    item_id=None,
                    qloo_entity_id=match.entity_id,
                    name=match.name,
                    entity_type=match.entity_type or "destination",
                    role="destination",
                    similarity=1.0,
                    source_call_id=match.call_id,
                    tags=match.tags,
                )
            )
            seen_entity_ids = {match.entity_id}
            for resolved_item in profile.entities:
                if (
                    resolved_item.status != "resolved"
                    or not resolved_item.entity_id
                    or resolved_item.entity_id in seen_entity_ids
                ):
                    continue
                seen_entity_ids.add(resolved_item.entity_id)
                session.add(
                    ProfileEntity(
                        id=str(uuid.uuid4()),
                        run_id=run.id,
                        item_id=resolved_item.item_id,
                        qloo_entity_id=resolved_item.entity_id,
                        name=resolved_item.entity_name or resolved_item.name,
                        entity_type=resolved_item.entity_type or "place",
                        role="item",
                        similarity=resolved_item.similarity,
                        source_call_id=resolved_item.call_id,
                        tags=resolved_item.tags,
                    )
                )
            for tag in profile.tags:
                session.add(
                    ProfileTag(
                        run_id=run.id,
                        tag_id=tag["id"],
                        label=tag["label"],
                        entity_count=int(tag["count"]),
                    )
                )
            run_row = await session.get(Run, run.id)
            if run_row is not None:
                run_row.settings = {
                    **(run_row.settings or {}),
                    "scoring_version": SCORING_VERSION,
                    "thresholds": DEFAULT_THRESHOLDS,
                }
                run_row.counters = dict(self.counters)
            await session.commit()
        return {
            "destination": match.name,
            "resolved": profile.resolved_count,
            "unresolved": profile.unresolved,
            "tags": [tag["label"] for tag in profile.tags[:5]],
        }

    async def _profile_signal_ids(self) -> list[str]:
        assert self.context is not None
        destination_match = self.context.destination_match
        destination_id = destination_match.entity_id if destination_match else None
        if self.context.profile is not None:
            return [
                item.entity_id
                for item in self.context.profile.entities
                if item.entity_id and (destination_id is None or item.entity_id != destination_id)
            ]
        async with self.session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(ProfileEntity).where(
                            ProfileEntity.run_id == self.context.run.id,
                            ProfileEntity.role == "item",
                        )
                    )
                )
                .scalars()
                .all()
            )
        return [
            row.qloo_entity_id
            for row in rows
            if destination_id is None or row.qloo_entity_id != destination_id
        ]

    async def tool_score_markets(self) -> dict[str, Any]:
        assert self.context is not None and self.service is not None
        context = self.context
        run = context.run
        destination_match = context.destination_match
        assert destination_match is not None
        signal_ids = await self._profile_signal_ids()
        observations: list[MarketObservation] = []
        async with self.session_factory() as session:
            markets = {
                market.id: market
                for market in (
                    await session.execute(select(Market).where(Market.id.in_(context.market_ids)))
                )
                .scalars()
                .all()
            }
        for market_id in context.market_ids:
            market = markets.get(market_id)
            if market is None:
                continue
            try:
                insight = await self.service.destination_insight(
                    destination=destination_match,
                    profile_entity_ids=signal_ids,
                    market_lat=market.lat,
                    market_lon=market.lon,
                    run_id=run.id,
                    step=f"score_{market_id}",
                )
            except QlooBudgetExceeded:
                raise
            except (QlooAuthError, QlooUnconfigured):
                raise
            except QlooError as exc:
                await self._add_warning(run.id, "market_excluded", f"{market.city}: {exc.detail}")
                continue
            observations.append(
                MarketObservation(
                    market_id=market_id,
                    target_affinity=insight.affinity,
                    baseline_affinity=insight.baseline_affinity,
                    contribution_count=len(insight.contributions),
                    population_band=market.population_band,
                    source_call_ids=insight.call_ids,
                    warnings=insight.warnings,
                    contributions=insight.contributions,
                )
            )
            context.observations = observations
        if not observations:
            raise NoMarketData()
        scored = score_markets(observations)
        correlation = population_correlation(scored)
        context.scored = scored
        valid = [row for row in scored if row.taste_score is not None]
        if not valid:
            raise NoMarketData()
        shortlist = [
            row.market_id for row in valid[: min(self.settings.max_shortlist, max(3, len(valid)))]
        ]
        context.shortlist = shortlist
        population_suspect = bool(
            correlation is not None
            and abs(correlation) >= DEFAULT_THRESHOLDS["population_correlation"]
        )
        async with self.session_factory() as session:
            await session.execute(delete(MarketScore).where(MarketScore.run_id == run.id))
            for row in scored:
                session.add(
                    MarketScore(
                        run_id=run.id,
                        market_id=row.market_id,
                        target_affinity=row.target_affinity,
                        baseline_affinity=row.baseline_affinity,
                        target_pct=row.target_pct,
                        baseline_pct=row.baseline_pct,
                        lift=row.lift,
                        taste_score=row.taste_score,
                        coverage=row.coverage,
                        confidence=row.confidence,
                        flags=row.flags,
                        rank=row.rank,
                        source_call_ids=row.source_call_ids,
                        contributions=self._contributions_for(row.market_id),
                    )
                )
            run_row = await session.get(Run, run.id)
            if run_row is not None:
                settings = dict(run_row.settings or {})
                settings["population_correlation"] = correlation
                settings["population_suspect"] = population_suspect
                run_row.settings = settings
                run_row.shortlist = shortlist
                run_row.counters = dict(self.counters)
            await session.commit()
        return {
            "scored": len(scored),
            "shortlist": shortlist,
            "population_correlation": correlation,
            "population_suspect": population_suspect,
        }

    def _contributions_for(self, market_id: str) -> list[dict[str, Any]]:
        if self.context is None:
            return []
        observation = next(
            (row for row in self.context.observations if row.market_id == market_id), None
        )
        return observation.contributions if observation is not None else []

    async def tool_compute_gaps(self) -> dict[str, Any]:
        assert self.context is not None
        context = self.context
        run = context.run
        if context.arrivals_dataset is None:
            await self._add_warning(
                run.id, "no_arrivals", "No arrivals dataset selected; gap view disabled."
            )
            return {"gap_enabled": False}
        async with self.session_factory() as session:
            dataset = await session.get(ArrivalsDataset, context.arrivals_dataset.id)
            rows = (
                (
                    await session.execute(
                        select(ArrivalsRow).where(
                            ArrivalsRow.dataset_id == context.arrivals_dataset.id
                        )
                    )
                )
                .scalars()
                .all()
            )
            markets = (
                (await session.execute(select(Market).where(Market.id.in_(context.market_ids))))
                .scalars()
                .all()
            )
            market_refs = [
                MarketRef(
                    id=market.id,
                    city=market.city,
                    country_code=market.country_code,
                    country_name=market.country_name,
                    population_band=market.population_band,
                )
                for market in markets
            ]
            from tastebound_api.arrivals.parser import ArrivalsInputRow

            input_rows = [
                ArrivalsInputRow(
                    line=index + 2,
                    origin_raw=row.origin_raw,
                    arrivals=row.arrivals,
                    year=row.year,
                )
                for index, row in enumerate(rows)
            ]
            matched = match_arrivals(input_rows, market_refs)
            by_line = {
                input_row.line: db_row for input_row, db_row in zip(input_rows, rows, strict=True)
            }
            for row in rows:
                row.matched_market_id = None
                row.matched_country = None
            for match in matched.matched_rows:
                line_value = match.get("line")
                if not isinstance(line_value, int):
                    continue
                db_row = by_line.get(line_value)
                if db_row is None:
                    continue
                if match.get("market_id"):
                    db_row.matched_market_id = str(match["market_id"])
                if match.get("country"):
                    db_row.matched_country = str(match["country"])
            gap = compute_gap(
                context.scored,
                matched.by_market,
                taste_threshold=DEFAULT_THRESHOLDS["gap_taste"],
                arrivals_threshold=DEFAULT_THRESHOLDS["gap_arrivals"],
            )
            for market_id, result in gap.items():
                score_row = await session.get(
                    MarketScore, {"run_id": run.id, "market_id": market_id}
                )
                if score_row is None:
                    continue
                score_row.arrivals_share = result.arrivals_share
                score_row.arrivals_pct = result.arrivals_pct
                score_row.gap = result.gap
                score_row.quadrant = result.quadrant
            run_row = await session.get(Run, run.id)
            if run_row is not None:
                settings = dict(run_row.settings or {})
                settings["gap_enabled"] = bool(gap)
                settings["gap_note"] = (
                    "Country arrivals split across the selected markets by population band."
                    if matched.by_country
                    else None
                )
                if dataset is not None:
                    settings["arrivals_source_note"] = dataset.source_note
                run_row.settings = settings
                run_row.counters = dict(self.counters)
            await session.commit()
        return {
            "gap_markets": len(gap),
            "matched_markets": matched.matched_market_count,
            "quadrants": {
                quadrant: sum(1 for result in gap.values() if result.quadrant == quadrant)
                for quadrant in ("untapped", "core", "habit", "low_priority")
            },
        }

    async def tool_market_audience(self, market_ids: list[str]) -> dict[str, Any]:
        assert self.context is not None and self.service is not None
        context = self.context
        run = context.run
        signal_ids = await self._profile_signal_ids()
        summary = await self.service.demographics(
            profile_entity_ids=signal_ids,
            run_id=run.id,
            step="audience",
        )
        async with self.session_factory() as session:
            await session.execute(delete(MarketAudience).where(MarketAudience.run_id == run.id))
            for market_id in market_ids:
                for row in summary.rows:
                    session.add(
                        MarketAudience(
                            run_id=run.id,
                            market_id=market_id,
                            dimension=row["dimension"],
                            band=row["band"],
                            share=row.get("share"),
                            baseline_share=row.get("baseline_share"),
                            over_index=row.get("over_index"),
                            source_call_id=summary.call_ids[0] if summary.call_ids else None,
                        )
                    )
            run_row = await session.get(Run, run.id)
            if run_row is not None:
                settings = dict(run_row.settings or {})
                settings["audience_note"] = summary.note
                settings["audience_available"] = summary.available
                run_row.settings = settings
                run_row.counters = dict(self.counters)
            await session.commit()
        return {
            "available": summary.available,
            "rows": len(summary.rows),
            "markets": len(market_ids),
            "note": summary.note,
        }

    async def tool_market_angles(self, market_ids: list[str]) -> dict[str, Any]:
        assert self.context is not None
        context = self.context
        run = context.run
        destination_name = (
            context.destination_match.name
            if context.destination_match
            else context.destination.name
        )
        async with self.session_factory() as session:
            scores = {
                row.market_id: row
                for row in (
                    await session.execute(
                        select(MarketScore).where(
                            MarketScore.run_id == run.id, MarketScore.market_id.in_(market_ids)
                        )
                    )
                )
                .scalars()
                .all()
            }
            entities = (
                (
                    await session.execute(
                        select(ProfileEntity).where(
                            ProfileEntity.run_id == run.id, ProfileEntity.role == "item"
                        )
                    )
                )
                .scalars()
                .all()
            )
            entity_by_id = {entity.qloo_entity_id: entity for entity in entities}
            tags = (
                (
                    await session.execute(
                        select(ProfileTag)
                        .where(ProfileTag.run_id == run.id)
                        .order_by(ProfileTag.entity_count.desc())
                        .limit(6)
                    )
                )
                .scalars()
                .all()
            )
            markets = {
                market.id: market
                for market in (
                    await session.execute(select(Market).where(Market.id.in_(market_ids)))
                )
                .scalars()
                .all()
            }
            await session.execute(delete(MarketAngle).where(MarketAngle.run_id == run.id))
            insufficient = 0
            for market_id in market_ids:
                score = scores.get(market_id)
                market = markets.get(market_id)
                if score is None or market is None:
                    continue
                contributions = score.contributions or []
                ranked = sorted(
                    contributions, key=lambda item: float(item.get("score", 0)), reverse=True
                )[:3]
                evidence: list[dict[str, Any]] = []
                for item in ranked:
                    entity_id = str(item.get("entity_id", ""))
                    entity = entity_by_id.get(entity_id)
                    evidence.append(
                        {
                            "id": f"angle-{market_id}-entity-{entity_id}",
                            "kind": "entity",
                            "label": entity.name if entity else entity_id,
                            "value": float(item.get("score", 0)),
                            "source_call_id": score.source_call_ids[0]
                            if score.source_call_ids
                            else None,
                        }
                    )
                tag_evidence = []
                for tag in tags[:3]:
                    tag_evidence.append(
                        {
                            "id": f"angle-{market_id}-tag-{tag.tag_id}",
                            "kind": "tag",
                            "label": tag.label,
                            "value": tag.entity_count,
                            "source_call_id": score.source_call_ids[0]
                            if score.source_call_ids
                            else None,
                        }
                    )
                evidence.extend(tag_evidence)
                if not ranked and not tag_evidence:
                    insufficient += 1
                    headline = (
                        f"Insufficient per-entity data for {market.city}; "
                        "treat this market as low confidence."
                    )
                else:
                    lead_entity = evidence[0]["label"] if evidence else destination_name
                    lead_tag = tag_evidence[0]["label"] if tag_evidence else None
                    if lead_tag:
                        headline = (
                            f"Lead with {lead_tag} and {lead_entity}: people in {market.city} "
                            f"who like {destination_name} over-index on them."
                        )
                    else:
                        headline = (
                            f"Lead with {lead_entity}: people in {market.city} who like "
                            f"{destination_name} over-index on it."
                        )
                session.add(
                    MarketAngle(
                        run_id=run.id,
                        market_id=market_id,
                        headline=headline,
                        evidence=evidence,
                        source_call_ids=score.source_call_ids,
                    )
                )
            run_row = await session.get(Run, run.id)
            if run_row is not None:
                run_row.counters = dict(self.counters)
            await session.commit()
        return {"markets": len(market_ids), "insufficient": insufficient}

    async def tool_media_partners(self, market_ids: list[str]) -> dict[str, Any]:
        assert self.context is not None and self.service is not None
        context = self.context
        run = context.run
        signal_ids = await self._profile_signal_ids()
        async with self.session_factory() as session:
            markets = {
                market.id: market
                for market in (
                    await session.execute(select(Market).where(Market.id.in_(market_ids)))
                )
                .scalars()
                .all()
            }
            await session.execute(delete(MarketPartner).where(MarketPartner.run_id == run.id))
            await session.commit()
        counts: dict[str, int] = {}
        for market_id in market_ids:
            market = markets.get(market_id)
            if market is None:
                continue
            for partner_type in ("podcast", "artist", "movie", "book"):
                try:
                    candidates, _calls, warnings = await self.service.market_partners(
                        profile_entity_ids=signal_ids,
                        market_lat=market.lat,
                        market_lon=market.lon,
                        partner_type=partner_type,
                        run_id=run.id,
                        step=f"deep_{market_id}",
                    )
                except QlooBudgetExceeded:
                    raise
                except (QlooAuthError, QlooUnconfigured):
                    raise
                except QlooError as exc:
                    await self._add_warning(
                        run.id, "partner_failed", f"{market.city} {partner_type}: {exc.detail}"
                    )
                    continue
                for warning in warnings:
                    await self._add_warning(run.id, "partner_warning", warning)
                async with self.session_factory() as session:
                    for rank, candidate in enumerate(candidates[:10], start=1):
                        session.add(
                            MarketPartner(
                                id=str(uuid.uuid4()),
                                run_id=run.id,
                                market_id=market_id,
                                partner_type=partner_type,
                                qloo_entity_id=candidate.entity.entity_id,
                                name=candidate.entity.name,
                                lift=candidate.lift,
                                rank=rank,
                                explanation=None,
                                source_call_id=candidate.call_id,
                            )
                        )
                    await session.commit()
                counts[partner_type] = counts.get(partner_type, 0) + len(candidates[:10])
        try:
            brands, _call_id, warnings = await self.service.global_brands(
                profile_entity_ids=signal_ids, run_id=run.id, step="deep_global"
            )
        except QlooBudgetExceeded:
            raise
        except QlooError as exc:
            await self._add_warning(run.id, "brands_failed", exc.detail)
            brands = []
            warnings = []
        for warning in warnings:
            await self._add_warning(run.id, "partner_warning", warning)
        async with self.session_factory() as session:
            for rank, candidate in enumerate(brands[:10], start=1):
                session.add(
                    MarketPartner(
                        id=str(uuid.uuid4()),
                        run_id=run.id,
                        market_id=None,
                        partner_type="brand",
                        qloo_entity_id=candidate.entity.entity_id,
                        name=candidate.entity.name,
                        lift=None,
                        rank=rank,
                        explanation="Global brand affinity; brands ignore location.",
                        source_call_id=candidate.call_id,
                    )
                )
            run_row = await session.get(Run, run.id)
            if run_row is not None:
                run_row.counters = dict(self.counters)
            await session.commit()
        counts["brand"] = len(brands[:10])
        return counts

    async def tool_write_briefs(self, market_ids: list[str]) -> dict[str, Any]:
        assert self.context is not None
        context = self.context
        run = context.run
        destination_name = (
            context.destination_match.name
            if context.destination_match
            else context.destination.name
        )
        written = 0
        sources: dict[str, int] = {}
        async with self.session_factory() as session:
            scores = {
                row.market_id: row
                for row in (
                    await session.execute(
                        select(MarketScore).where(
                            MarketScore.run_id == run.id, MarketScore.market_id.in_(market_ids)
                        )
                    )
                )
                .scalars()
                .all()
            }
            markets = {
                market.id: market
                for market in (
                    await session.execute(select(Market).where(Market.id.in_(market_ids)))
                )
                .scalars()
                .all()
            }
            angles = {
                row.market_id: row
                for row in (
                    await session.execute(
                        select(MarketAngle).where(
                            MarketAngle.run_id == run.id, MarketAngle.market_id.in_(market_ids)
                        )
                    )
                )
                .scalars()
                .all()
            }
            audiences = (
                (
                    await session.execute(
                        select(MarketAudience).where(MarketAudience.run_id == run.id)
                    )
                )
                .scalars()
                .all()
            )
            partners = (
                (await session.execute(select(MarketPartner).where(MarketPartner.run_id == run.id)))
                .scalars()
                .all()
            )
            run_row = await session.get(Run, run.id)
            settings = dict(run_row.settings or {}) if run_row else {}
            for market_id in market_ids:
                market = markets.get(market_id)
                score = scores.get(market_id)
                if market is None or score is None:
                    continue
                angle = angles.get(market_id)
                market_partners = [p for p in partners if p.market_id == market_id]
                market_audience = [a for a in audiences if a.market_id == market_id]
                bundle = build_bundle(
                    market_id=market_id,
                    destination=destination_name,
                    market_city=market.city,
                    evidence=angle.evidence if angle else [],
                    numbers=[
                        value
                        for value in [
                            score.taste_score,
                            score.lift,
                            score.gap,
                            score.arrivals_share,
                            score.coverage,
                            float(score.rank or 0),
                            *[float(p.lift) for p in market_partners if p.lift is not None],
                            *[
                                float(a.over_index)
                                for a in market_audience
                                if a.over_index is not None
                            ],
                        ]
                        if value is not None
                    ],
                    names=[
                        market.city,
                        destination_name,
                        *[p.name for p in market_partners],
                        *(
                            [str(item.get("label")) for item in (angle.evidence or [])]
                            if angle
                            else []
                        ),
                    ],
                )
                content: BriefContent | None = None
                source = "template"
                model = None
                if self.provider is not None and self.settings.llm_tool_calling:
                    content, model, violations = await self._write_with_llm(bundle, run.id)
                    if content is not None:
                        source = "llm"
                    else:
                        if violations:
                            await self._add_warning(
                                run.id, "brief_grounding", "; ".join(violations[:3])
                            )
                if content is None:
                    content = self._template_brief(
                        market=market,
                        score=score,
                        angle=angle,
                        audience=market_audience,
                        partners=market_partners,
                        destination=destination_name,
                        gap_note=settings.get("gap_note"),
                    )
                existing = (
                    (
                        await session.execute(
                            select(Brief).where(
                                Brief.run_id == run.id, Brief.market_id == market_id
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                evidence_ids = sorted(bundle.evidence_ids)
                if existing is None:
                    session.add(
                        Brief(
                            id=str(uuid.uuid4()),
                            run_id=run.id,
                            workspace_id=run.workspace_id,
                            market_id=market_id,
                            content={
                                "title": content.title,
                                "summary": content.summary,
                                "sections": content.sections,
                                "evidence_ids": evidence_ids,
                            },
                            source=source,
                            model=model,
                            prompt_version=PROMPT_VERSION,
                        )
                    )
                else:
                    existing.content = {
                        "title": content.title,
                        "summary": content.summary,
                        "sections": content.sections,
                        "evidence_ids": evidence_ids,
                    }
                    existing.source = source
                    existing.model = model
                    existing.updated_at = _now()
                sources[source] = sources.get(source, 0) + 1
                written += 1
            if run_row is not None:
                run_row.counters = dict(self.counters)
            await session.commit()
        return {"briefs": written, "sources": sources}

    async def _write_with_llm(
        self, bundle: Any, run_id: str
    ) -> tuple[BriefContent | None, str | None, list[str]]:
        assert self.provider is not None
        bundle_payload = {
            "market_id": bundle.market_id,
            "destination": bundle.destination,
            "market_city": bundle.market_city,
            "evidence_ids": sorted(bundle.evidence_ids),
            "names": sorted(bundle.names),
            "numbers": sorted(bundle.numbers),
        }
        messages = [
            ChatMessage(role="system", content=load_prompt("market_brief")),
            ChatMessage(
                role="user",
                content=f"Evidence bundle (JSON):\n{json.dumps(bundle_payload, default=str)}",
            ),
        ]
        started = time.monotonic()
        try:
            result = await self.provider.chat(
                messages,
                temperature=self.settings.llm_temperature_writing,
                response_format={"type": "json_object"},
            )
        except LLMError as exc:
            await self._record_llm(run_id, "brief", "error", 0)
            return None, None, [str(exc)]
        parsed = _extract_json(result.content)
        violations: list[str] = []
        content = self._brief_from_json(parsed)
        if content is not None:
            violations = validate_brief(content, bundle)
        else:
            violations = ["The provider did not return the required JSON shape."]
        if violations:
            repair_messages = [
                *messages,
                ChatMessage(role="assistant", content=result.content or ""),
                ChatMessage(
                    role="user",
                    content=(
                        "Your previous answer broke the grounding rules: "
                        + "; ".join(violations)
                        + ". Rewrite the JSON using only the bundle."
                    ),
                ),
            ]
            try:
                repaired = await self.provider.chat(
                    repair_messages,
                    temperature=self.settings.llm_temperature_tools,
                    response_format={"type": "json_object"},
                )
            except LLMError:
                await self._record_llm(run_id, "brief_repair", "error", 0)
                return None, None, violations
            repaired_content = self._brief_from_json(_extract_json(repaired.content))
            repaired_violations = (
                validate_brief(repaired_content, bundle) if repaired_content else ["Invalid JSON."]
            )
            await self._record_llm(run_id, "brief", "ok", int((time.monotonic() - started) * 1000))
            if repaired_content is not None and not repaired_violations:
                return repaired_content, result.model, []
            return None, None, repaired_violations
        await self._record_llm(run_id, "brief", "ok", int((time.monotonic() - started) * 1000))
        return content, result.model, []

    def _brief_from_json(self, parsed: dict[str, Any] | None) -> BriefContent | None:
        if not parsed:
            return None
        title = str(parsed.get("title") or "").strip()
        summary = str(parsed.get("summary") or "").strip()
        sections = parsed.get("sections")
        if not title or not summary or not isinstance(sections, list) or not sections:
            return None
        cleaned: list[dict[str, Any]] = []
        for section in sections:
            if not isinstance(section, dict):
                return None
            heading = str(section.get("heading") or "").strip()
            body = str(section.get("body") or "").strip()
            cited = section.get("cited_evidence_ids") or []
            if not heading or not body or not isinstance(cited, list):
                return None
            cleaned.append(
                {
                    "heading": heading,
                    "body": body,
                    "cited_evidence_ids": [str(item) for item in cited],
                }
            )
        return BriefContent(title=title, summary=summary, sections=cleaned)

    def _template_brief(
        self,
        *,
        market: Market,
        score: MarketScore,
        angle: MarketAngle | None,
        audience: list[MarketAudience],
        partners: list[MarketPartner],
        destination: str,
        gap_note: str | None,
    ) -> BriefContent:
        taste = score.taste_score or 0.0
        lift = score.lift or 0.0
        rank = score.rank or 0
        evidence_ids: list[str] = [f"score-{market.id}"]
        if score.gap is not None:
            evidence_ids.append(f"gap-{market.id}")
        if angle is not None:
            evidence_ids.extend(str(item.get("id")) for item in angle.evidence)
        top_partner_by_type: dict[str, MarketPartner] = {}
        for partner in sorted(partners, key=lambda row: row.rank):
            top_partner_by_type.setdefault(partner.partner_type, partner)
        evidence_ids.extend(
            f"partner-{partner.partner_type}-{partner.qloo_entity_id}"
            for partner in top_partner_by_type.values()
        )
        best_age = max(
            (row for row in audience if row.dimension == "age" and row.over_index is not None),
            key=lambda row: row.over_index or 0,
            default=None,
        )
        if best_age is not None:
            evidence_ids.append(f"audience-{market.id}-{best_age.band}")
        gender = next(
            (row for row in audience if row.dimension == "gender" and (row.over_index or 0) > 0),
            None,
        )
        headline = angle.headline if angle else f"Insufficient per-entity data for {market.city}."
        summary = (
            f"{market.city} ranks {rank} of the scored markets with a taste score of {taste}/100 "
            f"and a lift of {round(lift, 4)} over baseline."
        )
        sections = [
            {
                "heading": "Why this market",
                "body": (
                    f"Taste score {taste}/100 (rank {rank}) with lift {round(lift, 4)} over the "
                    f"popularity baseline. Confidence: {score.confidence}."
                ),
                "cited_evidence_ids": [f"score-{market.id}"],
            },
            {
                "heading": "Who to target",
                "body": (
                    (
                        f"The strongest age signal is {_band_label(best_age.band)} at "
                        f"{best_age.over_index} points over the population average."
                        if best_age is not None
                        else "Qloo returned no audience data for this profile."
                    )
                    + (
                        f" Gender skew: {_band_label(gender.band)} at {gender.over_index} points."
                        if gender is not None
                        else ""
                    )
                ),
                "cited_evidence_ids": [f"audience-{market.id}-{best_age.band}"]
                if best_age
                else [f"score-{market.id}"],
            },
            {
                "heading": "What to lead with",
                "body": headline,
                "cited_evidence_ids": [
                    str(item.get("id")) for item in (angle.evidence if angle else [])[:2]
                ]
                or [f"score-{market.id}"],
            },
            {
                "heading": "Partners to approach",
                "body": (
                    "; ".join(
                        f"{partner.name} ({partner.partner_type})"
                        for partner in top_partner_by_type.values()
                    )
                    or "No partner data returned for this market."
                ),
                "cited_evidence_ids": [
                    f"partner-{partner.partner_type}-{partner.qloo_entity_id}"
                    for partner in top_partner_by_type.values()
                ]
                or [f"score-{market.id}"],
            },
            {
                "heading": "Budget and caveats",
                "body": (
                    "Use the allocator to turn this score into a share. "
                    + (f"{gap_note} " if gap_note else "")
                    + "This is taste fit, not a visitor forecast."
                ),
                "cited_evidence_ids": evidence_ids[:4],
            },
        ]
        return BriefContent(
            title=f"{market.city}: taste-led brief for {destination}",
            summary=summary,
            sections=sections,
        )

    async def _record_llm(self, run_id: str, purpose: str, status: str, duration_ms: int) -> None:
        self.counters["llm"] += 1
        provider_name = self.provider.name if self.provider else "none"
        model_name = self.provider.model if self.provider else "none"

        async def _op(session: AsyncSession) -> None:
            session.add(
                LLMCall(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    purpose=purpose,
                    provider=provider_name,
                    model=model_name,
                    prompt_version=PROMPT_VERSION,
                    status=status,
                    duration_ms=duration_ms,
                )
            )
            await session.commit()

        await _with_retry(self.session_factory, _op)

    async def tool_finish_phase(self) -> dict[str, Any]:
        return {"ok": True}
