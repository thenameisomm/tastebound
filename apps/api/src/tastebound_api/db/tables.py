from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), default="anon")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Market(Base):
    __tablename__ = "markets"
    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    city: Mapped[str] = mapped_column(String(80))
    country_code: Mapped[str] = mapped_column(String(2))
    country_name: Mapped[str] = mapped_column(String(80))
    region: Mapped[str] = mapped_column(String(40))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    radius_km: Mapped[int] = mapped_column(Integer, default=40)
    population_band: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    presets: Mapped[list[str]] = mapped_column(JSON, default=list)


class Destination(Base):
    __tablename__ = "destinations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    country_code: Mapped[str] = mapped_column(String(2))
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius_km: Mapped[int] = mapped_column(Integer, default=40)
    qloo_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SignatureItem(Base):
    __tablename__ = "signature_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    destination_id: Mapped[str] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(24))
    origin: Mapped[str] = mapped_column(String(24), default="user")
    position: Mapped[int] = mapped_column(Integer, default=0)


class ArrivalsDataset(Base):
    __tablename__ = "arrivals_datasets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    destination_id: Mapped[str | None] = mapped_column(
        ForeignKey("destinations.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(160))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str] = mapped_column(String(16), default="mixed")
    source_note: Mapped[str] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ArrivalsRow(Base):
    __tablename__ = "arrivals_rows"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("arrivals_datasets.id", ondelete="CASCADE"))
    origin_raw: Mapped[str] = mapped_column(String(160))
    arrivals: Mapped[int] = mapped_column(Integer)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matched_market_id: Mapped[str | None] = mapped_column(String(48), nullable=True)
    matched_country: Mapped[str | None] = mapped_column(String(2), nullable=True)


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    destination_id: Mapped[str] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"))
    arrivals_dataset_id: Mapped[str | None] = mapped_column(
        ForeignKey("arrivals_datasets.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(24), default="queued")
    orchestration: Mapped[str | None] = mapped_column(String(32), nullable=True)
    orchestration_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    scoring_version: Mapped[str] = mapped_column(String(32), default="2026.10.1")
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    counters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    shortlist: Mapped[list[str]] = mapped_column(JSON, default=list)
    client_ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RunMarket(Base):
    __tablename__ = "run_markets"
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)
    market_id: Mapped[str] = mapped_column(String(48), primary_key=True)


class QlooCall(Base):
    __tablename__ = "qloo_calls"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("runs.id", ondelete="SET NULL"), nullable=True
    )
    step: Mapped[str] = mapped_column(String(64))
    endpoint: Mapped[str] = mapped_column(String(120))
    params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    cache_key: Mapped[str] = mapped_column(String(64), index=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warnings: Mapped[list[Any]] = mapped_column(JSON, default=list)
    response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LLMCall(Base):
    __tablename__ = "llm_calls"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("runs.id", ondelete="SET NULL"), nullable=True
    )
    purpose: Mapped[str] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(24))
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProfileEntity(Base):
    __tablename__ = "profile_entities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    item_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    qloo_entity_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(160))
    entity_type: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(24), default="item")
    similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_call_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    tags: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    __table_args__ = (UniqueConstraint("run_id", "qloo_entity_id"),)


class ProfileTag(Base):
    __tablename__ = "profile_tags"
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    label: Mapped[str] = mapped_column(String(160))
    entity_count: Mapped[int] = mapped_column(Integer, default=1)


class MarketScore(Base):
    __tablename__ = "market_scores"
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)
    market_id: Mapped[str] = mapped_column(String(48), primary_key=True)
    target_affinity: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_affinity: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    lift: Mapped[float | None] = mapped_column(Float, nullable=True)
    taste_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    arrivals_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    arrivals_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    gap: Mapped[float | None] = mapped_column(Float, nullable=True)
    quadrant: Mapped[str | None] = mapped_column(String(24), nullable=True)
    flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_call_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    angle_headline: Mapped[str | None] = mapped_column(Text, nullable=True)
    contributions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


class MarketAudience(Base):
    __tablename__ = "market_audience"
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)
    market_id: Mapped[str] = mapped_column(String(48), primary_key=True)
    dimension: Mapped[str] = mapped_column(String(16), primary_key=True)
    band: Mapped[str] = mapped_column(String(32), primary_key=True)
    share: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    over_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_call_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class MarketAngle(Base):
    __tablename__ = "market_angles"
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)
    market_id: Mapped[str] = mapped_column(String(48), primary_key=True)
    headline: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    source_call_ids: Mapped[list[str]] = mapped_column(JSON, default=list)


class MarketPartner(Base):
    __tablename__ = "market_partners"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    market_id: Mapped[str | None] = mapped_column(String(48), nullable=True)
    partner_type: Mapped[str] = mapped_column(String(16))
    qloo_entity_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    lift: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_call_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    __table_args__ = (UniqueConstraint("run_id", "market_id", "partner_type", "qloo_entity_id"),)


class Allocation(Base):
    __tablename__ = "allocations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    workspace_id: Mapped[str] = mapped_column(String(36))
    total: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    mode: Mapped[str] = mapped_column(String(24), default="grow_untapped")
    shares: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Brief(Base):
    __tablename__ = "briefs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    workspace_id: Mapped[str] = mapped_column(String(36))
    market_id: Mapped[str] = mapped_column(String(48))
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(16), default="template")
    edited: Mapped[bool] = mapped_column(Boolean, default=False)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("run_id", "market_id"),)


class RunEvent(Base):
    __tablename__ = "run_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    seq: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("run_id", "seq"),)


class Evaluation(Base):
    __tablename__ = "evaluations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    method: Mapped[str] = mapped_column(String(64))
    results: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
