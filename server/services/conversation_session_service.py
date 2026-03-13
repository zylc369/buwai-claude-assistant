"""Conversation Session service for business logic."""

import time
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Session
from repositories.conversation_session_repository import ConversationSessionRepository


class ConversationSessionService:
    """Service layer for conversation session management.
    
    Provides business logic for session operations, wrapping the
    ConversationSessionRepository with additional functionality like timestamp
    management and transaction handling.
    
    Attributes:
        session: SQLAlchemy async session.
        session_repo: ConversationSessionRepository instance.
    
    Example:
        async with async_session() as session:
            service = ConversationSessionService(session)
            session = await service.create_session(
                session_unique_id="sess-001",
                project_unique_id="proj-001",
                workspace_unique_id="ws-001",
                directory="/path/to/dir",
                title="My Session"
            )
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize ConversationSessionService with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.session_repo = ConversationSessionRepository(session)
    
    async def create_session(
        self,
        session_unique_id: str,
        project_unique_id: str,
        workspace_unique_id: str,
        directory: str,
        title: str,
        time_compacting: Optional[int] = None,
        time_archived: Optional[int] = None,
    ) -> Session:
        """Create a new conversation session.
        
        Args:
            session_unique_id: Unique identifier for the session.
            project_unique_id: The unique identifier of the project.
            workspace_unique_id: The unique identifier of the workspace.
            directory: The working directory path.
            title: The session title.
            time_compacting: Optional compacting timestamp.
            time_archived: Optional archived timestamp.
            
        Returns:
            Created Session instance.
        """
        current_time = int(time.time())
        
        session = await self.session_repo.create(
            session_unique_id=session_unique_id,
            project_unique_id=project_unique_id,
            workspace_unique_id=workspace_unique_id,
            directory=directory,
            title=title,
            time_created=current_time,
            time_updated=current_time,
            time_compacting=time_compacting,
            time_archived=time_archived,
        )
        
        await self.session.commit()
        await self.session.refresh(session)
        
        return session
    
    async def get_by_unique_id(self, session_unique_id: str) -> Optional[Session]:
        """Get a session by its unique identifier.
        
        Args:
            session_unique_id: The session's unique identifier.
            
        Returns:
            Session instance if found, None otherwise.
        """
        return await self.session_repo.get_by_unique_id(session_unique_id)
    
    async def list_sessions(
        self,
        project_unique_id: Optional[str] = None,
        workspace_unique_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        include_archived: bool = False,
    ) -> List[Session]:
        """List sessions with pagination and optional filters.
        
        Args:
            project_unique_id: Optional filter by project unique ID.
            workspace_unique_id: Optional filter by workspace unique ID.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            include_archived: Whether to include archived sessions (default: False).
            
        Returns:
            List of sessions matching the criteria.
        """
        return await self.session_repo.list(
            project_unique_id=project_unique_id,
            workspace_unique_id=workspace_unique_id,
            offset=offset,
            limit=limit,
            include_archived=include_archived,
        )
    
    async def update_session(
        self,
        session_unique_id: str,
        **kwargs
    ) -> Optional[Session]:
        """Update a session's information.
        
        Args:
            session_unique_id: The session's unique identifier.
            **kwargs: Fields to update with new values.
            
        Returns:
            Updated Session instance if found, None otherwise.
        """
        session = await self.session_repo.get_by_unique_id(session_unique_id)
        if not session:
            return None
        
        # Auto-update time_updated
        kwargs["time_updated"] = int(time.time())
        
        updated = await self.session_repo.update(session, **kwargs)
        await self.session.commit()
        await self.session.refresh(updated)
        
        return updated
    
    async def delete_session(self, session_unique_id: str) -> bool:
        """Delete a session by unique ID.
        
        Cascades to related messages as defined in the model relationships.
        
        Args:
            session_unique_id: The session's unique identifier.
            
        Returns:
            True if deleted, False if not found.
        """
        session = await self.session_repo.get_by_unique_id(session_unique_id)
        if not session:
            return False
        
        await self.session_repo.delete(session)
        await self.session.commit()
        
        return True
    
    async def archive_session(
        self,
        session_unique_id: str,
        archived_time: Optional[int] = None,
    ) -> Optional[Session]:
        """Archive a session by setting its time_archived timestamp.
        
        Args:
            session_unique_id: The unique identifier of the session to archive.
            archived_time: Unix timestamp for archive time (default: current time).
            
        Returns:
            Updated session if found, None otherwise.
        """
        session = await self.session_repo.archive(
            session_unique_id=session_unique_id,
            archived_time=archived_time,
        )
        
        if session:
            await self.session.commit()
            await self.session.refresh(session)
        
        return session
    
    async def unarchive_session(
        self,
        session_unique_id: str,
    ) -> Optional[Session]:
        """Unarchive a session by clearing its time_archived timestamp.
        
        Args:
            session_unique_id: The unique identifier of the session to unarchive.
            
        Returns:
            Updated session if found, None otherwise.
        """
        session = await self.session_repo.unarchive(
            session_unique_id=session_unique_id,
        )
        
        if session:
            await self.session.commit()
            await self.session.refresh(session)
        
        return session
    
    async def count_by_project(
        self,
        project_unique_id: str,
        include_archived: bool = False,
    ) -> int:
        """Count sessions for a specific project.
        
        Args:
            project_unique_id: The unique identifier of the project.
            include_archived: Whether to include archived sessions (default: False).
            
        Returns:
            Number of sessions for the project.
        """
        return await self.session_repo.count_by_project(
            project_unique_id=project_unique_id,
            include_archived=include_archived,
        )
    
    async def count_by_workspace(
        self,
        workspace_unique_id: str,
        include_archived: bool = False,
    ) -> int:
        """Count sessions for a specific workspace.
        
        Args:
            workspace_unique_id: The unique identifier of the workspace.
            include_archived: Whether to include archived sessions (default: False).
            
        Returns:
            Number of sessions for the workspace.
        """
        return await self.session_repo.count_by_workspace(
            workspace_unique_id=workspace_unique_id,
            include_archived=include_archived,
        )
