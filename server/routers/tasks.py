"""Task API endpoints."""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import TaskService


router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    project_id: int
    description: str | None = None
    assignee_id: int | None = None
    status: str = "pending"
    priority: str = "normal"
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    status: str | None = None
    priority: str | None = None
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    project_id: int
    assignee_id: int | None
    status: str
    priority: str
    due_date: datetime | None
    
    class Config:
        from_attributes = True


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new task."""
    service = TaskService(db)
    try:
        task = await service.create_task(
            title=task_data.title,
            project_id=task_data.project_id,
            description=task_data.description,
            assignee_id=task_data.assignee_id,
            status=task_data.status,
            priority=task_data.priority,
            due_date=task_data.due_date
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    project_id: int | None = None,
    assignee_id: int | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Get tasks with optional filters."""
    service = TaskService(db)
    
    if project_id:
        tasks = await service.get_project_tasks(project_id)
    elif assignee_id:
        tasks = await service.get_user_tasks(assignee_id)
    elif status:
        try:
            tasks = await service.get_tasks_by_status(status)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # For now, return empty list if no filter
        tasks = []
    
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific task."""
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a task."""
    service = TaskService(db)
    try:
        update_data = {k: v for k, v in task_data.dict().items() if v is not None}
        task = await service.update_task(task_id, **update_data)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a task."""
    service = TaskService(db)
    deleted = await service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/overdue/", response_model=List[TaskResponse])
async def get_overdue_tasks(
    db: AsyncSession = Depends(get_db_session)
):
    """Get all overdue tasks."""
    service = TaskService(db)
    tasks = await service.get_overdue_tasks()
    return tasks
