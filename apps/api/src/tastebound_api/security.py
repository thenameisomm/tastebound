from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import uuid
from typing import Annotated

from fastapi import Depends, Header, Query

from tastebound_api.db.database import get_session_factory, utcnow
from tastebound_api.db.tables import Workspace
from tastebound_api.errors import InvalidWorkspace
from tastebound_api.settings import get_settings


def _sign(workspace_id: str) -> str:
    secret = get_settings().session_secret.encode("utf-8")
    return hmac.new(secret, workspace_id.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def issue_token(workspace_id: str) -> str:
    raw = f"{workspace_id}.{_sign(workspace_id)}".encode()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def parse_token(token: str) -> str:
    padded = token + "=" * (-len(token) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
        raise InvalidWorkspace() from exc
    workspace_id, _, signature = raw.partition(".")
    if not workspace_id or not signature:
        raise InvalidWorkspace()
    if not hmac.compare_digest(signature, _sign(workspace_id)):
        raise InvalidWorkspace()
    return workspace_id


def new_workspace_id() -> str:
    return str(uuid.uuid4())


async def _workspace_from_token(token: str) -> str:
    workspace_id = parse_token(token)
    session_factory = get_session_factory()
    async with session_factory() as session:
        row = await session.get(Workspace, workspace_id)
        if row is None:
            session.add(Workspace(id=workspace_id, kind="anon"))
        else:
            row.last_seen_at = utcnow()
        await session.commit()
    return workspace_id


async def workspace_id_dependency(
    token_header: Annotated[str | None, Header(alias="X-Workspace-Token")] = None,
    token_query: Annotated[str | None, Query(alias="token")] = None,
) -> str:
    token = token_header or token_query
    if not token:
        raise InvalidWorkspace()
    return await _workspace_from_token(token)


WorkspaceId = Annotated[str, Depends(workspace_id_dependency)]
