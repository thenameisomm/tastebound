from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import quote

from sqlalchemy import select

from tastebound_api.assistant.models import EvidenceItem
from tastebound_api.db.database import get_session_factory
from tastebound_api.db.tables import (
    Allocation,
    Destination,
    Market,
    MarketAngle,
    MarketAudience,
    MarketPartner,
    MarketScore,
    ProfileEntity,
    ProfileTag,
    Run,
    SignatureItem,
)
from tastebound_api.errors import NotFound, ValidationProblem
from tastebound_api.grounding import ALLOWED_NAME_WORDS, NUMBER_RE, WORD_RE
from tastebound_api.scoring.markets import DEFAULT_THRESHOLDS

READY_STATUSES = {"scored", "deep_dive", "done", "partial"}


@dataclass
class AssistantContext:
    run: Run
    destination_name: str
    focus_market_id: str | None
    payload: dict[str, Any]
    evidence: dict[str, EvidenceItem]
    suggested_questions: list[str]
    numbers: set[float]
    names: set[str]
    ready: bool
    notice: str | None = None
    context_chars: int = 0
    omitted_markets: int = 0
    extra_names: set[str] = field(default_factory=set)


def _pct(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"{value * 100:.1f}%"


def _number(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)


def _clean_detail(parts: list[str]) -> str:
    return " · ".join(part for part in parts if part)


def _collect_numbers(value: Any, bucket: set[float]) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | float):
        bucket.add(float(value))
        return
    if isinstance(value, str):
        for match in NUMBER_RE.findall(value):
            try:
                bucket.add(float(match.replace("%", "").replace(",", ".")))
            except ValueError:
                continue
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect_numbers(item, bucket)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _collect_numbers(item, bucket)


def _collect_names(value: Any, bucket: set[str]) -> None:
    if isinstance(value, str):
        bucket.add(value.casefold())
        for match in WORD_RE.findall(value):
            for word in match.split():
                bucket.add(word.strip("'’").casefold())
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect_names(item, bucket)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _collect_names(item, bucket)


def _market_href(run_id: str, market_id: str, anchor: str = "score") -> str:
    return f"/runs/{quote(run_id)}/markets/{quote(market_id)}#{anchor}"


def _trace_href(run_id: str, call_id: str | None) -> str:
    base = f"/runs/{quote(run_id)}/trace"
    return f"{base}?call={quote(call_id)}" if call_id else base


def _ready(run: Run, has_scores: bool) -> bool:
    return bool(has_scores and run.status in READY_STATUSES)


def _headline_suggestions(
    *, focus_city: str | None, gap_enabled: bool, quadrant: str | None
) -> list[str]:
    if focus_city:
        suggestions = [
            f"Explain {focus_city}'s taste score and confidence.",
            f"Who is the audience in {focus_city}?",
        ]
        if quadrant:
            suggestions.append(f"Why is {focus_city} in the {quadrant.replace('_', ' ')} quadrant?")
        else:
            suggestions.append(f"What should we lead with in {focus_city}?")
        suggestions.append(f"Which partners fit {focus_city}, and what is the caveat?")
        return suggestions
    suggestions = ["Which market should we prioritise, and why?"]
    suggestions.append(
        "What is the strongest untapped opportunity?"
        if gap_enabled
        else "Where is taste fit strongest?"
    )
    suggestions.append("Where is the evidence weakest?")
    suggestions.append("What should we do next with this shortlist?")
    return suggestions


