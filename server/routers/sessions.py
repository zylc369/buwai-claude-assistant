"""Conversation Session API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import ConversationSessionService
from logger import get_logger


router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = get_logger(__name__)


class SessionCreate(BaseModel):
    session_unique_id: str
    external_session_id: str
    project_unique_id: str
    workspace_unique_id: str
    directory: str
    title: str
    test: bool = False


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
    gmt_create: int
    gmt_modified: int
    time_compacting: Optional[int] = None
    time_archived: Optional[int] = None
    
    class Config:
        from_attributes = True


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    request: Request,
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data")
):
    """Create a new conversation session."""
    logger.info(f"create_session called: {request.method} {request.url.path}")
    logger.debug(f"params: session_unique_id={session_data.session_unique_id}, project_unique_id={session_data.project_unique_id}")

    service = ConversationSessionService(db)
    session = await service.create_session(
        session_unique_id=session_data.session_unique_id,
        external_session_id=session_data.external_session_id,
        project_unique_id=session_data.project_unique_id,
        workspace_unique_id=session_data.workspace_unique_id,
        directory=session_data.directory,
        title=session_data.title,
        test=test,
    )

    logger.info(f"create_session completed: status=201")
    return session


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    request: Request,
    project_unique_id: Optional[str] = None,
    workspace_unique_id: Optional[str] = None,
    external_session_id: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data")
):
    """Get sessions with optional filters (excludes archived by default)."""
    logger.info(f"list_sessions called: {request.method} {request.url.path}")
    logger.debug(f"params: project_unique_id={project_unique_id}, workspace_unique_id={workspace_unique_id}, offset={offset}, limit={limit}")

    service = ConversationSessionService(db)
    sessions = await service.list_sessions(
        project_unique_id=project_unique_id,
        workspace_unique_id=workspace_unique_id,
        external_session_id=external_session_id,
        offset=offset,
        limit=limit,
        include_archived=include_archived,
        test=test,
    )

    logger.info(f"list_sessions completed: status=200")
    return sessions


@router.get("/{session_unique_id}", response_model=SessionResponse)
async def get_session(
    request: Request,
    session_unique_id: str,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data")
):
    """Get a specific session by unique ID."""
    logger.info(f"get_session called: {request.method} {request.url.path}")
    logger.debug(f"params: session_unique_id={session_unique_id}")

    service = ConversationSessionService(db)
    session = await service.get_by_unique_id(session_unique_id, test=test)
    if not session:
        logger.error(f"get_session failed: Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info(f"get_session completed: status=200")
    return session


@router.put("/{session_unique_id}", response_model=SessionResponse)
async def update_session(
    request: Request,
    session_unique_id: str,
    session_data: SessionUpdate,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data")
):
    """Update a session."""
    logger.info(f"update_session called: {request.method} {request.url.path}")
    logger.debug(f"params: session_unique_id={session_unique_id}")

    service = ConversationSessionService(db)
    update_data = {k: v for k, v in session_data.model_dump().items() if v is not None}
    session = await service.update_session(session_unique_id, test=test, **update_data)
    if not session:
        logger.error(f"update_session failed: Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info(f"update_session completed: status=200")
    return session


@router.delete("/{session_unique_id}", status_code=204)
async def delete_session(
    request: Request,
    session_unique_id: str,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data")
):
    """Delete a session (cascades to messages)."""
    logger.info(f"delete_session called: {request.method} {request.url.path}")
    logger.debug(f"params: session_unique_id={session_unique_id}")

    service = ConversationSessionService(db)
    deleted = await service.delete_session(session_unique_id, test=test)
    if not deleted:
        logger.error(f"delete_session failed: Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info(f"delete_session completed: status=204")


@router.post("/{session_unique_id}/archive", response_model=SessionResponse)
async def archive_session(
    request: Request,
    session_unique_id: str,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data")
):
    """Archive a session."""
    logger.info(f"archive_session called: {request.method} {request.url.path}")
    logger.debug(f"params: session_unique_id={session_unique_id}")

    service = ConversationSessionService(db)
    session = await service.archive_session(session_unique_id, test=test)
    if not session:
        logger.error(f"archive_session failed: Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info(f"archive_session completed: status=200")
    return session


@router.post("/{session_unique_id}/unarchive", response_model=SessionResponse)
async def unarchive_session(
    request: Request,
    session_unique_id: str,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data")
):
    """Unarchive a session."""
    logger.info(f"unarchive_session called: {request.method} {request.url.path}")
    logger.debug(f"params: session_unique_id={session_unique_id}")

    service = ConversationSessionService(db)
    session = await service.unarchive_session(session_unique_id, test=test)
    if not session:
        logger.error(f"unarchive_session failed: Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    logger.info(f"unarchive_session completed: status=200")
    return session
