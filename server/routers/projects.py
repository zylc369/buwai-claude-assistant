"""Project API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import ProjectService
from logger import get_logger


router = APIRouter(prefix="/projects", tags=["projects"])
logger = get_logger(__name__)


# Request/Response Models
class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    directory: str = Field(..., description="Directory name for the project (alphanumeric, underscores, and hyphens)")
    project_unique_id: Optional[str] = Field(None, description="Unique identifier for the project (auto-generated if not provided)")
    name: str = Field(..., description="Project name (required)")
    branch: Optional[str] = Field(None, description="Optional git branch name")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    directory: Optional[str] = Field(None, description="Path to the project directory")
    name: Optional[str] = Field(None, description="Project name")
    branch: Optional[str] = Field(None, description="Git branch name")


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: int
    project_unique_id: str
    directory: str
    branch: Optional[str]
    name: str
    gmt_create: int
    gmt_modified: int
    latest_active_time: Optional[int] = None
    
    class Config:
        from_attributes = True


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: Request,
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new project.

    Args:
        project_data: Project creation data.

    Returns:
        Created project.

    Raises:
        HTTPException: 400 if project_unique_id already exists.
    """
    logger.info(f"create_project called: {request.method} {request.url.path}")
    logger.debug(f"params: project_unique_id={project_data.project_unique_id}")

    service = ProjectService(db)

    if project_data.project_unique_id:
        existing = await service.get_project_by_unique_id(project_data.project_unique_id)
        if existing:
            logger.error(f"create_project failed: Project with unique_id '{project_data.project_unique_id}' already exists")
            raise HTTPException(
                status_code=400,
                detail=f"Project with unique_id '{project_data.project_unique_id}' already exists"
            )

    try:
        project = await service.create_project(
            directory=project_data.directory,
            project_unique_id=project_data.project_unique_id,
            name=project_data.name,
            branch=project_data.branch,
        )
        logger.info(f"create_project completed: status=201")
        return project
    except Exception as e:
        logger.error(f"create_project failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    request: Request,
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    name: Optional[str] = Query(None, description="Filter by name (fuzzy match, case-insensitive)"),
    db: AsyncSession = Depends(get_db_session)
):
    """List projects with pagination and optional name filter.

    Args:
        offset: Offset for pagination.
        limit: Maximum number of results.
        name: Optional name filter (fuzzy match, case-insensitive).

    Returns:
        List of projects matching the criteria.
    """
    logger.info(f"list_projects called: {request.method} {request.url.path}")
    logger.debug(f"params: offset={offset}, limit={limit}, name={name}")

    service = ProjectService(db)
    projects = await service.list_projects(
        offset=offset,
        limit=limit,
        name=name,
    )

    logger.info(f"list_projects completed: status=200")
    return projects


@router.get("/{project_unique_id}", response_model=ProjectResponse)
async def get_project(
    request: Request,
    project_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific project by unique ID.

    Args:
        project_unique_id: The project's unique identifier.

    Returns:
        Project data.

    Raises:
        HTTPException: 404 if project not found.
    """
    logger.info(f"get_project called: {request.method} {request.url.path}")
    logger.debug(f"params: project_unique_id={project_unique_id}")

    service = ProjectService(db)
    project = await service.get_project_by_unique_id(project_unique_id)

    if not project:
        logger.error(f"get_project failed: Project '{project_unique_id}' not found")
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_unique_id}' not found"
        )

    logger.info(f"get_project completed: status=200")
    return project


@router.put("/{project_unique_id}", response_model=ProjectResponse)
async def update_project(
    request: Request,
    project_unique_id: str,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a project.

    Args:
        project_unique_id: The project's unique identifier.
        project_data: Fields to update.

    Returns:
        Updated project.

    Raises:
        HTTPException: 404 if project not found.
    """
    logger.info(f"update_project called: {request.method} {request.url.path}")
    logger.debug(f"params: project_unique_id={project_unique_id}")

    service = ProjectService(db)

    project = await service.get_project_by_unique_id(project_unique_id)
    if not project:
        logger.error(f"update_project failed: Project '{project_unique_id}' not found")
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_unique_id}' not found"
        )

    update_data = {k: v for k, v in project_data.model_dump().items() if v is not None}

    if not update_data:
        logger.info(f"update_project completed: status=200 (no changes)")
        return project

    updated = await service.update_project(project.id, **update_data)
    logger.info(f"update_project completed: status=200")
    return updated


@router.delete("/{project_unique_id}", status_code=204)
async def delete_project(
    request: Request,
    project_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a project (cascades to workspaces, sessions, messages).

    Args:
        project_unique_id: The project's unique identifier.

    Raises:
        HTTPException: 404 if project not found.
    """
    logger.info(f"delete_project called: {request.method} {request.url.path}")
    logger.debug(f"params: project_unique_id={project_unique_id}")

    service = ProjectService(db)

    project = await service.get_project_by_unique_id(project_unique_id)
    if not project:
        logger.error(f"delete_project failed: Project '{project_unique_id}' not found")
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_unique_id}' not found"
        )

    deleted = await service.delete_project(project.id)
    if not deleted:
        logger.error(f"delete_project failed: Failed to delete project")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete project"
        )

    logger.info(f"delete_project completed: status=204")
