"""Project API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    owner_id: int
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    
    class Config:
        from_attributes = True


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new project."""
    service = ProjectService(db)
    project = await service.create_project(
        name=project_data.name,
        owner_id=project_data.owner_id,
        description=project_data.description
    )
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    owner_id: int | None = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Get all projects or filter by owner."""
    service = ProjectService(db)
    if owner_id:
        projects = await service.get_user_projects(owner_id)
    else:
        # For now, return empty list if no filter
        # In production, you'd want admin-only access to all projects
        projects = []
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific project."""
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a project."""
    service = ProjectService(db)
    update_data = {k: v for k, v in project_data.dict().items() if v is not None}
    project = await service.update_project(project_id, **update_data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a project."""
    service = ProjectService(db)
    deleted = await service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
