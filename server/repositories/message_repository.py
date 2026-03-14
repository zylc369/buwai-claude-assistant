"""Message repository for database operations."""

import json
from typing import List, Optional, Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Message
from repositories.base import BaseRepository
from logger import get_logger

logger = get_logger(__name__)


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
        logger.debug("MessageRepository initialized")
    
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
        try:
            logger.debug(f"get_by_session_unique_id called with session_unique_id={session_unique_id}, offset={offset}, limit={limit}")
            result = await self.session.execute(
                select(Message)
                .where(Message.session_unique_id == session_unique_id)
                .order_by(Message.gmt_create)
                .offset(offset)
                .limit(limit)
            )
            messages = list(result.scalars().all())
            logger.debug(f"get_by_session_unique_id returned {len(messages)} messages")
            return messages
        except Exception as e:
            logger.error(f"get_by_session_unique_id failed: {str(e)}")
            raise
    
    async def get_by_unique_id(self, message_unique_id: str) -> Optional[Message]:
        """Get a message by its unique identifier.
        
        Args:
            message_unique_id: The unique identifier of the message.
            
        Returns:
            Message instance if found, None otherwise.
        """
        try:
            logger.debug(f"get_by_unique_id called with message_unique_id={message_unique_id}")
            result = await self.session.execute(
                select(Message).where(Message.message_unique_id == message_unique_id)
            )
            message = result.scalar_one_or_none()
            logger.debug(f"get_by_unique_id returned {type(message).__name__ if message else 'None'}")
            return message
        except Exception as e:
            logger.error(f"get_by_unique_id failed: {str(e)}")
            raise
    
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
        logger.debug(f"list called with session_unique_id={session_unique_id}, offset={offset}, limit={limit}")
        return await self.get_by_session_unique_id(session_unique_id, offset, limit)
    
    async def create(
        self,
        message_unique_id: str,
        session_unique_id: str,
        gmt_create: int,
        gmt_modified: int,
        data: Dict[str, Any]
    ) -> Message:
        """Create a new message with JSON data.
        
        Args:
            message_unique_id: The unique identifier for the message.
            session_unique_id: The unique identifier of the parent session.
            gmt_create: Creation timestamp (Unix epoch).
            gmt_modified: Update timestamp (Unix epoch).
            data: Message data dictionary (will be stored as JSON string).
            
        Returns:
            Created message instance.
        """
        try:
            logger.debug(f"create called with message_unique_id={message_unique_id}, session_unique_id={session_unique_id}, gmt_create={gmt_create}, gmt_modified={gmt_modified}")
            instance = self.model(
                message_unique_id=message_unique_id,
                session_unique_id=session_unique_id,
                gmt_create=gmt_create,
                gmt_modified=gmt_modified,
                data=json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else data
            )
            self.session.add(instance)
            await self.session.flush()
            logger.debug(f"create returned message with id={instance.id}")
            return instance
        except Exception as e:
            logger.error(f"create failed: {str(e)}")
            raise
    
    async def get_messages_after_id(
        self,
        session_unique_id: str,
        last_message_id: int,
        limit: int = 100
    ) -> List[Message]:
        """Get messages with id greater than last_message_id for incremental fetching.
        
        Args:
            session_unique_id: The unique identifier of the session.
            last_message_id: Only return messages with id > this value.
            limit: Maximum number of results (default: 100).
            
        Returns:
            List of messages with id > last_message_id, ordered by gmt_create.
        """
        try:
            logger.debug(f"get_messages_after_id called with session_unique_id={session_unique_id}, last_message_id={last_message_id}, limit={limit}")
            result = await self.session.execute(
                select(Message)
                .where(Message.session_unique_id == session_unique_id)
                .where(Message.id > last_message_id)
                .order_by(Message.gmt_create)
                .limit(limit)
            )
            messages = list(result.scalars().all())
            logger.debug(f"get_messages_after_id returned {len(messages)} messages")
            return messages
        except Exception as e:
            logger.error(f"get_messages_after_id failed: {str(e)}")
            raise
    
    async def count_by_session(self, session_unique_id: str) -> int:
        """Count messages for a specific session.
        
        Args:
            session_unique_id: The unique identifier of the session.
            
        Returns:
            Number of messages in the session.
        """
        try:
            logger.debug(f"count_by_session called with session_unique_id={session_unique_id}")
            result = await self.session.execute(
                select(Message).where(Message.session_unique_id == session_unique_id)
            )
            count = len(result.scalars().all())
            logger.debug(f"count_by_session returned {count}")
            return count
        except Exception as e:
            logger.error(f"count_by_session failed: {str(e)}")
            raise
