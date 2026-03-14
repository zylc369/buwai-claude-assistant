"""Project service for business logic."""

import re
import time
from pathlib import Path
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_config
from database.models import Project
from repositories.project_repository import ProjectRepository
from utils.id_generator import generate_uuidv7
from logger import get_logger

logger = get_logger(__name__)

# Directory name validation pattern: alphanumeric and underscores only
DIRECTORY_PATTERN = re.compile(r'^[0-9a-zA-Z_]+$')


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
                f"Must match pattern: [0-9a-zA-Z_]+"
            )

    def _compute_full_workspace_path(self, directory: str) -> Path:
        config = get_config()
        return Path(config.projects.root) / directory
    
    async def create_project(
        self,
        directory: str,
        name: Optional[str] = None,
        branch: Optional[str] = None,
        time_initialized: Optional[int] = None,
        project_unique_id: Optional[str] = None,
    ) -> Project:
        logger.debug(f"create_project called with directory={directory}")
        self._validate_directory(directory)

        if project_unique_id is None:
            project_unique_id = generate_uuidv7()

        current_time = int(time.time())

        logger.info(f"Business decision: creating project {project_unique_id}")
        project = await self.project_repo.create(
            project_unique_id=project_unique_id,
            directory=directory,
            name=name,
            branch=branch,
            time_initialized=time_initialized,
            gmt_create=current_time,
            gmt_modified=current_time,
        )

        await self.session.commit()
        await self.session.refresh(project)

        logger.debug(f"create_project completed")
        return project
    
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

        kwargs["gmt_modified"] = int(time.time())

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
            latest_active_time=int(time.time()),
            gmt_modified=int(time.time()),
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
