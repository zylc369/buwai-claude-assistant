"""Conversation Session service for business logic."""

import time
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_config
from database.models import Session
from repositories.conversation_session_repository import ConversationSessionRepository
from services.project_service import ProjectService
from services.workspace_service import WorkspaceService
from logger import get_logger

logger = get_logger(__name__)


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
        external_session_id: str,
        project_unique_id: str,
        workspace_unique_id: str,
        directory: Optional[str] = None,
        title: str = "",
        time_compacting: Optional[int] = None,
        time_archived: Optional[int] = None,
    ) -> Session:
        """Create a new conversation session.

        Args:
            session_unique_id: Unique identifier for the session.
            external_session_id: External session identifier (required).
            project_unique_id: The unique identifier of the project.
            workspace_unique_id: The unique identifier of the workspace.
            directory: The working directory path (computed if not provided).
            title: The session title.
            time_compacting: Optional compacting timestamp.
            time_archived: Optional archived timestamp.

        Returns:
            Created Session instance.
        """
        logger.debug(f"create_session called with session_unique_id={session_unique_id}")
        current_time = int(time.time())

        # Compute directory from project/workspace if not provided
        if directory is None:
            directory = await self._compute_session_directory(
                project_unique_id, workspace_unique_id
            )

        logger.info(f"Business decision: creating session {session_unique_id} for project {project_unique_id}")
        session = await self.session_repo.create(
            session_unique_id=session_unique_id,
            external_session_id=external_session_id,
            project_unique_id=project_unique_id,
            workspace_unique_id=workspace_unique_id,
            directory=directory,
            title=title,
            gmt_create=current_time,
            gmt_modified=current_time,
            time_compacting=time_compacting,
            time_archived=time_archived,
        )

        await self.session.commit()
        await self.session.refresh(session)

        logger.debug(f"create_session completed")
        return session
    
    async def _compute_session_directory(
        self,
        project_unique_id: str,
        workspace_unique_id: str,
    ) -> str:
        config = get_config()
        projects_root = config.projects.root
        
        workspace_service = WorkspaceService(self.session)
        workspace = await workspace_service.get_workspace_by_unique_id(workspace_unique_id)
        
        if workspace is not None:
            workspace_dir = workspace.directory
            if workspace_dir is not None:
                logger.debug(f"Using workspace directory: {workspace_dir}")
                return workspace_dir
        
        project_service = ProjectService(self.session)
        project = await project_service.get_project_by_unique_id(project_unique_id)
        
        if project is not None:
            project_dir = project.directory
            if project_dir is not None:
                logger.debug(f"Using project directory: {project_dir}")
                return project_dir
        
        fallback_dir = f"{projects_root}/{project_unique_id}/{workspace_unique_id}"
        logger.warning(f"Using fallback directory: {fallback_dir}")
        return fallback_dir
    
    async def get_by_unique_id(self, session_unique_id: str) -> Optional[Session]:
        """Get a session by its unique identifier.

        Args:
            session_unique_id: The session's unique identifier.

        Returns:
            Session instance if found, None otherwise.
        """
        logger.debug(f"get_by_unique_id called with session_unique_id={session_unique_id}")
        result = await self.session_repo.get_by_unique_id(session_unique_id)
        logger.debug(f"get_by_unique_id completed, found={result is not None}")
        return result

    async def get_session_by_external_id(
        self, external_session_id: str
    ) -> Optional[Session]:
        """Get a session by its external session identifier.

        Args:
            external_session_id: The external session identifier.

        Returns:
            Session instance if found, None otherwise.
        """
        logger.debug(f"get_session_by_external_id called with external_session_id={external_session_id}")
        result = await self.session_repo.get_by_external_session_id(
            external_session_id
        )
        logger.debug(f"get_session_by_external_id completed, found={result is not None}")
        return result

    async def list_sessions(
        self,
        project_unique_id: Optional[str] = None,
        workspace_unique_id: Optional[str] = None,
        external_session_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        include_archived: bool = False,
    ) -> List[Session]:
        """List sessions with pagination and optional filters.

        Args:
            project_unique_id: Optional filter by project unique ID.
            workspace_unique_id: Optional filter by workspace unique ID.
            external_session_id: Optional filter by external session ID.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            include_archived: Whether to include archived sessions (default: False).

        Returns:
            List of sessions matching the criteria.
        """
        logger.debug(f"list_sessions called with project_unique_id={project_unique_id}, workspace_unique_id={workspace_unique_id}, offset={offset}, limit={limit}")
        result = await self.session_repo.list(
            project_unique_id=project_unique_id,
            workspace_unique_id=workspace_unique_id,
            external_session_id=external_session_id,
            offset=offset,
            limit=limit,
            include_archived=include_archived,
        )
        logger.debug(f"list_sessions completed, returned {len(result)} sessions")
        return result
    
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
        logger.debug(f"update_session called with session_unique_id={session_unique_id}")
        session = await self.session_repo.get_by_unique_id(session_unique_id)
        if not session:
            logger.debug(f"update_session completed, session not found")
            return None

        # Auto-update gmt_modified
        kwargs["gmt_modified"] = int(time.time())

        logger.info(f"Business decision: updating session {session_unique_id}")
        updated = await self.session_repo.update(session, **kwargs)
        await self.session.commit()
        await self.session.refresh(updated)

        logger.debug(f"update_session completed")
        return updated
    
    async def delete_session(self, session_unique_id: str) -> bool:
        """Delete a session by unique ID.

        Cascades to related messages as defined in the model relationships.

        Args:
            session_unique_id: The session's unique identifier.

        Returns:
            True if deleted, False if not found.
        """
        logger.debug(f"delete_session called with session_unique_id={session_unique_id}")
        session = await self.session_repo.get_by_unique_id(session_unique_id)
        if not session:
            logger.debug(f"delete_session completed, session not found")
            return False

        logger.info(f"Business decision: deleting session {session_unique_id}")
        await self.session_repo.delete(session)
        await self.session.commit()

        logger.debug(f"delete_session completed")
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
        logger.debug(f"archive_session called with session_unique_id={session_unique_id}")
        logger.info(f"Business decision: archiving session {session_unique_id}")
        session = await self.session_repo.archive(
            session_unique_id=session_unique_id,
            archived_time=archived_time,
        )

        if session:
            await self.session.commit()
            await self.session.refresh(session)

        logger.debug(f"archive_session completed, success={session is not None}")
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
        logger.debug(f"unarchive_session called with session_unique_id={session_unique_id}")
        logger.info(f"Business decision: unarchiving session {session_unique_id}")
        session = await self.session_repo.unarchive(
            session_unique_id=session_unique_id,
        )

        if session:
            await self.session.commit()
            await self.session.refresh(session)

        logger.debug(f"unarchive_session completed, success={session is not None}")
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
        logger.debug(f"count_by_project called with project_unique_id={project_unique_id}, include_archived={include_archived}")
        result = await self.session_repo.count_by_project(
            project_unique_id=project_unique_id,
            include_archived=include_archived,
        )
        logger.debug(f"count_by_project completed, found {result} sessions")
        return result
    
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
        logger.debug(f"count_by_workspace called with workspace_unique_id={workspace_unique_id}, include_archived={include_archived}")
        result = await self.session_repo.count_by_workspace(
            workspace_unique_id=workspace_unique_id,
            include_archived=include_archived,
        )
        logger.debug(f"count_by_workspace completed, found {result} sessions")
        return result
