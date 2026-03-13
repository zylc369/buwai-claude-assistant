"""Conversation Session API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import ConversationSessionService


router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionCreate(BaseModel):
    session_unique_id: str
    external_session_id: str
    project_unique_id: str
    workspace_unique_id: str
    directory: str
    title: str


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    directory: Optional[str] = None
    time_compacting: Optional[int] = None


class SessionResponse(BaseModel):
    id: int
    session_unique_id: str
    external_session_id: str
    sdk_session_id: Optional[str] = None
    project_unique_id: str
    workspace_unique_id: str
    directory: str
    title: str
    time_created: int
    time_updated: int
    time_compacting: Optional[int] = None
    time_archived: Optional[int] = None
    
    class Config:
        from_attributes = True


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new conversation session."""
    service = ConversationSessionService(db)
    session = await service.create_session(
        session_unique_id=session_data.session_unique_id,
        external_session_id=session_data.external_session_id,
        project_unique_id=session_data.project_unique_id,
        workspace_unique_id=session_data.workspace_unique_id,
        directory=session_data.directory,
        title=session_data.title,
    )
    return session


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    project_unique_id: Optional[str] = None,
    workspace_unique_id: Optional[str] = None,
    external_session_id: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db_session)
):
    """Get sessions with optional filters (excludes archived by default)."""
    service = ConversationSessionService(db)
    sessions = await service.list_sessions(
        project_unique_id=project_unique_id,
        workspace_unique_id=workspace_unique_id,
        external_session_id=external_session_id,
        offset=offset,
        limit=limit,
        include_archived=include_archived,
    )
    return sessions


@router.get("/{session_unique_id}", response_model=SessionResponse)
async def get_session(
    session_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific session by unique ID."""
    service = ConversationSessionService(db)
    session = await service.get_by_unique_id(session_unique_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/{session_unique_id}", response_model=SessionResponse)
async def update_session(
    session_unique_id: str,
    session_data: SessionUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a session."""
    service = ConversationSessionService(db)
    update_data = {k: v for k, v in session_data.model_dump().items() if v is not None}
    session = await service.update_session(session_unique_id, **update_data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_unique_id}", status_code=204)
async def delete_session(
    session_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a session (cascades to messages)."""
    service = ConversationSessionService(db)
    deleted = await service.delete_session(session_unique_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_unique_id}/archive", response_model=SessionResponse)
async def archive_session(
    session_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Archive a session."""
    service = ConversationSessionService(db)
    session = await service.archive_session(session_unique_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_unique_id}/unarchive", response_model=SessionResponse)
async def unarchive_session(
    session_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Unarchive a session."""
    service = ConversationSessionService(db)
    session = await service.unarchive_session(session_unique_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
