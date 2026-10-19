from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Header

from tastebound_api.db.database import get_session_factory
from tastebound_api.db.tables import Workspace
from tastebound_api.errors import InvalidWorkspace
from tastebound_api.schemas import WorkspaceSessionResponse
from tastebound_api.security import issue_token, parse_token

router = APIRouter(prefix="/v1/workspaces", tags=["workspaces"])


@router.post("/session", response_model=WorkspaceSessionResponse)
async def create_session(
    x_workspace_token: Annotated[str | None, Header(alias="X-Workspace-Token")] = None,
) -> WorkspaceSessionResponse:
    workspace_id: str | None = None
    if x_workspace_token:
        try:
            workspace_id = parse_token(x_workspace_token)
        except InvalidWorkspace:
            workspace_id = None
    created_at = datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        row = await session.get(Workspace, workspace_id) if workspace_id else None
        if row is None:
            workspace_id = workspace_id or str(uuid.uuid4())
            row = Workspace(id=workspace_id, kind="anon")
            session.add(row)
            await session.flush()
        else:
            workspace_id = row.id
            row.last_seen_at = datetime.now(UTC)
        created_at = row.created_at or created_at
        await session.commit()
    if workspace_id is None:
        workspace_id = str(uuid.uuid4())
    return WorkspaceSessionResponse(
        workspace_token=issue_token(workspace_id), created_at=created_at
    )
