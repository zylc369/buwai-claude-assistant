"""Message service for business logic with AI integration."""

import time
import json
from typing import List, Optional, Dict, Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Message
from repositories.message_repository import MessageRepository
from claude_client import ClaudeClient, ClaudeClientConfig
from pool import ClaudeClientPool


class MessageService:
    """Service layer for message management with AI integration.
    
    Provides business logic for message CRUD operations and AI prompt handling.
    Wraps MessageRepository and integrates with ClaudeClient for AI responses.
    
    Attributes:
        session: SQLAlchemy async session for database operations.
        message_repo: MessageRepository instance for data access.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize MessageService with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.message_repo = MessageRepository(session)
    
    async def create_message(
        self,
        message_unique_id: str,
        session_unique_id: str,
        data: Dict[str, Any],
        time_created: Optional[int] = None,
        time_updated: Optional[int] = None
    ) -> Message:
        """Create a new message.
        
        Args:
            message_unique_id: Unique identifier for the message.
            session_unique_id: Unique identifier of the parent session.
            data: Message data dictionary (will be stored as JSON).
            time_created: Creation timestamp (defaults to current time).
            time_updated: Update timestamp (defaults to current time).
            
        Returns:
            Created message instance.
        """
        current_time = int(time.time())
        
        message = await self.message_repo.create(
            message_unique_id=message_unique_id,
            session_unique_id=session_unique_id,
            time_created=time_created or current_time,
            time_updated=time_updated or current_time,
            data=data
        )
        
        await self.session.commit()
        await self.session.refresh(message)
        
        return message
    
    async def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """Get a message by its primary key ID.
        
        Args:
            message_id: The primary key ID of the message.
            
        Returns:
            Message instance if found, None otherwise.
        """
        return await self.message_repo.get_by_id(message_id)
    
    async def get_message_by_unique_id(
        self,
        message_unique_id: str
    ) -> Optional[Message]:
        """Get a message by its unique identifier.
        
        Args:
            message_unique_id: The unique identifier of the message.
            
        Returns:
            Message instance if found, None otherwise.
        """
        return await self.message_repo.get_by_unique_id(message_unique_id)
    
    async def list_messages(
        self,
        session_unique_id: str,
        offset: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """List messages for a session with pagination.
        
        Args:
            session_unique_id: The unique identifier of the session.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            
        Returns:
            List of messages belonging to the session, ordered by creation time.
        """
        return await self.message_repo.list(
            session_unique_id=session_unique_id,
            offset=offset,
            limit=limit
        )
    
    async def send_ai_prompt(
        self,
        prompt: str,
        session_unique_id: str,
        client_config: ClaudeClientConfig,
        pool: Optional[ClaudeClientPool] = None
    ) -> AsyncIterator[Any]:
        """Send a prompt to AI and yield streaming responses.
        
        Integrates with ClaudeClient to send prompts and receive streaming
        AI responses. Uses connection pooling if a pool is provided.
        
        Args:
            prompt: The user prompt to send to AI.
            session_unique_id: Session identifier for conversation continuity.
            client_config: Configuration for ClaudeClient.
            pool: Optional connection pool for client reuse.
            
        Yields:
            Response messages from the AI as an async iterator.
            
        Raises:
            RuntimeError: If client connection fails.
        """
        if pool is not None:
            # Use connection pool for client reuse
            client = await pool.get_client(session_unique_id, client_config)
            try:
                await client.query(prompt, session_unique_id)
                async for response in await client.receive_response():
                    yield response
            finally:
                await pool.release_client(session_unique_id)
        else:
            # Create a fresh client connection
            async with ClaudeClient(client_config) as client:
                await client.query(prompt, session_unique_id)
                async for response in await client.receive_response():
                    yield response
    
    async def count_messages(self, session_unique_id: str) -> int:
        """Count messages for a specific session.
        
        Args:
            session_unique_id: The unique identifier of the session.
            
        Returns:
            Number of messages in the session.
        """
        return await self.message_repo.count_by_session(session_unique_id)
    
    async def update_message(
        self,
        message_unique_id: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Message]:
        """Update a message's data.
        
        Args:
            message_unique_id: The unique identifier of the message to update.
            data: New message data dictionary (optional).
            **kwargs: Additional fields to update (e.g., time_updated).
            
        Returns:
            Updated message instance if found, None otherwise.
        """
        message = await self.message_repo.get_by_unique_id(message_unique_id)
        if not message:
            return None
        
        update_data = kwargs.copy()
        if data is not None:
            update_data["data"] = json.dumps(data)
        if "time_updated" not in update_data:
            update_data["time_updated"] = int(time.time())
        
        updated = await self.message_repo.update(message, **update_data)
        await self.session.commit()
        await self.session.refresh(updated)
        
        return updated
    
    async def delete_message(self, message_unique_id: str) -> bool:
        """Delete a message by its unique identifier.
        
        Args:
            message_unique_id: The unique identifier of the message to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        message = await self.message_repo.get_by_unique_id(message_unique_id)
        if not message:
            return False
        
        await self.message_repo.delete(message)
        await self.session.commit()
        
        return True
