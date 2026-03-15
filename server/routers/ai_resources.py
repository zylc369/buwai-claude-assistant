"""AI Resource API endpoints."""

import json
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import AiResourceService
from logger import get_logger


router = APIRouter(prefix="/ai-resources", tags=["AI Resources"])
logger = get_logger(__name__)


# Pydantic Schemas
class ContentSchema(BaseModel):
    type: Literal["MD", "SHELL"]
    data: str


class AIResourceCreate(BaseModel):
    name: str = Field(..., description="Resource name")
    type: Literal["SKILL", "COMMAND", "SYSTEM_PROMPT"] = Field(..., description="Resource type")
    sub_type: str = Field(default="", description="Sub-type for the resource")
    owner: str | None = Field(None, description="Owner workspace directory")
    disabled: bool = Field(default=False, description="Whether the resource is disabled")
    content: ContentSchema = Field(..., description="Resource content")
    test: bool = Field(default=False, description="Use test data")


class AIResourceUpdate(BaseModel):
    name: str | None = Field(None, description="Resource name")
    type: Literal["SKILL", "COMMAND", "SYSTEM_PROMPT"] | None = Field(None, description="Resource type")
    sub_type: str | None = Field(None, description="Sub-type for the resource")
    owner: str | None = Field(None, description="Owner workspace directory")
    disabled: bool | None = Field(None, description="Whether the resource is disabled")
    content: ContentSchema | None = Field(None, description="Resource content")
    test: bool | None = Field(None, description="Use test data")


class AIResourceResponse(BaseModel):
    id: int
    resource_unique_id: str
    name: str
    type: str
    sub_type: str
    owner: str | None
    disabled: bool
    content: dict
    gmt_create: int
    gmt_modified: int
    test: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=AIResourceResponse, status_code=201)
async def create_ai_resource(
    request: Request,
    resource_data: AIResourceCreate,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data"),
):
    """Create a new AI resource.

    Args:
        resource_data: AI resource creation data.

    Returns:
        Created AI resource.
    """
    logger.info(f"create_ai_resource called: {request.method} {request.url.path}")
    logger.debug(f"params: name={resource_data.name}, type={resource_data.type}")

    service = AiResourceService(db)

    content_dict = resource_data.content.model_dump()

    resource = await service.create_ai_resource(
        name=resource_data.name,
        type=resource_data.type,
        sub_type=resource_data.sub_type,
        owner=resource_data.owner,
        disabled=resource_data.disabled,
        content=content_dict,
        test=test or resource_data.test,
    )

    resource_dict = {
        "id": resource.id,
        "resource_unique_id": resource.resource_unique_id,
        "name": resource.name,
        "type": resource.type,
        "sub_type": resource.sub_type,
        "owner": resource.owner,
        "disabled": resource.disabled,
        "content": json.loads(resource.content) if resource.content else {},
        "gmt_create": resource.gmt_create,
        "gmt_modified": resource.gmt_modified,
        "test": resource.test,
    }

    logger.info(f"create_ai_resource completed: status=201")
    return AIResourceResponse(**resource_dict)


@router.get("/", response_model=List[AIResourceResponse])
async def list_ai_resources(
    request: Request,
    test: bool = Query(False, description="Use test data"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db_session),
):
    """List AI resources with pagination.

    Args:
        offset: Offset for pagination.
        limit: Maximum number of results.

    Returns:
        List of AI resources.
    """
    logger.info(f"list_ai_resources called: {request.method} {request.url.path}")
    logger.debug(f"params: offset={offset}, limit={limit}")

    service = AiResourceService(db)
    resources = await service.list_ai_resources(
        offset=offset,
        limit=limit,
        test=test,
    )

    # Parse JSON content for each resource
    response_resources = []
    for resource in resources:
        resource_dict = {
            "id": resource.id,
            "resource_unique_id": resource.resource_unique_id,
            "name": resource.name,
            "type": resource.type,
            "sub_type": resource.sub_type,
            "owner": resource.owner,
            "disabled": resource.disabled,
            "content": json.loads(resource.content) if resource.content else {},
            "gmt_create": resource.gmt_create,
            "gmt_modified": resource.gmt_modified,
            "test": resource.test,
        }
        response_resources.append(AIResourceResponse(**resource_dict))

    logger.info(f"list_ai_resources completed: status=200")
    return response_resources


