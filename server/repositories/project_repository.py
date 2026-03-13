"""Project repository for database operations."""

from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project
from repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model operations.
    
    Provides project-specific database operations on top of base CRUD.
    
    Attributes:
        model: The Project model class.
    
    Example:
        async with async_session() as session:
            repo = ProjectRepository(session)
            projects = await repo.list(offset=0, limit=10)
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize ProjectRepository with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session)
        self.model = Project
    
    async def get_by_unique_id(self, project_unique_id: str) -> Optional[Project]:
        """Get a project by its unique identifier.
        
        Args:
            project_unique_id: The unique identifier of the project.
            
        Returns:
            Project instance if found, None otherwise.
        """
        result = await self.session.execute(
            select(Project).where(Project.project_unique_id == project_unique_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str, exact: bool = False) -> List[Project]:
        """Get projects by name.
        
        Args:
            name: The project name to search for.
            exact: If True, do exact match; if False, do fuzzy/partial match.
            
        Returns:
            List of matching projects.
        """
        if exact:
            result = await self.session.execute(
                select(Project).where(Project.name == name)
            )
        else:
            result = await self.session.execute(
                select(Project).where(
                    func.lower(Project.name).like(f"%{name.lower()}%")
                )
            )
        return list(result.scalars().all())
    
    async def list(
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
        query = select(Project)
        
        # Apply name filter if provided (fuzzy match)
        if name:
            query = query.where(
                func.lower(Project.name).like(f"%{name.lower()}%")
            )
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # Inherited methods from BaseRepository:
    # - get_by_id(id: int) -> Optional[Project]
    # - create(**kwargs) -> Project
    # - update(instance: Project, **kwargs) -> Project
    # - delete(instance: Project) -> None
    # - count(**filters) -> int
    # - exists(id: int) -> bool
