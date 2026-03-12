"""Task service for business logic."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Task
from repositories.task_repository import TaskRepository


class TaskService:
    """Service layer for task management."""
    
    VALID_STATUSES = ["pending", "in_progress", "completed", "cancelled"]
    VALID_PRIORITIES = ["low", "normal", "high"]
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
    
    async def create_task(
        self,
        title: str,
        project_id: int,
        description: Optional[str] = None,
        assignee_id: Optional[int] = None,
        status: str = "pending",
        priority: str = "normal",
        due_date: Optional[datetime] = None
    ) -> Task:
        """Create a new task."""
        # Validate status
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {self.VALID_STATUSES}")
        
        # Validate priority
        if priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Invalid priority. Must be one of: {self.VALID_PRIORITIES}")
        
        task = await self.task_repo.create(
            title=title,
            description=description,
            project_id=project_id,
            assignee_id=assignee_id,
            status=status,
            priority=priority,
            due_date=due_date
        )
        
        await self.session.commit()
        await self.session.refresh(task)
        
        return task
    
    async def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        return await self.task_repo.get_by_id(task_id)
    
    async def get_project_tasks(self, project_id: int) -> List[Task]:
        """Get all tasks for a project."""
        return await self.task_repo.get_by_project(project_id)
    
    async def get_user_tasks(self, assignee_id: int) -> List[Task]:
        """Get all tasks assigned to a user."""
        return await self.task_repo.get_by_assignee(assignee_id)
    
    async def update_task(
        self,
        task_id: int,
        **kwargs
    ) -> Optional[Task]:
        """Update task information."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return None
        
        # Validate status if provided
        if 'status' in kwargs and kwargs['status'] not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {self.VALID_STATUSES}")
        
        # Validate priority if provided
        if 'priority' in kwargs and kwargs['priority'] not in self.VALID_PRIORITIES:
            raise ValueError(f"Invalid priority. Must be one of: {self.VALID_PRIORITIES}")
        
        updated = await self.task_repo.update(task, **kwargs)
        await self.session.commit()
        await self.session.refresh(updated)
        
        return updated
    
    async def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return False
        
        await self.task_repo.delete(task)
        await self.session.commit()
        
        return True
    
    async def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks."""
        return await self.task_repo.get_overdue_tasks()
    
    async def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get tasks by status."""
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {self.VALID_STATUSES}")
        return await self.task_repo.get_by_status(status)