@router.get("/{resource_unique_id}", response_model=AIResourceResponse)
async def get_ai_resource(
    request: Request,
    resource_unique_id: str,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data"),
):
    """Get a specific AI resource by unique ID.

    Args:
        resource_unique_id: The resource's unique identifier.

    Returns:
        AI resource data.

    Raises:
        HTTPException: 404 if resource not found.
    """
    logger.info(f"get_ai_resource called: {request.method} {request.url.path}")
    logger.debug(f"params: resource_unique_id={resource_unique_id}")

    service = AiResourceService(db)
    resource = await service.get_ai_resource_by_unique_id(resource_unique_id, test=test)

    if not resource:
        logger.error(f"get_ai_resource failed: Resource '{resource_unique_id}' not found")
        raise HTTPException(
            status_code=404,
            detail=f"Resource '{resource_unique_id}' not found"
        )

    # Parse JSON content
    resource_dict = {
        "id": resource.id,
        "resource_unique_id": resource.resource_unique_id,
        "name": resource.name,
        "type": resource.type,
        "sub_type": resource.sub_type,
        "owner": resource.owner,
        "disabled": resource.disabled,
        "content": json.loads(resource.content) if resource.content else {},
        "gmt_create": resource.gmt_create,
        "gmt_modified": resource.gmt_modified,
        "test": resource.test,
    }

    logger.info(f"get_ai_resource completed: status=200")
    return AIResourceResponse(**resource_dict)


@router.put("/{resource_unique_id}", response_model=AIResourceResponse)
async def update_ai_resource(
    request: Request,
    resource_unique_id: str,
    resource_data: AIResourceUpdate,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data"),
):
    """Update an AI resource.

    Args:
        resource_unique_id: The resource's unique identifier.
        resource_data: Fields to update.

    Returns:
        Updated AI resource.

    Raises:
        HTTPException: 404 if resource not found.
    """
    logger.info(f"update_ai_resource called: {request.method} {request.url.path}")
    logger.debug(f"params: resource_unique_id={resource_unique_id}")

    service = AiResourceService(db)

    resource = await service.get_ai_resource_by_unique_id(resource_unique_id, test=test)
    if not resource:
        logger.error(f"update_ai_resource failed: Resource '{resource_unique_id}' not found")
        raise HTTPException(
            status_code=404,
            detail=f"Resource '{resource_unique_id}' not found"
        )

    update_data = {k: v for k, v in resource_data.model_dump(exclude_unset=True).items() if v is not None}

    # Convert content to dict if provided
    if "content" in update_data:
        update_data["content"] = update_data["content"].model_dump()

    if "test" in update_data:
        del update_data["test"]

    if not update_data:
        logger.info(f"update_ai_resource completed: status=200 (no changes)")
        # Return the existing resource without changes
        resource_dict = {
            "id": resource.id,
            "resource_unique_id": resource.resource_unique_id,
            "name": resource.name,
            "type": resource.type,
            "sub_type": resource.sub_type,
            "owner": resource.owner,
            "disabled": resource.disabled,
            "content": json.loads(resource.content) if resource.content else {},
            "gmt_create": resource.gmt_create,
            "gmt_modified": resource.gmt_modified,
            "test": resource.test,
        }
        return AIResourceResponse(**resource_dict)

    updated = await service.update_ai_resource(resource_unique_id, test=test, **update_data)

    # Parse JSON content for response
    updated_dict = {
        "id": updated.id,
        "resource_unique_id": updated.resource_unique_id,
        "name": updated.name,
        "type": updated.type,
        "sub_type": updated.sub_type,
        "owner": updated.owner,
        "disabled": updated.disabled,
        "content": json.loads(updated.content) if updated.content else {},
        "gmt_create": updated.gmt_create,
        "gmt_modified": updated.gmt_modified,
        "test": updated.test,
    }

    logger.info(f"update_ai_resource completed: status=200")
    return AIResourceResponse(**updated_dict)


@router.delete("/{resource_unique_id}", status_code=204)
async def delete_ai_resource(
    request: Request,
    resource_unique_id: str,
    db: AsyncSession = Depends(get_db_session),
    test: bool = Query(False, description="Use test data"),
):
    """Delete an AI resource.

    Args:
        resource_unique_id: The resource's unique identifier.

    Raises:
        HTTPException: 404 if resource not found.
    """
    logger.info(f"delete_ai_resource called: {request.method} {request.url.path}")
    logger.debug(f"params: resource_unique_id={resource_unique_id}")

    service = AiResourceService(db)

    resource = await service.get_ai_resource_by_unique_id(resource_unique_id, test=test)
    if not resource:
        logger.error(f"delete_ai_resource failed: Resource '{resource_unique_id}' not found")
        raise HTTPException(
            status_code=404,
            detail=f"Resource '{resource_unique_id}' not found"
        )

    deleted = await service.delete_ai_resource(resource_unique_id, test=test)
    if not deleted:
        logger.error(f"delete_ai_resource failed: Failed to delete resource")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete resource"
        )

    logger.info(f"delete_ai_resource completed: status=204")
