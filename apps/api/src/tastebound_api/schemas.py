from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

ItemKind = Literal[
    "landmark",
    "neighbourhood",
    "dish",
    "drink",
    "venue",
    "festival",
    "music",
    "film",
    "book",
    "brand",
]
ItemOrigin = Literal["llm_website", "llm_name_only", "user"]
RunStatus = Literal["queued", "scoring", "scored", "deep_dive", "done", "failed", "partial"]
Confidence = Literal["high", "medium", "low"]
Quadrant = Literal["untapped", "core", "habit", "low_priority"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(BaseModel):
    status: str = "ok"
    db: str
    qloo: str
    llm: dict[str, Any]
    version: str


class WorkspaceSessionResponse(BaseModel):
    workspace_token: str
    created_at: datetime


class PresetOut(BaseModel):
    id: str
    label: str
    market_ids: list[str]


class MarketOut(BaseModel):
    id: str
    city: str
    country_code: str
    country_name: str
    region: str
    lat: float
    lon: float
    radius_km: int
    population_band: int
    presets: list[str]


class MarketsResponse(BaseModel):
    markets: list[MarketOut]
    presets: list[PresetOut]


class IntakeRequest(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    country_code: str = Field(min_length=2, max_length=2)
    website_url: HttpUrl | None = None

    @field_validator("country_code")
    @classmethod
    def _upper_country(cls, value: str) -> str:
        return value.upper()


class ProposedItem(BaseModel):
    name: str
    kind: ItemKind
    origin: ItemOrigin = "user"


class IntakeResponse(BaseModel):
    destination_name: str
    country_code: str
    items: list[ProposedItem]
    notice: str | None = None
    source: Literal["website", "general_knowledge", "manual"] = "manual"
    website_read: bool = False
    text_chars: int = 0


class SignatureItemInput(StrictModel):
    name: str = Field(min_length=1, max_length=160)
    kind: ItemKind
    origin: ItemOrigin = "user"


class DestinationCreateRequest(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    country_code: str = Field(min_length=2, max_length=2)
    website_url: HttpUrl | None = None
    items: list[SignatureItemInput] = Field(default_factory=list, max_length=15)

    @field_validator("country_code")
    @classmethod
    def _upper_country(cls, value: str) -> str:
        return value.upper()


class DestinationUpdateRequest(StrictModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    website_url: HttpUrl | None = None
    items: list[SignatureItemInput] | None = Field(default=None, max_length=15)

    @field_validator("country_code")
    @classmethod
    def _upper_country(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class SignatureItemOut(BaseModel):
    id: str
    name: str
    kind: ItemKind
    origin: ItemOrigin
    position: int


class DestinationResponse(BaseModel):
    destination_id: str
    name: str
    country_code: str
    website_url: str | None
    lat: float | None
    lon: float | None
    items: list[SignatureItemOut]


class ResolvedItemOut(BaseModel):
    item_id: str | None
    name: str
    kind: ItemKind
    role: str
    entity_id: str | None
    entity_name: str | None
    entity_type: str | None
    similarity: float
    status: str
    note: str | None
    tags: list[dict[str, str]]


class ProfilePreviewResponse(BaseModel):
    destination_entity_id: str | None
    destination_name: str
    items: list[ResolvedItemOut]
    tags: list[dict[str, Any]]
    unresolved: list[str]
    can_run: bool
    warnings: list[str]


class ArrivalsSampleOut(BaseModel):
    id: str
    name: str
    year: int | None
    source_name: str
    source_url: str
    level: str
    notes: str


class ArrivalsRowErrorOut(BaseModel):
    line: int
    message: str


class ArrivalsResponse(BaseModel):
    dataset_id: str
    name: str
    level: str
    source_note: str
    is_sample: bool
    rows: int
    matched_markets: int
    matched_countries: list[str]
    errors: list[ArrivalsRowErrorOut]
    unmatched: list[dict[str, Any]]
    notes: list[str]


class RunCreateRequest(StrictModel):
    destination_id: str
    market_ids: list[str] = Field(min_length=3, max_length=40)
    arrivals_dataset_id: str | None = None


class RunCreatedResponse(BaseModel):
    run_id: str
    status: str


class RunCounters(BaseModel):
    qloo_live: int = 0
    qloo_cached: int = 0
    llm: int = 0
    tools: int = 0


class RunOut(BaseModel):
    run_id: str
    status: str
    phase: str | None
    orchestration: str | None
    orchestration_reason: str | None
    counters: RunCounters
    warnings: list[dict[str, Any]]
    shortlist: list[str]
    settings: dict[str, Any]
    error_code: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class ProfileEntityOut(BaseModel):
    entity_id: str
    name: str
    entity_type: str
    role: str
    similarity: float | None
    tags: list[dict[str, Any]]


class RunProfileResponse(BaseModel):
    destination_entity_id: str | None
    entities: list[ProfileEntityOut]
    tags: list[dict[str, Any]]
    warnings: list[str]


class MarketRow(BaseModel):
    market_id: str
    city: str
    country_code: str
    country_name: str
    region: str
    rank: int | None
    taste_score: float | None
    lift: float | None
    target_affinity: float | None
    baseline_affinity: float | None
    coverage: float
    confidence: Confidence
    arrivals_share: float | None
    arrivals_pct: float | None
    gap: float | None
    quadrant: Quadrant | None
    flags: list[str]
    angle_headline: str | None
    population_band: int


class MarketListResponse(BaseModel):
    markets: list[MarketRow]
    gap_enabled: bool
    gap_note: str | None
    thresholds: dict[str, float]
    population_correlation: float | None
    population_suspect: bool


class AudienceRow(BaseModel):
    dimension: str
    band: str
    label: str
    share: float | None
    baseline_share: float | None
    over_index: float | None
    source_call_id: str | None


class AngleEvidence(BaseModel):
    id: str
    kind: str
    label: str
    value: float | str | None
    source_call_id: str | None


class AngleOut(BaseModel):
    headline: str
    evidence: list[AngleEvidence]


class PartnerOut(BaseModel):
    partner_type: str
    entity_id: str
    name: str
    lift: float | None
    rank: int
    market_specific: bool


class MarketDetailResponse(BaseModel):
    market: MarketOut
    score: MarketRow
    audience: list[AudienceRow]
    audience_note: str | None
    angle: AngleOut | None
    partners: dict[str, list[PartnerOut]]
    brands: list[PartnerOut]
    arrivals_source_note: str | None
    allocation_share: float | None
    budget_amount: float | None


class AllocationRequest(StrictModel):
    total: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, default="USD")
    mode: Literal["grow_untapped", "defend_core"] = "grow_untapped"
    locks: dict[str, float] = Field(default_factory=dict)
    minimum_share: float = Field(default=0.05, ge=0, le=1)


class AllocationShareOut(BaseModel):
    market_id: str
    city: str
    share: float
    amount: float
    weight: float
    locked: bool


class AllocationResponse(BaseModel):
    total: float
    currency: str
    mode: str
    shares: list[AllocationShareOut]


class BriefSectionOut(BaseModel):
    heading: str
    body: str
    cited_evidence_ids: list[str]


class BriefOut(BaseModel):
    id: str
    market_id: str
    city: str
    source: str
    edited: bool
    model: str | None
    title: str
    summary: str
    sections: list[BriefSectionOut]
    evidence_ids: list[str]


class BriefUpdateRequest(StrictModel):
    title: str | None = Field(default=None, max_length=160)
    summary: str | None = Field(default=None, max_length=400)
    sections: list[BriefSectionOut] | None = None


class TraceItem(BaseModel):
    kind: Literal["qloo", "llm", "tool", "event"]
    at: datetime
    step: str
    summary: str
    detail: dict[str, Any]


class TraceResponse(BaseModel):
    items: list[TraceItem]


class DemoResponse(BaseModel):
    run_id: str
    destination: str
    status: str
    shortlist: list[str]
    headline: str
    sample: bool = True