async def build_context(
    *,
    run: Run,
    focus_market_id: str | None,
    max_context_chars: int,
) -> AssistantContext:
    session_factory = get_session_factory()
    async with session_factory() as session:
        destination = await session.get(Destination, run.destination_id)
        if destination is None:
            raise NotFound("destination")
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
        scores = (
            (
                await session.execute(
                    select(MarketScore)
                    .where(MarketScore.run_id == run.id)
                    .order_by(MarketScore.rank.is_(None), MarketScore.rank, MarketScore.market_id)
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
        profile_entities = (
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
        profile_tags = (
            (
                await session.execute(
                    select(ProfileTag)
                    .where(ProfileTag.run_id == run.id)
                    .order_by(ProfileTag.entity_count.desc(), ProfileTag.label)
                )
            )
            .scalars()
            .all()
        )
        focus_score = None
        focus_market = None
        audience: list[MarketAudience] = []
        angle = None
        partners: list[MarketPartner] = []
        allocation = None
        if focus_market_id:
            focus_score = next((row for row in scores if row.market_id == focus_market_id), None)
            if focus_score is None:
                raise ValidationProblem("This market is not part of the run.")
            focus_market = markets.get(focus_market_id)
            if focus_market is None:
                raise NotFound("market")
            audience = list(
                (
                    await session.execute(
                        select(MarketAudience)
                        .where(
                            MarketAudience.run_id == run.id,
                            MarketAudience.market_id == focus_market_id,
                        )
                        .order_by(MarketAudience.dimension, MarketAudience.band)
                    )
                )
                .scalars()
                .all()
            )
            angle = await session.get(MarketAngle, {"run_id": run.id, "market_id": focus_market_id})
            partners = list(
                (
                    await session.execute(
                        select(MarketPartner)
                        .where(
                            MarketPartner.run_id == run.id,
                            MarketPartner.market_id == focus_market_id,
                        )
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
        global_brands = (
            (
                await session.execute(
                    select(MarketPartner)
                    .where(
                        MarketPartner.run_id == run.id,
                        MarketPartner.market_id.is_(None),
                        MarketPartner.partner_type == "brand",
                    )
                    .order_by(MarketPartner.rank)
                )
            )
            .scalars()
            .all()
        )

    run_settings = dict(run.settings or {})
    warnings = run_settings.get("warnings", [])
    if not isinstance(warnings, list):
        warnings = []
    gap_enabled = bool(run_settings.get("gap_enabled", False))
    population_suspect = bool(run_settings.get("population_suspect", False))

    evidence: dict[str, EvidenceItem] = {}
    evidence_counter = 0

    def add_evidence(
        kind: str,
        label: str,
        detail: str,
        href: str,
        source_call_id: str | None = None,
    ) -> EvidenceItem:
        nonlocal evidence_counter
        evidence_counter += 1
        item = EvidenceItem(
            id=f"E{evidence_counter}",
            kind=kind,
            label=label,
            detail=detail,
            href=href,
            source_call_id=source_call_id,
        )
        evidence[item.id] = item
        return item

    market_rows: list[dict[str, Any]] = []
    for score in scores:
        market = markets.get(score.market_id)
        if market is None:
            continue
        detail = _clean_detail(
            [
                f"rank {score.rank if score.rank is not None else 'unranked'}",
                (
                    f"taste {score.taste_score:.2f}"
                    if score.taste_score is not None
                    else "taste unknown"
                ),
                f"lift {score.lift:+.2f}" if score.lift is not None else "lift unknown",
                f"coverage {_pct(score.coverage)}",
                f"confidence {score.confidence or 'unknown'}",
                f"arrivals {_pct(score.arrivals_share)}",
                (
                    f"gap {score.gap * 100:+.2f} points"
                    if score.gap is not None
                    else "gap unavailable"
                ),
                f"quadrant {score.quadrant or 'unclassified'}",
            ]
        )
        score_call_ids = list(score.source_call_ids or [])
        source_call_id = score_call_ids[0] if score_call_ids else None
        item = add_evidence(
            "market_score",
            f"{market.city} score",
            detail,
            _market_href(run.id, market.id),
            source_call_id if isinstance(source_call_id, str) else None,
        )
        market_rows.append(
            {
                "market_id": market.id,
                "city": market.city,
                "country": market.country_name,
                "region": market.region,
                "rank": score.rank,
                "taste_score": _number(score.taste_score),
                "lift": _number(score.lift),
                "coverage": _number(score.coverage, 4),
                "confidence": score.confidence,
                "arrivals_share_pct": (
                    _number(score.arrivals_share * 100, 4)
                    if score.arrivals_share is not None
                    else None
                ),
                "arrivals_percentile": (
                    _number(score.arrivals_pct * 100, 2) if score.arrivals_pct is not None else None
                ),
                "gap_points": (_number(score.gap * 100, 2) if score.gap is not None else None),
                "quadrant": score.quadrant,
                "flags": list(score.flags or []),
                "angle_headline": score.angle_headline,
                "evidence_id": item.id,
            }
        )

    tags_payload: list[dict[str, Any]] = []
    for tag in profile_tags[:12]:
        item = add_evidence(
            "profile_tag",
            f"Profile tag: {tag.label}",
            f"{tag.label} appears across {tag.entity_count} profile entities.",
            f"/runs/{quote(run.id)}#method",
        )
        tags_payload.append(
            {"label": tag.label, "entity_count": tag.entity_count, "evidence_id": item.id}
        )

    profile_payload = {
        "resolved_items": len(profile_entities),
        "items": [
            {
                "name": entity.name,
                "type": entity.entity_type,
                "role": entity.role,
                "similarity": _number(entity.similarity, 4),
            }
            for entity in profile_entities[:20]
        ],
        "tags": tags_payload,
    }
    profile_evidence = add_evidence(
        "taste_profile",
        f"{destination.name} taste profile",
        _clean_detail(
            [
                f"{len(profile_entities)} resolved Qloo entities",
                f"{len(profile_tags)} tags",
                (
                    "top tags: " + ", ".join(tag.label for tag in profile_tags[:6])
                    if profile_tags
                    else "no tags"
                ),
            ]
        ),
        f"/runs/{quote(run.id)}#method",
    )
    profile_payload["evidence_id"] = profile_evidence.id

    focus_payload: dict[str, Any] | None = None
    focus_city = focus_market.city if focus_market is not None else None
    if focus_market is not None and focus_score is not None:
        audience_payload: list[dict[str, Any]] = []
        for row in audience:
            item = add_evidence(
                "audience",
                f"{focus_market.city} audience: {row.dimension} {row.band.replace('_', ' ')}",
                _clean_detail(
                    [
                        f"share {_pct(row.share)}",
                        f"baseline {_pct(row.baseline_share)}",
                        (
                            f"over-index {row.over_index:.2f}"
                            if row.over_index is not None
                            else "over-index unavailable"
                        ),
                    ]
                ),
                _market_href(run.id, focus_market.id, "audience"),
                row.source_call_id,
            )
            audience_payload.append(
                {
                    "dimension": row.dimension,
                    "band": row.band.replace("_", " "),
                    "share_pct": (_number(row.share * 100, 2) if row.share is not None else None),
                    "baseline_pct": (
                        _number(row.baseline_share * 100, 2)
                        if row.baseline_share is not None
                        else None
                    ),
                    "over_index": _number(row.over_index, 4),
                    "evidence_id": item.id,
                }
            )

        angle_payload = None
        if angle is not None:
            angle_calls = list(angle.source_call_ids or [])
            item = add_evidence(
                "campaign_angle",
                f"{focus_market.city} campaign angle",
                angle.headline,
                _market_href(run.id, focus_market.id, "angle"),
                angle_calls[0] if angle_calls else None,
            )
            angle_payload = {
                "headline": angle.headline,
                "angle_evidence": angle.evidence or [],
                "evidence_id": item.id,
            }

        grouped: dict[str, list[dict[str, Any]]] = {}
        for partner in partners:
            item = add_evidence(
                "partner",
                f"{partner.name} partner",
                _clean_detail(
                    [
                        f"{partner.partner_type} partner",
                        f"rank {partner.rank}",
                        (
                            f"lift {partner.lift:+.2f}"
                            if partner.lift is not None
                            else "lift unavailable"
                        ),
                    ]
                ),
                _market_href(run.id, focus_market.id, "partners"),
                partner.source_call_id,
            )
            grouped.setdefault(partner.partner_type, []).append(
                {
                    "name": partner.name,
                    "rank": partner.rank,
                    "lift": _number(partner.lift),
                    "evidence_id": item.id,
                }
            )

        brands_payload: list[dict[str, Any]] = []
        for brand in global_brands:
            item = add_evidence(
                "brand",
                f"{brand.name} global brand",
                (
                    f"Taste lift {brand.lift:+.2f} against the destination profile."
                    if brand.lift is not None
                    else "Taste lift unavailable."
                ),
                f"/runs/{quote(run.id)}#method",
                brand.source_call_id,
            )
            brands_payload.append(
                {
                    "name": brand.name,
                    "rank": brand.rank,
                    "lift": _number(brand.lift),
                    "evidence_id": item.id,
                }
            )

        allocation_payload = None
        if allocation is not None:
            entry = next(
                (
                    value
                    for value in allocation.shares or []
                    if value.get("market_id") == focus_market.id
                ),
                None,
            )
            if entry is not None:
                item = add_evidence(
                    "allocation",
                    f"{focus_market.city} budget share",
                    f"{_pct(float(entry.get('share', 0)))} of {allocation.currency} "
                    f"{allocation.total:,.0f} from the latest plan.",
                    f"/runs/{quote(run.id)}/plan",
                )
                allocation_payload = {
                    "share_pct": _number(float(entry.get("share", 0)) * 100, 2),
                    "amount": _number(float(entry.get("amount", 0))),
                    "currency": allocation.currency,
                    "total": _number(allocation.total),
                    "evidence_id": item.id,
                }

        focus_payload = {
            "market_id": focus_market.id,
            "city": focus_market.city,
            "country": focus_market.country_name,
            "region": focus_market.region,
            "score": next(
                (row for row in market_rows if row["market_id"] == focus_market.id), None
            ),
            "audience": audience_payload,
            "audience_available": bool(audience_payload)
            or bool(run_settings.get("audience_available", False)),
            "audience_note": run_settings.get("audience_note"),
            "angle": angle_payload,
            "partners": grouped,
            "global_brands": brands_payload,
            "allocation": allocation_payload,
        }

    warning_payload: list[dict[str, Any]] = []
    for warning in warnings[:8]:
        if not isinstance(warning, dict):
            continue
        message = str(warning.get("message") or "").strip()
        if not message:
            continue
        item = add_evidence(
            "warning",
            "Run warning",
            message,
            f"/runs/{quote(run.id)}#method",
        )
        warning_payload.append(
            {"code": warning.get("code"), "message": message, "evidence_id": item.id}
        )

    arrivals_evidence = None
    arrivals_source_note = run_settings.get("arrivals_source_note")
    if arrivals_source_note:
        arrivals_evidence = add_evidence(
            "arrivals",
            "Arrivals source",
            str(arrivals_source_note),
            f"/runs/{quote(run.id)}/plan",
        )

    method_evidence = add_evidence(
        "method",
        "How TasteBound scores markets",
        "Taste score is a percentile of target affinity. Lift is target minus baseline "
        "affinity. Gap is taste percentile minus arrivals percentile. Taste fit is not a "
        "visitor forecast or demand.",
        f"/runs/{quote(run.id)}#method",
    )
    caveat_evidence = None
    caveat_parts = []
    if population_suspect:
        caveat_parts.append(
            "Population correlation is "
            f"{(run_settings.get('population_correlation') or 0):.2f}; the ranking may partly "
            "track market size."
        )
    if run_settings.get("gap_note"):
        caveat_parts.append(str(run_settings["gap_note"]))
    if caveat_parts:
        caveat_evidence = add_evidence(
            "caveat",
            "Read with care",
            " ".join(caveat_parts),
            f"/runs/{quote(run.id)}#method",
        )

    thresholds = run_settings.get("thresholds") or DEFAULT_THRESHOLDS
    created_at = run.created_at
    payload: dict[str, Any] = {
        "run": {
            "id": run.id,
            "status": run.status,
            "destination": destination.name,
            "scoring_version": run.scoring_version,
            "created_at": (
                created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
            ),
            "gap_enabled": gap_enabled,
            "gap_note": run_settings.get("gap_note"),
            "arrivals_source_note": arrivals_source_note,
            "population_correlation": _number(run_settings.get("population_correlation"), 4),
            "population_suspect": population_suspect,
            "audience_available": bool(run_settings.get("audience_available", False)),
            "audience_note": run_settings.get("audience_note"),
            "thresholds": thresholds,
            "market_count": len(market_rows),
            "profile_item_count": len(items),
            "warnings": warning_payload,
            "method": (
                "Taste score is a percentile of target affinity, not a visitor forecast. "
                "Lift is target minus baseline. Gap is taste percentile minus arrivals "
                "percentile. The deterministic scorer decides; the assistant only explains."
            ),
            "method_evidence_id": method_evidence.id,
            "caveat_evidence_id": caveat_evidence.id if caveat_evidence else None,
            "arrivals_evidence_id": arrivals_evidence.id if arrivals_evidence else None,
        },
        "profile": profile_payload,
        "markets": market_rows,
        "focus_market": focus_payload,
    }

    focus_rank = next(
        (row["rank"] for row in market_rows if row["market_id"] == focus_market_id), None
    )
    context_chars = len(json.dumps(payload, ensure_ascii=False, default=str))
    for cap in (len(market_rows), 50, 35, 25, 15):
        if context_chars <= max_context_chars:
            break
        selected = market_rows[:cap]
        if focus_market_id and all(row["market_id"] != focus_market_id for row in selected):
            focus_row = next(
                (row for row in market_rows if row["market_id"] == focus_market_id), None
            )
            if focus_row is not None:
                selected = [*selected, focus_row]
                selected.sort(key=lambda row: (row["rank"] is None, row["rank"] or 0))
        payload["markets"] = selected
        payload["run"]["markets_omitted"] = len(market_rows) - len(selected)
        context_chars = len(json.dumps(payload, ensure_ascii=False, default=str))

    omitted = max(0, len(market_rows) - len(payload["markets"]))
    payload["run"]["markets_omitted"] = omitted
    if omitted:
        payload["run"]["markets_note"] = (
            f"Only the top {len(payload['markets'])} of {len(market_rows)} markets are shown; "
            "say so if a question depends on an omitted market."
        )

    numbers: set[float] = set()
    _collect_numbers(payload, numbers)
    if focus_rank is not None:
        numbers.add(float(focus_rank))
    names: set[str] = set(ALLOWED_NAME_WORDS)
    _collect_names(payload, names)
    names.add(destination.name.casefold())
    names.add("tastebound")

    ready = _ready(run, bool(market_rows))
    notice = None
    if not ready:
        notice = "Market results are not available yet. The assistant opens after scoring."
    suggestions = _headline_suggestions(
        focus_city=focus_city,
        gap_enabled=gap_enabled,
        quadrant=(
            next(
                (row["quadrant"] for row in market_rows if row["market_id"] == focus_market_id),
                None,
            )
            if focus_market_id
            else None
        ),
    )
    return AssistantContext(
        run=run,
        destination_name=destination.name,
        focus_market_id=focus_market_id,
        payload=payload,
        evidence=evidence,
        suggested_questions=suggestions[:4],
        numbers=numbers,
        names=names,
        ready=ready,
        notice=notice,
        context_chars=context_chars,
        omitted_markets=omitted,
    )


def context_json(context: AssistantContext) -> str:
    return json.dumps(context.payload, ensure_ascii=False, separators=(",", ":"), default=str)
