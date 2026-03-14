"""Workspace API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import WorkspaceService
from logger import get_logger


router = APIRouter(prefix="/workspaces", tags=["workspaces"])
logger = get_logger(__name__)


class WorkspaceCreate(BaseModel):
    workspace_unique_id: str
    project_unique_id: str
    name: str | None = None
    branch: str | None = None
    directory: str | None = None
    extra: str | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    branch: str | None = None
    directory: str | None = None
    extra: str | None = None


class WorkspaceResponse(BaseModel):
    id: int
    workspace_unique_id: str
    project_unique_id: str
    name: str | None
    branch: str | None
    directory: str | None
    extra: str | None
    
    class Config:
        from_attributes = True


@router.post("/", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    request: Request,
    workspace_data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new workspace."""
    logger.info(f"create_workspace called: {request.method} {request.url.path}")
    logger.debug(f"params: workspace_unique_id={workspace_data.workspace_unique_id}, project_unique_id={workspace_data.project_unique_id}")

    service = WorkspaceService(db)
    workspace = await service.create_workspace(
        workspace_unique_id=workspace_data.workspace_unique_id,
        project_unique_id=workspace_data.project_unique_id,
        name=workspace_data.name,
        branch=workspace_data.branch,
        directory=workspace_data.directory,
        extra=workspace_data.extra
    )

    logger.info(f"create_workspace completed: status=201")
    return workspace


@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    request: Request,
    project_unique_id: str = Query(..., description="Project unique ID (required)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get paginated list of workspaces for a project.

    project_unique_id is required.
    """
    logger.info(f"list_workspaces called: {request.method} {request.url.path}")
    logger.debug(f"params: project_unique_id={project_unique_id}, offset={offset}, limit={limit}")

    service = WorkspaceService(db)
    workspaces = await service.list_workspaces(
        project_unique_id=project_unique_id,
        offset=offset,
        limit=limit
    )

    logger.info(f"list_workspaces completed: status=200")
    return workspaces


@router.get("/{workspace_unique_id}", response_model=WorkspaceResponse)
async def get_workspace(
    request: Request,
    workspace_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific workspace by unique ID."""
    logger.info(f"get_workspace called: {request.method} {request.url.path}")
    logger.debug(f"params: workspace_unique_id={workspace_unique_id}")

    service = WorkspaceService(db)
    workspace = await service.get_workspace_by_unique_id(workspace_unique_id)
    if not workspace:
        logger.error(f"get_workspace failed: Workspace not found")
        raise HTTPException(status_code=404, detail="Workspace not found")

    logger.info(f"get_workspace completed: status=200")
    return workspace


@router.put("/{workspace_unique_id}", response_model=WorkspaceResponse)
async def update_workspace(
    request: Request,
    workspace_unique_id: str,
    workspace_data: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a workspace."""
    logger.info(f"update_workspace called: {request.method} {request.url.path}")
    logger.debug(f"params: workspace_unique_id={workspace_unique_id}")

    service = WorkspaceService(db)
    workspace = await service.get_workspace_by_unique_id(workspace_unique_id)
    if not workspace:
        logger.error(f"update_workspace failed: Workspace not found")
        raise HTTPException(status_code=404, detail="Workspace not found")

    update_data = {k: v for k, v in workspace_data.model_dump().items() if v is not None}
    updated_workspace = await service.update_workspace(workspace.id, **update_data)
    logger.info(f"update_workspace completed: status=200")
    return updated_workspace


@router.delete("/{workspace_unique_id}", status_code=204)
async def delete_workspace(
    request: Request,
    workspace_unique_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a workspace.

    Note: This will cascade delete all associated sessions.
    """
    logger.info(f"delete_workspace called: {request.method} {request.url.path}")
    logger.debug(f"params: workspace_unique_id={workspace_unique_id}")

    service = WorkspaceService(db)
    workspace = await service.get_workspace_by_unique_id(workspace_unique_id)
    if not workspace:
        logger.error(f"delete_workspace failed: Workspace not found")
        raise HTTPException(status_code=404, detail="Workspace not found")

    deleted = await service.delete_workspace(workspace.id)
    if not deleted:
        logger.error(f"delete_workspace failed: Failed to delete workspace")
        raise HTTPException(status_code=404, detail="Workspace not found")

    logger.info(f"delete_workspace completed: status=204")
