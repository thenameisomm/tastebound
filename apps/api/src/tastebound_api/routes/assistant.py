from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Query, Request

from tastebound_api.assistant import store
from tastebound_api.assistant.context import AssistantContext, build_context
from tastebound_api.assistant.models import Conversation, EvidenceItem
from tastebound_api.assistant.service import answer_question
from tastebound_api.errors import (
    AssistantNotReady,
    AssistantRateLimited,
    AssistantUnavailable,
    RateLimited,
    ValidationProblem,
)
from tastebound_api.llm.provider import get_provider
from tastebound_api.ratelimit import check, hash_identifier
from tastebound_api.routes.runs import _get_run
from tastebound_api.schemas import (
    AssistantAnswerResponse,
    AssistantBootstrapResponse,
    AssistantConversationCreate,
    AssistantConversationResponse,
    AssistantEvidenceOut,
    AssistantMessageOut,
    AssistantMessageRequest,
)
from tastebound_api.security import WorkspaceId
from tastebound_api.settings import Settings, get_settings

router = APIRouter(prefix="/v1/runs/{run_id}/assistant", tags=["assistant"])


def get_assistant_provider(settings: Settings) -> Any:
    return get_provider(settings)


def _evidence_out(item: EvidenceItem) -> AssistantEvidenceOut:
    return AssistantEvidenceOut(
        id=item.id,
        kind=item.kind,
        label=item.label,
        detail=item.detail,
        href=item.href,
        source_call_id=item.source_call_id,
    )


def _conversation_out(conversation: Conversation) -> AssistantConversationResponse:
    return AssistantConversationResponse(
        conversation_id=conversation.id,
        run_id=conversation.run_id,
        focus_market_id=conversation.focus_market_id,
        messages=[
            AssistantMessageOut(
                id=message.id,
                role=message.role,  # type: ignore[arg-type]
                content=message.content,
                evidence=[_evidence_out(item) for item in message.evidence],
                created_at=message.created_at,
            )
            for message in conversation.messages
        ],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _disabled_notice(settings: Settings, enabled: bool, context: AssistantContext) -> str | None:
    if not settings.assistant_enabled:
        return "The results assistant is disabled in this deployment."
    if not enabled:
        return "The results assistant needs a configured model provider."
    return context.notice


def _require_ready(settings: Settings, context: AssistantContext) -> None:
    if not settings.assistant_enabled:
        raise AssistantUnavailable("The results assistant is disabled in this deployment.")
    if not context.ready:
        raise AssistantNotReady()


@router.get("", response_model=AssistantBootstrapResponse)
async def assistant_bootstrap(
    run_id: str,
    workspace_id: WorkspaceId,
    focus_market_id: Annotated[str | None, Query()] = None,
) -> AssistantBootstrapResponse:
    settings = get_settings()
    run = await _get_run(run_id, workspace_id)
    context = await build_context(
        run=run,
        focus_market_id=focus_market_id,
        max_context_chars=settings.assistant_max_context_chars,
    )
    provider = get_assistant_provider(settings)
    enabled = bool(settings.assistant_enabled and provider is not None)
    return AssistantBootstrapResponse(
        enabled=enabled,
        ready=bool(enabled and context.ready),
        model=provider.model if provider is not None else None,
        focus_market_id=context.focus_market_id,
        suggested_questions=context.suggested_questions,
        notice=_disabled_notice(settings, enabled, context),
        max_message_chars=settings.assistant_max_message_chars,
        conversation_ttl_minutes=settings.assistant_conversation_ttl_minutes,
    )


@router.post("/conversations", response_model=AssistantConversationResponse, status_code=201)
async def create_conversation(
    run_id: str,
    workspace_id: WorkspaceId,
    payload: AssistantConversationCreate,
) -> AssistantConversationResponse:
    settings = get_settings()
    run = await _get_run(run_id, workspace_id)
    provider = get_assistant_provider(settings)
    if not settings.assistant_enabled or provider is None:
        raise AssistantUnavailable()
    context = await build_context(
        run=run,
        focus_market_id=payload.focus_market_id,
        max_context_chars=settings.assistant_max_context_chars,
    )
    _require_ready(settings, context)
    conversation = store.create(
        workspace_id=workspace_id,
        run_id=run.id,
        focus_market_id=payload.focus_market_id,
        ttl_seconds=settings.assistant_conversation_ttl_minutes * 60,
        max_conversations=settings.assistant_max_conversations,
    )
    return _conversation_out(conversation)


@router.get("/conversations/{conversation_id}", response_model=AssistantConversationResponse)
async def get_conversation(
    run_id: str,
    conversation_id: str,
    workspace_id: WorkspaceId,
) -> AssistantConversationResponse:
    settings = get_settings()
    run = await _get_run(run_id, workspace_id)
    conversation = store.get(
        workspace_id=workspace_id,
        run_id=run.id,
        conversation_id=conversation_id,
        ttl_seconds=settings.assistant_conversation_ttl_minutes * 60,
    )
    return _conversation_out(conversation)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AssistantAnswerResponse,
    status_code=201,
)
async def send_message(
    run_id: str,
    conversation_id: str,
    workspace_id: WorkspaceId,
    payload: AssistantMessageRequest,
    request: Request,
) -> AssistantAnswerResponse:
    settings = get_settings()
    run = await _get_run(run_id, workspace_id)
    question = payload.message.strip()
    if not question:
        raise ValidationProblem("Write a question before sending.")
    if len(question) > settings.assistant_max_message_chars:
        raise ValidationProblem(
            f"Keep the question under {settings.assistant_max_message_chars} characters."
        )

    conversation = store.get(
        workspace_id=workspace_id,
        run_id=run.id,
        conversation_id=conversation_id,
        ttl_seconds=settings.assistant_conversation_ttl_minutes * 60,
    )
    focus_market_id = payload.focus_market_id or conversation.focus_market_id
    context = await build_context(
        run=run,
        focus_market_id=focus_market_id,
        max_context_chars=settings.assistant_max_context_chars,
    )
    _require_ready(settings, context)
    provider = get_assistant_provider(settings)
    if provider is None:
        raise AssistantUnavailable()

    ip_hash = hash_identifier(request.client.host if request.client else "unknown")
    try:
        check(
            "assistant_ip",
            ip_hash,
            limit=settings.assistant_messages_per_ip_per_hour,
            window_seconds=3600,
        )
        check(
            "assistant_workspace",
            workspace_id,
            limit=settings.assistant_messages_per_workspace_per_hour,
            window_seconds=3600,
        )
    except RateLimited as exc:
        raise AssistantRateLimited() from exc

    store.try_begin(conversation)
    try:
        draft, evidence, model = await answer_question(
            provider=provider,
            context=context,
            conversation=conversation,
            question=question,
            settings=settings,
        )
        if payload.focus_market_id:
            conversation.focus_market_id = payload.focus_market_id
        message = store.append_exchange(
            conversation,
            question=question,
            answer=draft.answer,
            evidence=evidence,
        )
    finally:
        store.finish(conversation)

    return AssistantAnswerResponse(
        conversation_id=conversation.id,
        message_id=message.id,
        answer=draft.answer,
        evidence=[_evidence_out(item) for item in evidence],
        followups=draft.followups,
        model=model,
        created_at=message.created_at,
    )
