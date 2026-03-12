"""User service for business logic."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from repositories.user_repository import UserRepository


class UserService:
    """Service layer for user operations.
    
    Handles business logic for user management, coordinating
    between repositories and enforcing business rules.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize UserService with database session.
        
        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.user_repo = UserRepository(session)
    
    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None
    ) -> User:
        """Create a new user with validation.
        
        Args:
            email: User email address.
            username: Unique username.
            password: Plain text password (will be hashed).
            full_name: Optional full name.
            
        Returns:
            Created user instance.
            
        Raises:
            ValueError: If email or username already exists.
        """
        # Check if email already exists
        if await self.user_repo.email_exists(email):
            raise ValueError(f"Email '{email}' already registered")
        
        # Check if username already exists
        if await self.user_repo.username_exists(username):
            raise ValueError(f"Username '{username}' already taken")
        
        # Hash password (in production, use bcrypt or similar)
        # For now, just use placeholder
        hashed_password = f"hashed_{password}"
        
        # Create user
        user = await self.user_repo.create(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_admin=False
        )
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            user_id: User ID.
            
        Returns:
            User instance if found, None otherwise.
        """
        return await self.user_repo.get_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email.
        
        Args:
            email: User email.
            
        Returns:
            User instance if found, None otherwise.
        """
        return await self.user_repo.get_by_email(email)
    
    async def get_all_users(self, offset: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination.
        
        Args:
            offset: Pagination offset.
            limit: Maximum number of results.
            
        Returns:
            List of users.
        """
        return await self.user_repo.get_all(offset=offset, limit=limit)
    
    async def update_user(
        self,
        user_id: int,
        **kwargs
    ) -> Optional[User]:
        """Update user information.
        
        Args:
            user_id: User ID to update.
            **kwargs: Fields to update.
            
        Returns:
            Updated user instance.
            
        Raises:
            ValueError: If user not found or validation fails.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Validate email uniqueness if changing email
        if 'email' in kwargs and kwargs['email'] != user.email:
            if await self.user_repo.email_exists(kwargs['email']):
                raise ValueError(f"Email '{kwargs['email']}' already registered")
        
        # Validate username uniqueness if changing username
        if 'username' in kwargs and kwargs['username'] != user.username:
            if await self.user_repo.username_exists(kwargs['username']):
                raise ValueError(f"Username '{kwargs['username']}' already taken")
        
        updated_user = await self.user_repo.update(user, **kwargs)
        await self.session.commit()
        await self.session.refresh(updated_user)
        
        return updated_user
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user.
        
        Args:
            user_id: User ID to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        await self.user_repo.delete(user)
        await self.session.commit()
        
        return True
    
    async def get_active_users(self) -> List[User]:
        """Get all active users.
        
        Returns:
            List of active users.
        """
        return await self.user_repo.get_active_users()
