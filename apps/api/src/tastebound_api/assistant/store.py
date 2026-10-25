from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime

from tastebound_api.assistant.models import Conversation, EvidenceItem, StoredMessage
from tastebound_api.errors import AssistantBusy, ConversationNotFound

_CONVERSATIONS: dict[str, Conversation] = {}


def _now() -> datetime:
    return datetime.now(UTC)


def _sweep(ttl_seconds: int) -> None:
    cutoff = time.monotonic() - ttl_seconds
    expired = [key for key, value in _CONVERSATIONS.items() if value.last_used < cutoff]
    for key in expired:
        _CONVERSATIONS.pop(key, None)


def create(
    *,
    workspace_id: str,
    run_id: str,
    focus_market_id: str | None,
    ttl_seconds: int,
    max_conversations: int,
) -> Conversation:
    _sweep(ttl_seconds)
    if len(_CONVERSATIONS) >= max_conversations:
        oldest = min(_CONVERSATIONS.values(), key=lambda item: item.last_used)
        _CONVERSATIONS.pop(oldest.id, None)
    now = _now()
    conversation = Conversation(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        run_id=run_id,
        focus_market_id=focus_market_id,
        created_at=now,
        updated_at=now,
        last_used=time.monotonic(),
    )
    _CONVERSATIONS[conversation.id] = conversation
    return conversation


def get(
    *,
    workspace_id: str,
    run_id: str,
    conversation_id: str,
    ttl_seconds: int,
) -> Conversation:
    _sweep(ttl_seconds)
    conversation = _CONVERSATIONS.get(conversation_id)
    if (
        conversation is None
        or conversation.workspace_id != workspace_id
        or conversation.run_id != run_id
    ):
        raise ConversationNotFound()
    conversation.last_used = time.monotonic()
    return conversation


def try_begin(conversation: Conversation) -> None:
    if conversation.busy:
        raise AssistantBusy()
    conversation.busy = True


def finish(conversation: Conversation) -> None:
    conversation.busy = False


def append_exchange(
    conversation: Conversation,
    *,
    question: str,
    answer: str,
    evidence: list[EvidenceItem],
) -> StoredMessage:
    now = _now()
    conversation.messages.append(
        StoredMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=question,
            evidence=[],
            created_at=now,
        )
    )
    assistant_message = StoredMessage(
        id=str(uuid.uuid4()),
        role="assistant",
        content=answer,
        evidence=evidence,
        created_at=now,
    )
    conversation.messages.append(assistant_message)
    conversation.updated_at = now
    return assistant_message


def reset() -> None:
    _CONVERSATIONS.clear()
