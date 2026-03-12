"""Session service for authentication management."""

from datetime import datetime, timedelta
from typing import Optional
import secrets
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Session
from repositories.session_repository import SessionRepository


class SessionService:
    """Service layer for session management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.session_repo = SessionRepository(session)
    
    async def create_session(
        self,
        user_id: int,
        expires_in_hours: int = 24,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Session:
        """Create a new session for a user."""
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Create session
        session = await self.session_repo.create(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        await self.session.commit()
        await self.session.refresh(session)
        
        return session
    
    async def validate_session(self, token: str) -> Optional[Session]:
        """Validate a session token."""
        return await self.session_repo.get_by_token(token) if await self.session_repo.is_valid_token(token) else None
    
    async def end_session(self, token: str) -> bool:
        """End a session by token."""
        session = await self.session_repo.get_by_token(token)
        if not session:
            return False
        
        await self.session_repo.delete(session)
        await self.session.commit()
        
        return True
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions."""
        count = await self.session_repo.delete_expired_sessions()
        await self.session.commit()
        return count
