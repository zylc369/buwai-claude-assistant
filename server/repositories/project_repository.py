"""Project repository for database operations."""

from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project
from repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model operations.
    
    Provides project-specific database operations on top of base CRUD.
    
    Attributes:
        model: The Project model class.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize ProjectRepository with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session)
        self.model = Project
    
    async def get_by_owner(self, owner_id: int) -> List[Project]:
        """Get all projects owned by a specific user.
        
        Args:
            owner_id: User ID who owns the projects.
            
        Returns:
            List of projects owned by the user.
        """
        result = await self.session.execute(
            select(Project).where(Project.owner_id == owner_id)
        )
        return list(result.scalars().all())
    
    async def search_by_name(self, name_query: str) -> List[Project]:
        """Search projects by name (case-insensitive partial match).
        
        Args:
            name_query: Search string to match against project names.
            
        Returns:
            List of matching projects.
        """
        result = await self.session.execute(
            select(Project).where(
                func.lower(Project.name).like(f"%{name_query.lower()}%")
            )
        )
        return list(result.scalars().all())
    
    async def count_projects_by_owner(self, owner_id: int) -> int:
        """Count total projects for a specific owner.
        
        Args:
            owner_id: User ID to count projects for.
            
        Returns:
            Number of projects owned by the user.
        """
        result = await self.session.execute(
            select(Project).where(Project.owner_id == owner_id)
        )
        return len(result.scalars().all())
