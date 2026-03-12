"""Session repository for database operations."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Session
from repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Repository for Session model operations.
    
    Provides session-specific database operations on top of base CRUD.
    
    Attributes:
        model: The Session model class.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize SessionRepository with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session)
        self.model = Session
    
    async def get_by_token(self, token: str) -> Optional[Session]:
        """Get a session by token.
        
        Args:
            token: Session token.
            
        Returns:
            Session instance if found, None otherwise.
        """
        result = await self.session.execute(
            select(Session).where(Session.token == token)
        )
        return result.scalar_one_or_none()
    
    async def get_valid_sessions_for_user(self, user_id: int) -> List[Session]:
        """Get all valid (non-expired) sessions for a user.
        
        Args:
            user_id: User ID to filter by.
            
        Returns:
            List of valid sessions for the user.
        """
        result = await self.session.execute(
            select(Session).where(
                and_(
                    Session.user_id == user_id,
                    Session.expires_at > datetime.utcnow()
                )
            )
        )
        return list(result.scalars().all())
    
    async def delete_expired_sessions(self) -> int:
        """Delete all expired sessions.
        
        Removes sessions where expires_at is in the past.
        
        Returns:
            Number of sessions deleted.
        """
        # Find expired sessions
        result = await self.session.execute(
            select(Session).where(Session.expires_at <= datetime.utcnow())
        )
        expired_sessions = result.scalars().all()
        
        # Delete them
        count = 0
        for session in expired_sessions:
            await self.session.delete(session)
            count += 1
        
        return count
    
    async def is_valid_token(self, token: str) -> bool:
        """Check if a token is valid (exists and not expired).
        
        Args:
            token: Session token to validate.
            
        Returns:
            True if token is valid, False otherwise.
        """
        result = await self.session.execute(
            select(Session).where(
                and_(
                    Session.token == token,
                    Session.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def delete_sessions_for_user(self, user_id: int) -> int:
        """Delete all sessions for a specific user.
        
        Args:
            user_id: User ID to delete sessions for.
            
        Returns:
            Number of sessions deleted.
        """
        result = await self.session.execute(
            select(Session).where(Session.user_id == user_id)
        )
        sessions = result.scalars().all()
        
        count = 0
        for session in sessions:
            await self.session.delete(session)
            count += 1
        
        return count
