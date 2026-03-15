"""Project service for business logic."""

import os
from pathlib import Path
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_config
from database.models import DIRECTORY_PATTERN, Project
from repositories.project_repository import ProjectRepository
from utils.id_generator import generate_uuidv7
from utils.timestamp import get_timestamp_ms
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
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repo = ProjectRepository(session)

    @staticmethod
    def _validate_directory(directory: str) -> None:
        if not DIRECTORY_PATTERN.match(directory):
            raise ValueError(
                f"Invalid directory name '{directory}'. "
                f"Must match pattern: [0-9a-zA-Z_-]+"
            )

    def _compute_full_workspace_path(self, directory: str) -> Path:
        config = get_config()
        return Path(config.projects.root) / directory

    def _compute_full_project_path(self, directory: str) -> Path:
        """Compute the full path for a project directory.

        Args:
            directory: The project directory name.

        Returns:
            Full Path to the project directory.
        """
        config = get_config()
        return Path(config.projects.root) / directory

    def _create_project_directory(self, directory: str) -> Path:
        """Create the physical directory for a project.

        Args:
            directory: The project directory name.

        Returns:
            The created Path.

        Raises:
            ValueError: If the directory already exists.
            OSError: If directory creation fails.
        """
        full_path = self._compute_full_project_path(directory)
        if full_path.exists():
            raise ValueError(
                f"Directory already exists: {full_path}"
            )
        try:
            full_path.mkdir(parents=True, exist_ok=False)
            logger.info(f"Created project directory: {full_path}")
            return full_path
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    async def create_project(
        self,
        directory: str,
        name: str,
        branch: Optional[str] = None,
        project_unique_id: Optional[str] = None,
    ) -> Project:
        logger.debug(f"create_project called with directory={directory}")
        self._validate_directory(directory)

        # Create physical directory first
        created_path = self._create_project_directory(directory)

        if project_unique_id is None:
            project_unique_id = generate_uuidv7()

        current_time = get_timestamp_ms()

        try:
            logger.info(f"Business decision: creating project {project_unique_id}")
            project = await self.project_repo.create(
                project_unique_id=project_unique_id,
                directory=directory,
                name=name,
                branch=branch,
                gmt_create=current_time,
                gmt_modified=current_time,
            )

            await self.session.commit()
            await self.session.refresh(project)

            logger.debug(f"create_project completed")
            return project
        except Exception as e:
            # Rollback: remove created directory if DB operation fails
            logger.error(f"DB operation failed, rolling back directory creation: {e}")
            try:
                os.rmdir(created_path)
                logger.info(f"Rolled back directory creation: {created_path}")
            except OSError as rollback_error:
                logger.warning(f"Failed to rollback directory {created_path}: {rollback_error}")
            raise
    
    async def get_project_by_id(self, project_id: int) -> Optional[Project]:
        logger.debug(f"get_project_by_id called with project_id={project_id}")
        result = await self.project_repo.get_by_id(project_id)
        logger.debug(f"get_project_by_id completed, found={result is not None}")
        return result

    async def get_project_by_unique_id(
        self, project_unique_id: str
    ) -> Optional[Project]:
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
        logger.debug(f"update_project called with project_id={project_id}")
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            logger.debug(f"update_project completed, project not found")
            return None

        if "directory" in kwargs:
            self._validate_directory(kwargs["directory"])

        kwargs["gmt_modified"] = get_timestamp_ms()

        logger.info(f"Business decision: updating project {project_id}")
        updated = await self.project_repo.update(project, **kwargs)
        await self.session.commit()
        await self.session.refresh(updated)

        logger.debug(f"update_project completed")
        return updated

    async def update_latest_active_time(self, project_unique_id: str) -> Optional[Project]:
        logger.debug(f"update_latest_active_time called for {project_unique_id}")
        project = await self.project_repo.get_by_unique_id(project_unique_id)
        if not project:
            logger.debug(f"update_latest_active_time completed, project not found")
            return None

        updated = await self.project_repo.update(
            project,
            latest_active_time=get_timestamp_ms(),
            gmt_modified=get_timestamp_ms(),
        )
        await self.session.commit()
        await self.session.refresh(updated)

        logger.debug(f"update_latest_active_time completed")
        return updated

    async def delete_project(self, project_id: int) -> bool:
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
