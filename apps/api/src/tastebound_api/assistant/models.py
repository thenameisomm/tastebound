from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    kind: str
    label: str
    detail: str
    href: str
    source_call_id: str | None = None


@dataclass
class StoredMessage:
    id: str
    role: str
    content: str
    evidence: list[EvidenceItem]
    created_at: datetime


@dataclass
class Conversation:
    id: str
    workspace_id: str
    run_id: str
    focus_market_id: str | None
    messages: list[StoredMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_used: float = 0.0
    busy: bool = False
