"""Message service for business logic with AI integration."""

import json
from typing import List, Optional, Dict, Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Message
from repositories.message_repository import MessageRepository
from repositories.project_repository import ProjectRepository
from repositories.workspace_repository import WorkspaceRepository
from claude_client import ClaudeClient, ClaudeClientConfig
from pool import ClaudeClientPool
from utils.id_generator import generate_uuidv7
from utils.timestamp import get_timestamp_ms
from logger import get_logger

logger = get_logger(__name__)


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
        gmt_create: Optional[int] = None,
        gmt_modified: Optional[int] = None
    ) -> Message:
        """Create a new message.
        
        Args:
            message_unique_id: Unique identifier for the message.
            session_unique_id: Unique identifier of the parent session.
            data: Message data dictionary (will be stored as JSON).
            gmt_create: Creation timestamp (defaults to current time).
            gmt_modified: Update timestamp (defaults to current time).
            
        Returns:
            Created message instance.
        """
        logger.debug(f"create_message called with message_unique_id={message_unique_id}, session_unique_id={session_unique_id}")
        current_time = get_timestamp_ms()
        
        message = await self.message_repo.create(
            message_unique_id=message_unique_id,
            session_unique_id=session_unique_id,
            gmt_create=gmt_create or current_time,
            gmt_modified=gmt_modified or current_time,
            data=data
        )
        
        await self.session.commit()
        await self.session.refresh(message)
        
        logger.debug(f"create_message completed")
        return message
    
    async def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """Get a message by its primary key ID.
        
        Args:
            message_id: The primary key ID of the message.
            
        Returns:
            Message instance if found, None otherwise.
        """
        logger.debug(f"get_message_by_id called with message_id={message_id}")
        result = await self.message_repo.get_by_id(message_id)
        logger.debug(f"get_message_by_id completed, found={result is not None}")
        return result
    
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
        logger.debug(f"get_message_by_unique_id called with message_unique_id={message_unique_id}")
        result = await self.message_repo.get_by_unique_id(message_unique_id)
        logger.debug(f"get_message_by_unique_id completed, found={result is not None}")
        return result
    
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
        logger.debug(f"list_messages called with session_unique_id={session_unique_id}, offset={offset}, limit={limit}")
        result = await self.message_repo.list(
            session_unique_id=session_unique_id,
            offset=offset,
            limit=limit
        )
        logger.debug(f"list_messages completed, returned {len(result)} messages")
        return result
    
    async def list_messages_after_id(
        self,
        session_unique_id: str,
        last_message_id: int,
        limit: int = 100
    ) -> List[Message]:
        """List messages with id greater than last_message_id for incremental fetching.
        
        Args:
            session_unique_id: The unique identifier of the session.
            last_message_id: Only return messages with id > this value.
            limit: Maximum number of results (default: 100).
            
        Returns:
            List of messages with id > last_message_id, ordered by creation time.
        """
        logger.debug(f"list_messages_after_id called with session_unique_id={session_unique_id}, last_message_id={last_message_id}, limit={limit}")
        result = await self.message_repo.get_messages_after_id(
            session_unique_id=session_unique_id,
            last_message_id=last_message_id,
            limit=limit
        )
        logger.debug(f"list_messages_after_id completed, returned {len(result)} messages")
        return result
    
    def _extract_response_text(self, chunks: List[Any]) -> str:
        """Extract text content from AI response chunks.
        
        Args:
            chunks: List of response chunk objects from Claude API.
            
        Returns:
            Extracted text content as a string.
        """
        text_parts = []
        
        for chunk in chunks:
            if hasattr(chunk, 'content'):
                content = chunk.content
                if isinstance(content, list):
                    for item in content:
                        if hasattr(item, 'text'):
                            text_parts.append(item.text)
                        elif hasattr(item, 'thinking'):
                            text_parts.append(f"[Thinking: {item.thinking}]")
                elif isinstance(content, str):
                    text_parts.append(content)
            elif hasattr(chunk, 'text'):
                text_parts.append(chunk.text)
            elif hasattr(chunk, 'result'):
                text_parts.append(chunk.result)
            elif isinstance(chunk, str):
                text_parts.append(chunk)
        
        return "".join(text_parts)
    
    async def send_ai_prompt(
        self,
        prompt: str,
        session_unique_id: str,
        client_config: ClaudeClientConfig,
        project_unique_id: Optional[str] = None,
        workspace_unique_id: Optional[str] = None,
        pool: Optional[ClaudeClientPool] = None
    ) -> AsyncIterator[Any]:
        """Send a prompt to AI and yield streaming responses.

        Integrates with ClaudeClient to send prompts and receive streaming
        AI responses. Uses connection pooling if a pool is provided.
        Persists both user message and AI response to database.

        Args:
            prompt: The user prompt to send to AI.
            session_unique_id: Session identifier for conversation continuity.
            client_config: Configuration for ClaudeClient.
            project_unique_id: Optional project identifier for activity tracking.
            workspace_unique_id: Optional workspace identifier for activity tracking.
            pool: Optional connection pool for client reuse.

        Yields:
            Response messages from the AI as an async iterator.

        Raises:
            RuntimeError: If client connection fails.
        """
        logger.debug(f"send_ai_prompt called with session_unique_id={session_unique_id}")
        logger.info(f"AI operation: sending prompt of length {len(prompt)} characters")
        current_time = get_timestamp_ms()

        user_msg_id = f"user-{generate_uuidv7()}"
        logger.info(f"Business decision: creating user message {user_msg_id}")
        await self.message_repo.create(
            message_unique_id=user_msg_id,
            session_unique_id=session_unique_id,
            gmt_create=current_time,
            gmt_modified=current_time,
            data={"role": "user", "content": prompt}
        )
        await self.session.commit()

        if project_unique_id or workspace_unique_id:
            await self._update_latest_active_time(project_unique_id, workspace_unique_id, current_time)

        ai_chunks = []
        logger.info(f"AI operation: querying AI client (using pool={pool is not None})")

        try:
            if pool is not None:
                client = await pool.get_client(session_unique_id, client_config)
                try:
                    await client.query(prompt, session_unique_id)
                    async for response in await client.receive_response():
                        ai_chunks.append(response)
                        yield response
                finally:
                    await pool.release_client(session_unique_id)
            else:
                async with ClaudeClient(client_config) as client:
                    await client.query(prompt, session_unique_id)
                    async for response in await client.receive_response():
                        ai_chunks.append(response)
                        yield response

            ai_msg_id = f"assistant-{generate_uuidv7()}"
            ai_response_text = self._extract_response_text(ai_chunks)
            logger.info(f"AI operation: received response of length {len(ai_response_text)} characters")

            logger.info(f"Business decision: creating assistant message {ai_msg_id}")
            await self.message_repo.create(
                message_unique_id=ai_msg_id,
                session_unique_id=session_unique_id,
                gmt_create=current_time,
                gmt_modified=current_time,
                data={"role": "assistant", "content": ai_response_text}
            )
            await self.session.commit()

            logger.debug(f"send_ai_prompt completed")
        except Exception as e:
            logger.error(f"send_ai_prompt failed: {str(e)}")
            raise

    async def _update_latest_active_time(
        self,
        project_unique_id: Optional[str],
        workspace_unique_id: Optional[str],
        current_time: int
    ) -> None:
        """Update latest_active_time for project and workspace.

        Args:
            project_unique_id: Project identifier to update.
            workspace_unique_id: Workspace identifier to update.
            current_time: Current timestamp to set as latest_active_time.
        """
        project_repo = ProjectRepository(self.session)
        workspace_repo = WorkspaceRepository(self.session)

        if project_unique_id:
            project = await project_repo.get_by_unique_id(project_unique_id)
            if project:
                await project_repo.update(project, latest_active_time=current_time)
                logger.debug(f"Updated latest_active_time for project {project_unique_id}")

        if workspace_unique_id:
            workspace = await workspace_repo.get_by_unique_id(workspace_unique_id)
            if workspace:
                await workspace_repo.update(workspace, latest_active_time=current_time)
                logger.debug(f"Updated latest_active_time for workspace {workspace_unique_id}")
    
    async def count_messages(self, session_unique_id: str) -> int:
        """Count messages for a specific session.

        Args:
            session_unique_id: The unique identifier of the session.

        Returns:
            Number of messages in the session.
        """
        logger.debug(f"count_messages called with session_unique_id={session_unique_id}")
        result = await self.message_repo.count_by_session(session_unique_id)
        logger.debug(f"count_messages completed, found {result} messages")
        return result
    
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
            **kwargs: Additional fields to update (e.g., gmt_modified).

        Returns:
            Updated message instance if found, None otherwise.
        """
        logger.debug(f"update_message called with message_unique_id={message_unique_id}")
        message = await self.message_repo.get_by_unique_id(message_unique_id)
        if not message:
            logger.debug(f"update_message completed, message not found")
            return None

        update_data = kwargs.copy()
        if data is not None:
            update_data["data"] = json.dumps(data, ensure_ascii=False)
        if "gmt_modified" not in update_data:
            update_data["gmt_modified"] = get_timestamp_ms()

        logger.info(f"Business decision: updating message {message_unique_id}")
        updated = await self.message_repo.update(message, **update_data)
        await self.session.commit()
        await self.session.refresh(updated)

        logger.debug(f"update_message completed")
        return updated
    
    async def delete_message(self, message_unique_id: str) -> bool:
        """Delete a message by its unique identifier.

        Args:
            message_unique_id: The unique identifier of the message to delete.

        Returns:
            True if deleted, False if not found.
        """
        logger.debug(f"delete_message called with message_unique_id={message_unique_id}")
        message = await self.message_repo.get_by_unique_id(message_unique_id)
        if not message:
            logger.debug(f"delete_message completed, message not found")
            return False

        logger.info(f"Business decision: deleting message {message_unique_id}")
        await self.message_repo.delete(message)
        await self.session.commit()

        logger.debug(f"delete_message completed")
        return True
