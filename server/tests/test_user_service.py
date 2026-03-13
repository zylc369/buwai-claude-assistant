"""Tests for UserService."""

import pytest
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services import UserService


class TestUserServiceCreate:
    """Tests for UserService.create_user method."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession):
        """Test creating a user successfully."""
        service = UserService(db_session)
        
        user = await service.create_user(
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="Test User"
        )
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.hashed_password.startswith("hashed_")

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, db_session: AsyncSession):
        """Test that duplicate email raises ValueError."""
        service = UserService(db_session)
        
        await service.create_user(
            email="test@example.com",
            username="testuser1",
            password="password123"
        )
        
        with pytest.raises(ValueError, match="already registered"):
            await service.create_user(
                email="test@example.com",
                username="testuser2",
                password="password456"
            )

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, db_session: AsyncSession):
        """Test that duplicate username raises ValueError."""
        service = UserService(db_session)
        
        await service.create_user(
            email="test1@example.com",
            username="testuser",
            password="password123"
        )
        
        with pytest.raises(ValueError, match="already taken"):
            await service.create_user(
                email="test2@example.com",
                username="testuser",
                password="password456"
            )

    @pytest.mark.asyncio
    async def test_create_user_without_full_name(self, db_session: AsyncSession):
        """Test creating user without optional full_name."""
        service = UserService(db_session)
        
        user = await service.create_user(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        
        assert user.full_name is None


class TestUserServiceGet:
    """Tests for UserService get methods."""

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session: AsyncSession):
        """Test getting user by ID."""
        service = UserService(db_session)
        
        created = await service.create_user(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        
        found = await service.get_user(created.id)
        
        assert found is not None
        assert found.id == created.id
        assert found.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent user returns None."""
        service = UserService(db_session)
        
        found = await service.get_user(999)
        
        assert found is None

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session: AsyncSession):
        """Test getting user by email."""
        service = UserService(db_session)
        
        await service.create_user(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        
        found = await service.get_user_by_email("test@example.com")
        
        assert found is not None
        assert found.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_all_users(self, db_session: AsyncSession):
        """Test getting all users with pagination."""
        service = UserService(db_session)
        
        for i in range(5):
            await service.create_user(
                email=f"test{i}@example.com",
                username=f"testuser{i}",
                password="password123"
            )
        
        users = await service.get_all_users(offset=0, limit=10)
        
        assert len(users) == 5

    @pytest.mark.asyncio
    async def test_get_active_users(self, db_session: AsyncSession):
        """Test getting active users only."""
        service = UserService(db_session)
        
        # Create active user
        await service.create_user(
            email="active@example.com",
            username="activeuser",
            password="password123"
        )
        
        # Create and deactivate user
        inactive = await service.create_user(
            email="inactive@example.com",
            username="inactiveuser",
            password="password123"
        )
        await service.update_user(inactive.id, is_active=False)
        
        active_users = await service.get_active_users()
        
        assert len(active_users) == 1
        assert active_users[0].username == "activeuser"


class TestUserServiceUpdate:
    """Tests for UserService.update_user method."""

    @pytest.mark.asyncio
    async def test_update_user_email(self, db_session: AsyncSession):
        """Test updating user email."""
        service = UserService(db_session)
        
        user = await service.create_user(
            email="old@example.com",
            username="testuser",
            password="password123"
        )
        
        updated = await service.update_user(user.id, email="new@example.com")
        
        assert updated.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_update_user_duplicate_email(self, db_session: AsyncSession):
        """Test that updating to duplicate email raises ValueError."""
        service = UserService(db_session)
        
        await service.create_user(
            email="user1@example.com",
            username="user1",
            password="password123"
        )
        
        user2 = await service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )
        
        with pytest.raises(ValueError, match="already registered"):
            await service.update_user(user2.id, email="user1@example.com")

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, db_session: AsyncSession):
        """Test updating non-existent user raises ValueError."""
        service = UserService(db_session)
        
        with pytest.raises(ValueError, match="not found"):
            await service.update_user(999, email="test@example.com")


class TestUserServiceDelete:
    """Tests for UserService.delete_user method."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, db_session: AsyncSession):
        """Test deleting user successfully."""
        service = UserService(db_session)
        
        user = await service.create_user(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        
        result = await service.delete_user(user.id)
        
        assert result is True
        
        # Verify user is deleted
        found = await service.get_user(user.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, db_session: AsyncSession):
        """Test deleting non-existent user returns False."""
        service = UserService(db_session)
        
        result = await service.delete_user(999)
        
        assert result is False
