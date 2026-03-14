"""Workspace repository for database operations."""

from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Workspace
from repositories.base import BaseRepository
from logger import get_logger

logger = get_logger(__name__)


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository for Workspace model operations.
    
    Provides workspace-specific database operations on top of base CRUD.
    
    Attributes:
        model: The Workspace model class.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize WorkspaceRepository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session)
        self.model = Workspace
        logger.debug("WorkspaceRepository initialized")
    
    async def get_by_project_unique_id(
        self,
        project_unique_id: str
    ) -> List[Workspace]:
        """Get all workspaces for a specific project.

        Args:
            project_unique_id: Unique identifier of the project.

        Returns:
            List of workspaces belonging to the project.
        """
        try:
            logger.debug(f"get_by_project_unique_id called with project_unique_id={project_unique_id}")
            result = await self.session.execute(
                select(Workspace).where(
                    Workspace.project_unique_id == project_unique_id
                )
            )
            workspaces = list(result.scalars().all())
            logger.debug(f"get_by_project_unique_id returned {len(workspaces)} workspaces")
            return workspaces
        except Exception as e:
            logger.error(f"get_by_project_unique_id failed: {str(e)}")
            raise
    
    async def get_by_unique_id(
        self,
        workspace_unique_id: str
    ) -> Optional[Workspace]:
        """Get a workspace by its unique identifier.

        Args:
            workspace_unique_id: Unique identifier of the workspace.

        Returns:
            Workspace if found, None otherwise.
        """
        try:
            logger.debug(f"get_by_unique_id called with workspace_unique_id={workspace_unique_id}")
            result = await self.session.execute(
                select(Workspace).where(
                    Workspace.workspace_unique_id == workspace_unique_id
                )
            )
            workspace = result.scalar_one_or_none()
            logger.debug(f"get_by_unique_id returned {type(workspace).__name__ if workspace else 'None'}")
            return workspace
        except Exception as e:
            logger.error(f"get_by_unique_id failed: {str(e)}")
            raise
    
    async def get_by_name(
        self,
        name_query: str,
        project_unique_id: Optional[str] = None
    ) -> List[Workspace]:
        """Search workspaces by name (case-insensitive partial match).

        Args:
            name_query: Search string to match against workspace names.
            project_unique_id: Optional project ID to filter results.

        Returns:
            List of matching workspaces.
        """
        try:
            logger.debug(f"get_by_name called with name_query={name_query}, project_unique_id={project_unique_id}")
            query = select(Workspace).where(
                func.lower(Workspace.name).like(f"%{name_query.lower()}%")
            )

            if project_unique_id:
                query = query.where(
                    Workspace.project_unique_id == project_unique_id
                )

            result = await self.session.execute(query)
            workspaces = list(result.scalars().all())
            logger.debug(f"get_by_name returned {len(workspaces)} workspaces")
            return workspaces
        except Exception as e:
            logger.error(f"get_by_name failed: {str(e)}")
            raise
    
    async def list(
        self,
        project_unique_id: str,
        offset: int = 0,
        limit: int = 100
    ) -> List[Workspace]:
        """Get paginated list of workspaces for a project.

        Args:
            project_unique_id: Unique identifier of the project (required).
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).

        Returns:
            List of workspaces for the project.
        """
        try:
            logger.debug(f"list called with project_unique_id={project_unique_id}, offset={offset}, limit={limit}")
            result = await self.session.execute(
                select(Workspace)
                .where(Workspace.project_unique_id == project_unique_id)
                .offset(offset)
                .limit(limit)
            )
            workspaces = list(result.scalars().all())
            logger.debug(f"list returned {len(workspaces)} workspaces")
            return workspaces
        except Exception as e:
            logger.error(f"list failed: {str(e)}")
            raise
