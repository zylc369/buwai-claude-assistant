"""Project service for business logic."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project
from repositories.project_repository import ProjectRepository


class ProjectService:
    """Service layer for project management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repo = ProjectRepository(session)
    
    async def create_project(
        self,
        name: str,
        owner_id: int,
        description: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        project = await self.project_repo.create(
            name=name,
            description=description,
            owner_id=owner_id
        )
        
        await self.session.commit()
        await self.session.refresh(project)
        
        return project
    
    async def get_project(self, project_id: int) -> Optional[Project]:
        """Get a project by ID."""
        return await self.project_repo.get_by_id(project_id)
    
    async def get_user_projects(self, owner_id: int) -> List[Project]:
        """Get all projects for a user."""
        return await self.project_repo.get_by_owner(owner_id)
    
    async def update_project(
        self,
        project_id: int,
        **kwargs
    ) -> Optional[Project]:
        """Update project information."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return None
        
        updated = await self.project_repo.update(project, **kwargs)
        await self.session.commit()
        await self.session.refresh(updated)
        
        return updated
    
    async def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return False
        
        await self.project_repo.delete(project)
        await self.session.commit()
        
        return True
    
    async def search_projects(self, query: str) -> List[Project]:
        """Search projects by name."""
        return await self.project_repo.search_by_name(query)
