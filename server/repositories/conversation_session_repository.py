"""Conversation Session repository for database operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Session
from repositories.base import BaseRepository
from utils.timestamp import get_timestamp_ms
from logger import get_logger

logger = get_logger(__name__)


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
        logger.debug("ConversationSessionRepository initialized")
    
    async def get_by_unique_id(self, session_unique_id: str, test: bool = False) -> Optional[Session]:
        """Get a session by its unique identifier.

        Args:
            session_unique_id: The unique identifier of the session.
            test: Filter by test flag (default: False).

        Returns:
            Session instance if found, None otherwise.
        """
        try:
            logger.debug(f"get_by_unique_id called with session_unique_id={session_unique_id}, test={test}")
            result = await self.session.execute(
                select(Session).where(Session.session_unique_id == session_unique_id, Session.test == test)
            )
            session = result.scalar_one_or_none()
            logger.debug(f"get_by_unique_id returned {type(session).__name__ if session else 'None'}")
            return session
        except Exception as e:
            logger.error(f"get_by_unique_id failed: {str(e)}")
            raise

    async def get_by_external_session_id(
        self, external_session_id: str, test: bool = False
    ) -> Optional[Session]:
        """Get a session by its external session identifier.

        Args:
            external_session_id: The external session identifier.
            test: Filter by test flag (default: False).

        Returns:
            Session instance if found, None otherwise.
        """
        try:
            logger.debug(f"get_by_external_session_id called with external_session_id={external_session_id}, test={test}")
            result = await self.session.execute(
                select(Session).where(Session.external_session_id == external_session_id, Session.test == test)
            )
            session = result.scalar_one_or_none()
            logger.debug(f"get_by_external_session_id returned {type(session).__name__ if session else 'None'}")
            return session
        except Exception as e:
            logger.error(f"get_by_external_session_id failed: {str(e)}")
            raise

    async def create_session(
        self,
        session_unique_id: str,
        external_session_id: str,
        project_unique_id: str,
        workspace_unique_id: str,
        directory: str,
        title: str,
        gmt_create: Optional[int] = None,
        gmt_modified: Optional[int] = None,
        test: bool = False,
    ) -> Session:
        """Create a new session.

        Args:
            session_unique_id: Unique identifier for the session.
            external_session_id: External session identifier.
            project_unique_id: Unique identifier for the project.
            workspace_unique_id: Unique identifier for the workspace.
            directory: Session directory path.
            title: Session title.
            gmt_create: Creation timestamp (defaults to current time).
            gmt_modified: Update timestamp (defaults to current time).
            test: Whether this is a test session (default: False).

        Returns:
            Created Session instance.
        """
        try:
            logger.debug(f"create_session called with session_unique_id={session_unique_id}, project_unique_id={project_unique_id}, workspace_unique_id={workspace_unique_id}, test={test}")
            if gmt_create is None or gmt_modified is None:
                current_time = get_timestamp_ms()
                if gmt_create is None:
                    gmt_create = current_time
                if gmt_modified is None:
                    gmt_modified = current_time

            session = await self.create(
                session_unique_id=session_unique_id,
                external_session_id=external_session_id,
                project_unique_id=project_unique_id,
                workspace_unique_id=workspace_unique_id,
                directory=directory,
                title=title,
                gmt_create=gmt_create,
                gmt_modified=gmt_modified,
                test=test,
            )
            logger.debug(f"create_session returned session with id={session.id}")
            return session
        except Exception as e:
            logger.error(f"create_session failed: {str(e)}")
            raise

    async def update_session(
        self,
        session: Session,
        title: Optional[str] = None,
        directory: Optional[str] = None,
        test: bool = False,
    ) -> Session:
        """Update an existing session.

        Args:
            session: Session instance to update.
            title: Title to update (optional).
            directory: Directory to update (optional).
            test: Filter by test flag (default: False).

        Returns:
            Updated Session instance.
        """
        try:
            logger.debug(f"update_session called with session.id={session.id}, title={title}, directory={directory}, test={test}")
            update_kwargs = {}
            if title is not None:
                update_kwargs["title"] = title
            if directory is not None:
                update_kwargs["directory"] = directory

            if update_kwargs:
                session = await self.update(session, **update_kwargs)

            logger.debug(f"update_session returned session with id={session.id}")
            return session
        except Exception as e:
            logger.error(f"update_session failed: {str(e)}")
            raise
    
    async def get_by_project_unique_id(
        self,
        project_unique_id: str,
        offset: int = 0,
        limit: int = 100,
        include_archived: bool = False,
        test: bool = False,
    ) -> List[Session]:
        """Get all sessions for a specific project.

        Args:
            project_unique_id: The unique identifier of the project.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            include_archived: Whether to include archived sessions (default: False).
            test: Filter by test flag (default: False).

        Returns:
            List of sessions for the project.
        """
        try:
            logger.debug(f"get_by_project_unique_id called with project_unique_id={project_unique_id}, offset={offset}, limit={limit}, include_archived={include_archived}, test={test}")
            query = select(Session).where(
                Session.project_unique_id == project_unique_id,
                Session.test == test
            )

            if not include_archived:
                query = query.where(Session.time_archived.is_(None))

            query = query.offset(offset).limit(limit)
            result = await self.session.execute(query)
            sessions = list(result.scalars().all())
            logger.debug(f"get_by_project_unique_id returned {len(sessions)} sessions")
            return sessions
        except Exception as e:
            logger.error(f"get_by_project_unique_id failed: {str(e)}")
            raise
    
    async def get_by_workspace_unique_id(
        self,
        workspace_unique_id: str,
        offset: int = 0,
        limit: int = 100,
        include_archived: bool = False,
        test: bool = False,
    ) -> List[Session]:
        """Get all sessions for a specific workspace.

        Args:
            workspace_unique_id: The unique identifier of the workspace.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            include_archived: Whether to include archived sessions (default: False).
            test: Filter by test flag (default: False).

        Returns:
            List of sessions for the workspace.
        """
        try:
            logger.debug(f"get_by_workspace_unique_id called with workspace_unique_id={workspace_unique_id}, offset={offset}, limit={limit}, include_archived={include_archived}, test={test}")
            query = select(Session).where(
                Session.workspace_unique_id == workspace_unique_id,
                Session.test == test
            )

            if not include_archived:
                query = query.where(Session.time_archived.is_(None))

            query = query.offset(offset).limit(limit)
            result = await self.session.execute(query)
            sessions = list(result.scalars().all())
            logger.debug(f"get_by_workspace_unique_id returned {len(sessions)} sessions")
            return sessions
        except Exception as e:
            logger.error(f"get_by_workspace_unique_id failed: {str(e)}")
            raise
    
    async def list(
        self,
        project_unique_id: Optional[str] = None,
        workspace_unique_id: Optional[str] = None,
        external_session_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        include_archived: bool = False,
        test: bool = False,
    ) -> List[Session]:
        """Get sessions with optional filtering and pagination.

        Args:
            project_unique_id: Optional filter by project unique ID.
            workspace_unique_id: Optional filter by workspace unique ID.
            external_session_id: Optional filter by external session ID.
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            include_archived: Whether to include archived sessions (default: False).
            test: Filter by test flag (default: False).

        Returns:
            List of sessions matching the filters.
        """
        try:
            logger.debug(f"list called with project_unique_id={project_unique_id}, workspace_unique_id={workspace_unique_id}, external_session_id={external_session_id}, offset={offset}, limit={limit}, include_archived={include_archived}, test={test}")
            query = select(Session).where(Session.test == test)

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
            sessions = list(result.scalars().all())
            logger.debug(f"list returned {len(sessions)} sessions")
            return sessions
        except Exception as e:
            logger.error(f"list failed: {str(e)}")
            raise
    
    async def archive(
        self,
        session_unique_id: str,
        archived_time: Optional[int] = None,
        test: bool = False,
    ) -> Optional[Session]:
        """Archive a session by setting its time_archived timestamp.

        Args:
            session_unique_id: The unique identifier of the session to archive.
            archived_time: Unix timestamp for archive time (default: current time).
            test: Filter by test flag (default: False).

        Returns:
            Updated session if found, None otherwise.
        """
        try:
            logger.debug(f"archive called with session_unique_id={session_unique_id}, archived_time={archived_time}, test={test}")
            session = await self.get_by_unique_id(session_unique_id, test=test)
            if session is None:
                logger.debug(f"archive returned None (session not found)")
                return None

            if archived_time is None:
                archived_time = get_timestamp_ms()

            session.time_archived = archived_time
            await self.session.flush()
            logger.debug(f"archive succeeded for session with id={session.id}")
            return session
        except Exception as e:
            logger.error(f"archive failed: {str(e)}")
            raise
    
    async def unarchive(
        self,
        session_unique_id: str,
        test: bool = False,
    ) -> Optional[Session]:
        """Unarchive a session by clearing its time_archived timestamp.

        Args:
            session_unique_id: The unique identifier of the session to unarchive.
            test: Filter by test flag (default: False).

        Returns:
            Updated session if found, None otherwise.
        """
        try:
            logger.debug(f"unarchive called with session_unique_id={session_unique_id}, test={test}")
            session = await self.get_by_unique_id(session_unique_id, test=test)
            if session is None:
                logger.debug(f"unarchive returned None (session not found)")
                return None

            session.time_archived = None
            await self.session.flush()
            logger.debug(f"unarchive succeeded for session with id={session.id}")
            return session
        except Exception as e:
            logger.error(f"unarchive failed: {str(e)}")
            raise
    
    async def count_by_project(
        self,
        project_unique_id: str,
        include_archived: bool = False,
        test: bool = False,
    ) -> int:
        """Count sessions for a specific project.

        Args:
            project_unique_id: The unique identifier of the project.
            include_archived: Whether to include archived sessions (default: False).
            test: Filter by test flag (default: False).

        Returns:
            Number of sessions for the project.
        """
        try:
            logger.debug(f"count_by_project called with project_unique_id={project_unique_id}, include_archived={include_archived}, test={test}")
            query = select(Session).where(
                Session.project_unique_id == project_unique_id,
                Session.test == test
            )

            if not include_archived:
                query = query.where(Session.time_archived.is_(None))

            result = await self.session.execute(query)
            count = len(result.scalars().all())
            logger.debug(f"count_by_project returned {count}")
            return count
        except Exception as e:
            logger.error(f"count_by_project failed: {str(e)}")
            raise
    
    async def count_by_workspace(
        self,
        workspace_unique_id: str,
        include_archived: bool = False,
        test: bool = False,
    ) -> int:
        """Count sessions for a specific workspace.

        Args:
            workspace_unique_id: The unique identifier of the workspace.
            include_archived: Whether to include archived sessions (default: False).
            test: Filter by test flag (default: False).

        Returns:
            Number of sessions for the workspace.
        """
        try:
            logger.debug(f"count_by_workspace called with workspace_unique_id={workspace_unique_id}, include_archived={include_archived}, test={test}")
            query = select(Session).where(
                Session.workspace_unique_id == workspace_unique_id,
                Session.test == test
            )

            if not include_archived:
                query = query.where(Session.time_archived.is_(None))

            result = await self.session.execute(query)
            count = len(result.scalars().all())
            logger.debug(f"count_by_workspace returned {count}")
            return count
        except Exception as e:
            logger.error(f"count_by_workspace failed: {str(e)}")
            raise
