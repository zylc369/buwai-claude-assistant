"""Project service for business logic."""

import time
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project
from repositories.project_repository import ProjectRepository
from logger import get_logger

logger = get_logger(__name__)


class ProjectService:
    """Service layer for project management.
    
    Provides business logic for project operations, wrapping the
    ProjectRepository with additional functionality like timestamp
    management and transaction handling.
    
    Attributes:
        session: SQLAlchemy async session.
        project_repo: ProjectRepository instance.
    
    Example:
        async with async_session() as session:
            service = ProjectService(session)
            project = await service.create_project(
                project_unique_id="proj-001",
                worktree="/path/to/worktree",
                name="My Project"
            )
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize ProjectService with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.project_repo = ProjectRepository(session)
    
    async def create_project(
        self,
        project_unique_id: str,
        worktree: str,
        name: Optional[str] = None,
        branch: Optional[str] = None,
        time_initialized: Optional[int] = None,
    ) -> Project:
        """Create a new project.

        Args:
            project_unique_id: Unique identifier for the project.
            worktree: Path to the worktree directory.
            name: Optional project name.
            branch: Optional git branch name.
            time_initialized: Optional initialization timestamp.

        Returns:
            Created Project instance.
        """
        logger.debug(f"create_project called with project_unique_id={project_unique_id}, worktree={worktree}")
        current_time = int(time.time())

        logger.info(f"Business decision: creating project {project_unique_id}")
        project = await self.project_repo.create(
            project_unique_id=project_unique_id,
            worktree=worktree,
            name=name,
            branch=branch,
            time_initialized=time_initialized,
            time_created=current_time,
            time_updated=current_time,
        )

        await self.session.commit()
        await self.session.refresh(project)

        logger.debug(f"create_project completed")
        return project
    
    async def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Get a project by its ID.

        Args:
            project_id: The project's primary key.

        Returns:
            Project instance if found, None otherwise.
        """
        logger.debug(f"get_project_by_id called with project_id={project_id}")
        result = await self.project_repo.get_by_id(project_id)
        logger.debug(f"get_project_by_id completed, found={result is not None}")
        return result
    
    async def get_project_by_unique_id(
        self, project_unique_id: str
    ) -> Optional[Project]:
        """Get a project by its unique identifier.

        Args:
            project_unique_id: The project's unique identifier.

        Returns:
            Project instance if found, None otherwise.
        """
        logger.debug(f"get_project_by_unique_id called with project_unique_id={project_unique_id}")
        result = await self.project_repo.get_by_unique_id(project_unique_id)
        logger.debug(f"get_project_by_unique_id completed, found={result is not None}")
        return result
    
    async def list_projects(
        self,
        offset: int = 0,
        limit: int = 100,
        name: Optional[str] = None,
    ) -> List[Project]:
        """List projects with pagination and optional name filter.

        Args:
            offset: Offset for pagination (default: 0).
            limit: Maximum number of results (default: 100).
            name: Optional name filter (fuzzy match, case-insensitive).

        Returns:
            List of projects matching the criteria.
        """
        logger.debug(f"list_projects called with offset={offset}, limit={limit}, name={name}")
        result = await self.project_repo.list(
            offset=offset,
            limit=limit,
            name=name,
        )
        logger.debug(f"list_projects completed, returned {len(result)} projects")
        return result
    
    async def update_project(
        self,
        project_id: int,
        **kwargs
    ) -> Optional[Project]:
        """Update a project's information.

        Args:
            project_id: The project's primary key.
            **kwargs: Fields to update with new values.

        Returns:
            Updated Project instance if found, None otherwise.
        """
        logger.debug(f"update_project called with project_id={project_id}")
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            logger.debug(f"update_project completed, project not found")
            return None

        # Auto-update time_updated
        kwargs["time_updated"] = int(time.time())

        logger.info(f"Business decision: updating project {project_id}")
        updated = await self.project_repo.update(project, **kwargs)
        await self.session.commit()
        await self.session.refresh(updated)

        logger.debug(f"update_project completed")
        return updated
    
    async def delete_project(self, project_id: int) -> bool:
        """Delete a project by ID.

        Cascades to related workspaces, sessions, and messages
        as defined in the model relationships.

        Args:
            project_id: The project's primary key.

        Returns:
            True if deleted, False if not found.
        """
        logger.debug(f"delete_project called with project_id={project_id}")
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            logger.debug(f"delete_project completed, project not found")
            return False

        logger.info(f"Business decision: deleting project {project_id}")
        await self.project_repo.delete(project)
        await self.session.commit()

        logger.debug(f"delete_project completed")
        return True
