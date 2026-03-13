"""Message repository for database operations."""

import json
from typing import List, Optional, Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Message
from repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model operations.
    
    Provides message-specific database operations on top of base CRUD.
    
    Attributes:
        model: The Message model class.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize MessageRepository with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session)
        self.model = Message
    
    async def get_by_session_unique_id(
        self,
        session_unique_id: str,
        offset: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """Get all messages for a specific session with pagination.
        
        Args:
            session_unique_id: The unique identifier of the session.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            
        Returns:
            List of messages belonging to the session.
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.session_unique_id == session_unique_id)
            .order_by(Message.time_created)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_unique_id(self, message_unique_id: str) -> Optional[Message]:
        """Get a message by its unique identifier.
        
        Args:
            message_unique_id: The unique identifier of the message.
            
        Returns:
            Message instance if found, None otherwise.
        """
        result = await self.session.execute(
            select(Message).where(Message.message_unique_id == message_unique_id)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        session_unique_id: str,
        offset: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """List messages for a session with pagination.
        
        This is an alias for get_by_session_unique_id for API consistency.
        
        Args:
            session_unique_id: The unique identifier of the session.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            
        Returns:
            List of messages belonging to the session.
        """
        return await self.get_by_session_unique_id(session_unique_id, offset, limit)
    
    async def create(
        self,
        message_unique_id: str,
        session_unique_id: str,
        time_created: int,
        time_updated: int,
        data: Dict[str, Any]
    ) -> Message:
        """Create a new message with JSON data.
        
        Args:
            message_unique_id: The unique identifier for the message.
            session_unique_id: The unique identifier of the parent session.
            time_created: Creation timestamp (Unix epoch).
            time_updated: Update timestamp (Unix epoch).
            data: Message data dictionary (will be stored as JSON string).
            
        Returns:
            Created message instance.
        """
        instance = self.model(
            message_unique_id=message_unique_id,
            session_unique_id=session_unique_id,
            time_created=time_created,
            time_updated=time_updated,
            data=json.dumps(data) if isinstance(data, dict) else data
        )
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def count_by_session(self, session_unique_id: str) -> int:
        """Count messages for a specific session.
        
        Args:
            session_unique_id: The unique identifier of the session.
            
        Returns:
            Number of messages in the session.
        """
        result = await self.session.execute(
            select(Message).where(Message.session_unique_id == session_unique_id)
        )
        return len(result.scalars().all())
