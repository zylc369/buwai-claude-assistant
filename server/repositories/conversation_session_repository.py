"""Conversation Session repository for database operations."""

import time
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Session
from repositories.base import BaseRepository


class ConversationSessionRepository(BaseRepository[Session]):
    """Repository for Conversation Session model operations.
    
    Provides session-specific database operations on top of base CRUD.
    Supports filtering by project, workspace, and archive status.
    
    Attributes:
        model: The Session model class.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize ConversationSessionRepository with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session)
        self.model = Session
    
    async def get_by_unique_id(self, session_unique_id: str) -> Optional[Session]:
        """Get a session by its unique identifier.

        Args:
            session_unique_id: The unique identifier of the session.

        Returns:
            Session instance if found, None otherwise.
        """
        result = await self.session.execute(
            select(Session).where(Session.session_unique_id == session_unique_id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_session_id(
        self, external_session_id: str
    ) -> Optional[Session]:
        """Get a session by its external session identifier.

        Args:
            external_session_id: The external session identifier.

        Returns:
            Session instance if found, None otherwise.
        """
        result = await self.session.execute(
            select(Session).where(Session.external_session_id == external_session_id)
        )
        return result.scalar_one_or_none()

    async def create_session(
        self,
        session_unique_id: str,
        external_session_id: str,
        project_unique_id: str,
        workspace_unique_id: str,
        directory: str,
        title: str,
        sdk_session_id: Optional[str] = None,
        time_created: Optional[int] = None,
        time_updated: Optional[int] = None,
    ) -> Session:
        """Create a new session.

        Args:
            session_unique_id: Unique identifier for the session.
            external_session_id: External session identifier.
            project_unique_id: Unique identifier for the project.
            workspace_unique_id: Unique identifier for the workspace.
            directory: Session directory path.
            title: Session title.
            sdk_session_id: SDK session identifier (optional).
            time_created: Creation timestamp (defaults to current time).
            time_updated: Update timestamp (defaults to current time).

        Returns:
            Created Session instance.
        """
        if time_created is None or time_updated is None:
            current_time = int(time.time())
            if time_created is None:
                time_created = current_time
            if time_updated is None:
                time_updated = current_time

        return await self.create(
            session_unique_id=session_unique_id,
            external_session_id=external_session_id,
            project_unique_id=project_unique_id,
            workspace_unique_id=workspace_unique_id,
            directory=directory,
            title=title,
            sdk_session_id=sdk_session_id,
            time_created=time_created,
            time_updated=time_updated,
        )

    async def update_session(
        self,
        session: Session,
        sdk_session_id: Optional[str] = None,
        title: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Session:
        """Update an existing session.

        Args:
            session: Session instance to update.
            sdk_session_id: SDK session identifier to update (optional).
            title: Title to update (optional).
            directory: Directory to update (optional).

        Returns:
            Updated Session instance.
        """
        update_kwargs = {}
        if sdk_session_id is not None:
            update_kwargs["sdk_session_id"] = sdk_session_id
        if title is not None:
            update_kwargs["title"] = title
        if directory is not None:
            update_kwargs["directory"] = directory

        if update_kwargs:
            session = await self.update(session, **update_kwargs)

        return session
    
    async def get_by_project_unique_id(
        self,
        project_unique_id: str,
        offset: int = 0,
        limit: int = 100,
        include_archived: bool = False,
    ) -> List[Session]:
        """Get all sessions for a specific project.
        
        Args:
            project_unique_id: The unique identifier of the project.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            include_archived: Whether to include archived sessions (default: False).
            
        Returns:
            List of sessions for the project.
        """
        query = select(Session).where(
            Session.project_unique_id == project_unique_id
        )
        
        if not include_archived:
            query = query.where(Session.time_archived.is_(None))
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_workspace_unique_id(
        self,
        workspace_unique_id: str,
        offset: int = 0,
        limit: int = 100,
        include_archived: bool = False,
    ) -> List[Session]:
        """Get all sessions for a specific workspace.
        
        Args:
            workspace_unique_id: The unique identifier of the workspace.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            include_archived: Whether to include archived sessions (default: False).
            
        Returns:
            List of sessions for the workspace.
        """
        query = select(Session).where(
            Session.workspace_unique_id == workspace_unique_id
        )
        
        if not include_archived:
            query = query.where(Session.time_archived.is_(None))
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list(
        self,
        project_unique_id: Optional[str] = None,
        workspace_unique_id: Optional[str] = None,
        external_session_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        include_archived: bool = False,
    ) -> List[Session]:
        """Get sessions with optional filtering and pagination.
        
        Args:
            project_unique_id: Optional filter by project unique ID.
            workspace_unique_id: Optional filter by workspace unique ID.
            external_session_id: Optional filter by external session ID.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            include_archived: Whether to include archived sessions (default: False).
            
        Returns:
            List of sessions matching the filters.
        """
        query = select(Session)
        
        if project_unique_id is not None:
            query = query.where(Session.project_unique_id == project_unique_id)
        
        if workspace_unique_id is not None:
            query = query.where(Session.workspace_unique_id == workspace_unique_id)
        
        if external_session_id is not None:
            query = query.where(Session.external_session_id == external_session_id)
        
        if not include_archived:
            query = query.where(Session.time_archived.is_(None))
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def archive(
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
        session = await self.get_by_unique_id(session_unique_id)
        if session is None:
            return None
        
        if archived_time is None:
            archived_time = int(time.time())
        
        session.time_archived = archived_time
        await self.session.flush()
        return session
    
    async def unarchive(
        self,
        session_unique_id: str,
    ) -> Optional[Session]:
        """Unarchive a session by clearing its time_archived timestamp.
        
        Args:
            session_unique_id: The unique identifier of the session to unarchive.
            
        Returns:
            Updated session if found, None otherwise.
        """
        session = await self.get_by_unique_id(session_unique_id)
        if session is None:
            return None
        
        session.time_archived = None
        await self.session.flush()
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
        query = select(Session).where(
            Session.project_unique_id == project_unique_id
        )
        
        if not include_archived:
            query = query.where(Session.time_archived.is_(None))
        
        result = await self.session.execute(query)
        return len(result.scalars().all())
    
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
        query = select(Session).where(
            Session.workspace_unique_id == workspace_unique_id
        )
        
        if not include_archived:
            query = query.where(Session.time_archived.is_(None))
        
        result = await self.session.execute(query)
        return len(result.scalars().all())
