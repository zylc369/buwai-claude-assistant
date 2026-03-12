"""User API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from services import UserService
from database.models import User


router = APIRouter(prefix="/users", tags=["users"])


# Pydantic models for request/response
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    full_name: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new user."""
    service = UserService(db)
    try:
        user = await service.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[UserResponse])
async def list_users(
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Get all users."""
    service = UserService(db)
    users = await service.get_all_users(offset=offset, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific user by ID."""
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a user."""
    service = UserService(db)
    try:
        # Only include non-None fields
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        user = await service.update_user(user_id, **update_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a user."""
    service = UserService(db)
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
