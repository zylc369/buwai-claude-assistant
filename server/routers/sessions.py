"""Session API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import SessionService


router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionCreate(BaseModel):
    user_id: int
    expires_in_hours: int = 24


class SessionResponse(BaseModel):
    id: int
    user_id: int
    token: str
    expires_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    session_data: SessionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new session."""
    service = SessionService(db)
    
    session = await service.create_session(
        user_id=session_data.user_id,
        expires_in_hours=session_data.expires_in_hours,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return {
        "id": session.id,
        "user_id": session.user_id,
        "token": session.token,
        "expires_at": str(session.expires_at)
    }


@router.delete("/{token}", status_code=204)
async def end_session(
    token: str,
    db: AsyncSession = Depends(get_db_session)
):
    """End a session."""
    service = SessionService(db)
    ended = await service.end_session(token)
    if not ended:
        raise HTTPException(status_code=404, detail="Session not found")
