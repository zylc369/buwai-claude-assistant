"""Task repository for database operations."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Task
from repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository for Task model operations.
    
    Provides task-specific database operations on top of base CRUD.
    
    Attributes:
        model: The Task model class.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize TaskRepository with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session)
        self.model = Task
    
    async def get_by_project(self, project_id: int) -> List[Task]:
        """Get all tasks for a specific project.
        
        Args:
            project_id: Project ID to filter by.
            
        Returns:
            List of tasks in the project.
        """
        result = await self.session.execute(
            select(Task).where(Task.project_id == project_id)
        )
        return list(result.scalars().all())
    
    async def get_by_assignee(self, assignee_id: int) -> List[Task]:
        """Get all tasks assigned to a specific user.
        
        Args:
            assignee_id: User ID to filter by.
            
        Returns:
            List of tasks assigned to the user.
        """
        result = await self.session.execute(
            select(Task).where(Task.assignee_id == assignee_id)
        )
        return list(result.scalars().all())
    
    async def get_by_status(self, status: str) -> List[Task]:
        """Get all tasks with a specific status.
        
        Args:
            status: Status to filter by (e.g., "pending", "in_progress", "completed").
            
        Returns:
            List of tasks with the given status.
        """
        result = await self.session.execute(
            select(Task).where(Task.status == status)
        )
        return list(result.scalars().all())
    
    async def get_by_priority(self, priority: str) -> List[Task]:
        """Get all tasks with a specific priority.
        
        Args:
            priority: Priority to filter by (e.g., "low", "normal", "high").
            
        Returns:
            List of tasks with the given priority.
        """
        result = await self.session.execute(
            select(Task).where(Task.priority == priority)
        )
        return list(result.scalars().all())
    
    async def get_overdue_tasks(self) -> List[Task]:
        """Get all tasks that are overdue (due_date < now and status != completed).
        
        Returns:
            List of overdue tasks.
        """
        result = await self.session.execute(
            select(Task).where(
                Task.due_date < datetime.utcnow(),
                Task.status != "completed"
            )
        )
        return list(result.scalars().all())
    
    async def count_tasks_by_project(self, project_id: int) -> int:
        """Count total tasks for a specific project.
        
        Args:
            project_id: Project ID to count tasks for.
            
        Returns:
            Number of tasks in the project.
        """
        result = await self.session.execute(
            select(Task).where(Task.project_id == project_id)
        )
        return len(result.scalars().all())
