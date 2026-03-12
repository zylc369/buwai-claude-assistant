"""User repository for database operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations.
    
    Provides user-specific database operations on top of base CRUD.
    
    Attributes:
        model: The User model class.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize UserRepository with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session)
        self.model = User
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address.
        
        Args:
            email: User's email address.
            
        Returns:
            User instance if found, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username.
        
        Args:
            username: User's username.
            
        Returns:
            User instance if found, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_active_users(self) -> List[User]:
        """Get all active users.
        
        Returns:
            List of users where is_active=True.
        """
        result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())
    
    async def get_admin_users(self) -> List[User]:
        """Get all admin users.
        
        Returns:
            List of users where is_admin=True.
        """
        result = await self.session.execute(
            select(User).where(User.is_admin == True)
        )
        return list(result.scalars().all())
    
    async def email_exists(self, email: str) -> bool:
        """Check if an email address is already registered.
        
        Args:
            email: Email address to check.
            
        Returns:
            True if email exists, False otherwise.
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None
    
    async def username_exists(self, username: str) -> bool:
        """Check if a username is already taken.
        
        Args:
            username: Username to check.
            
        Returns:
            True if username exists, False otherwise.
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None
