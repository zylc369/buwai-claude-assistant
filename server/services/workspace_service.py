"""Workspace service for business logic."""

import re
import time
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Workspace
from repositories.workspace_repository import WorkspaceRepository
from logger import get_logger
from utils.id_generator import generate_uuidv7

logger = get_logger(__name__)

# Directory name pattern for validation
DIRECTORY_PATTERN = re.compile(r'^[0-9a-zA-Z_]+$')


def _validate_directory(directory: str) -> None:
    """Validate directory name format.

    Only validates simple directory names (no path separators).
    Full paths are allowed without validation.

    Args:
        directory: Directory name to validate.

    Raises:
        ValueError: If directory name doesn't match the required pattern.
    """
    if '/' in directory or '\\' in directory:
        return
    if not DIRECTORY_PATTERN.match(directory):
        raise ValueError(
            f"Invalid directory name '{directory}'. "
            "Directory must contain only alphanumeric characters and underscores."
        )


class WorkspaceService:
    """Service layer for workspace management.
    
    Provides business logic operations for workspace management,
    wrapping the WorkspaceRepository with transaction handling.
    
    Attributes:
        session: SQLAlchemy async session.
        workspace_repo: WorkspaceRepository instance.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize WorkspaceService with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.workspace_repo = WorkspaceRepository(session)
    
    async def create_workspace(
        self,
        workspace_unique_id: str,
        project_unique_id: str,
        name: Optional[str] = None,
        branch: Optional[str] = None,
        directory: Optional[str] = None,
        extra: Optional[str] = None
    ) -> Workspace:
        """Create a new workspace.

        Args:
            workspace_unique_id: Unique identifier for the workspace.
            project_unique_id: Unique identifier of the parent project.
            name: Optional name for the workspace.
            branch: Optional branch name.
            directory: Optional directory path.
            extra: Optional JSON data as text.

        Returns:
            Created workspace instance.
        """
        logger.debug(f"create_workspace called with workspace_unique_id={workspace_unique_id}, project_unique_id={project_unique_id}")

        if directory:
            _validate_directory(directory)

        current_time = int(time.time() * 1000)
        logger.info(f"Business decision: creating workspace {workspace_unique_id}")
        workspace = await self.workspace_repo.create(
            workspace_unique_id=workspace_unique_id,
            project_unique_id=project_unique_id,
            name=name,
            branch=branch,
            directory=directory,
            extra=extra,
            gmt_create=current_time,
            gmt_modified=current_time,
            latest_active_time=current_time
        )

        await self.session.commit()
        await self.session.refresh(workspace)

        logger.debug(f"create_workspace completed")
        return workspace
    
    async def get_workspace_by_id(self, workspace_id: int) -> Optional[Workspace]:
        """Get a workspace by its primary key ID.

        Args:
            workspace_id: Primary key ID of the workspace.

        Returns:
            Workspace if found, None otherwise.
        """
        logger.debug(f"get_workspace_by_id called with workspace_id={workspace_id}")
        result = await self.workspace_repo.get_by_id(workspace_id)
        logger.debug(f"get_workspace_by_id completed, found={result is not None}")
        return result
    
    async def get_workspace_by_unique_id(
        self,
        workspace_unique_id: str
    ) -> Optional[Workspace]:
        """Get a workspace by its unique identifier.

        Args:
            workspace_unique_id: Unique identifier of the workspace.

        Returns:
            Workspace if found, None otherwise.
        """
        logger.debug(f"get_workspace_by_unique_id called with workspace_unique_id={workspace_unique_id}")
        result = await self.workspace_repo.get_by_unique_id(workspace_unique_id)
        logger.debug(f"get_workspace_by_unique_id completed, found={result is not None}")
        return result
    
    async def list_workspaces(
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
        logger.debug(f"list_workspaces called with project_unique_id={project_unique_id}, offset={offset}, limit={limit}")
        result = await self.workspace_repo.list(
            project_unique_id=project_unique_id,
            offset=offset,
            limit=limit
        )
        logger.debug(f"list_workspaces completed, returned {len(result)} workspaces")
        return result
    
    async def update_workspace(
        self,
        workspace_id: int,
        **kwargs
    ) -> Optional[Workspace]:
        """Update workspace information.

        Args:
            workspace_id: Primary key ID of the workspace.
            **kwargs: Fields to update (name, branch, directory, extra).

        Returns:
            Updated workspace if found, None otherwise.
        """
        logger.debug(f"update_workspace called with workspace_id={workspace_id}")
        workspace = await self.workspace_repo.get_by_id(workspace_id)
        if not workspace:
            logger.debug(f"update_workspace completed, workspace not found")
            return None

        if 'directory' in kwargs and kwargs['directory']:
            _validate_directory(kwargs['directory'])

        kwargs['gmt_modified'] = int(time.time() * 1000)

        logger.info(f"Business decision: updating workspace {workspace_id}")
        updated = await self.workspace_repo.update(workspace, **kwargs)
        await self.session.commit()
        await self.session.refresh(updated)

        logger.debug(f"update_workspace completed")
        return updated

    async def update_latest_active_time(
        self,
        workspace_id: int
    ) -> Optional[Workspace]:
        """Update the latest active time for a workspace.

        Args:
            workspace_id: Primary key ID of the workspace.

        Returns:
            Updated workspace if found, None otherwise.
        """
        logger.debug(f"update_latest_active_time called with workspace_id={workspace_id}")
        workspace = await self.workspace_repo.get_by_id(workspace_id)
        if not workspace:
            logger.debug(f"update_latest_active_time completed, workspace not found")
            return None

        current_time = int(time.time() * 1000)
        updated = await self.workspace_repo.update(
            workspace,
            latest_active_time=current_time,
            gmt_modified=current_time
        )
        await self.session.commit()
        await self.session.refresh(updated)

        logger.debug(f"update_latest_active_time completed")
        return updated
    
    async def delete_workspace(self, workspace_id: int) -> bool:
        """Delete a workspace.

        Note: This will cascade delete all associated sessions due to
        the model relationship configuration.

        Args:
            workspace_id: Primary key ID of the workspace.

        Returns:
            True if deleted, False if workspace not found.
        """
        logger.debug(f"delete_workspace called with workspace_id={workspace_id}")
        workspace = await self.workspace_repo.get_by_id(workspace_id)
        if not workspace:
            logger.debug(f"delete_workspace completed, workspace not found")
            return False

        logger.info(f"Business decision: deleting workspace {workspace_id}")
        await self.workspace_repo.delete(workspace)
        await self.session.commit()

        logger.debug(f"delete_workspace completed")
        return True
    
    async def search_workspaces(
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
        logger.debug(f"search_workspaces called with name_query={name_query}, project_unique_id={project_unique_id}")
        result = await self.workspace_repo.get_by_name(
            name_query=name_query,
            project_unique_id=project_unique_id
        )
        logger.debug(f"search_workspaces completed, found {len(result)} workspaces")
        return result
