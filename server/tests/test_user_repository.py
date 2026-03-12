"""Tests for UserRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from repositories.user_repository import UserRepository


@pytest.mark.asyncio
class TestUserRepository:
    """Test suite for UserRepository."""

    async def test_get_by_email_existing_user(self, db_session: AsyncSession):
        """Test retrieving a user by email when user exists."""
        # Arrange
        repo = UserRepository(db_session)
        user = await repo.create(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed123"
        )
        await db_session.commit()

        # Act
        found_user = await repo.get_by_email("test@example.com")

        # Assert
        assert found_user is not None
        assert found_user.email == "test@example.com"
        assert found_user.username == "testuser"
        assert found_user.id == user.id

    async def test_get_by_email_nonexistent_user(self, db_session: AsyncSession):
        """Test retrieving a user by email when user does not exist."""
        # Arrange
        repo = UserRepository(db_session)

        # Act
        found_user = await repo.get_by_email("nonexistent@example.com")

        # Assert
        assert found_user is None

    async def test_get_by_username_existing_user(self, db_session: AsyncSession):
        """Test retrieving a user by username when user exists."""
        # Arrange
        repo = UserRepository(db_session)
        user = await repo.create(
            email="test2@example.com",
            username="testuser2",
            hashed_password="hashed456"
        )
        await db_session.commit()

        # Act
        found_user = await repo.get_by_username("testuser2")

        # Assert
        assert found_user is not None
        assert found_user.username == "testuser2"
        assert found_user.id == user.id

    async def test_get_by_username_nonexistent_user(self, db_session: AsyncSession):
        """Test retrieving a user by username when user does not exist."""
        # Arrange
        repo = UserRepository(db_session)

        # Act
        found_user = await repo.get_by_username("nonexistent")

        # Assert
        assert found_user is None

    async def test_get_active_users(self, db_session: AsyncSession):
        """Test retrieving only active users."""
        # Arrange
        repo = UserRepository(db_session)
        await repo.create(
            email="active1@example.com",
            username="active1",
            hashed_password="hash1",
            is_active=True
        )
        await repo.create(
            email="active2@example.com",
            username="active2",
            hashed_password="hash2",
            is_active=True
        )
        await repo.create(
            email="inactive@example.com",
            username="inactive",
            hashed_password="hash3",
            is_active=False
        )
        await db_session.commit()

        # Act
        active_users = await repo.get_active_users()

        # Assert
        assert len(active_users) == 2
        emails = [u.email for u in active_users]
        assert "active1@example.com" in emails
        assert "active2@example.com" in emails
        assert "inactive@example.com" not in emails

    async def test_get_admin_users(self, db_session: AsyncSession):
        """Test retrieving only admin users."""
        # Arrange
        repo = UserRepository(db_session)
        await repo.create(
            email="admin1@example.com",
            username="admin1",
            hashed_password="hash1",
            is_admin=True
        )
        await repo.create(
            email="admin2@example.com",
            username="admin2",
            hashed_password="hash2",
            is_admin=True
        )
        await repo.create(
            email="regular@example.com",
            username="regular",
            hashed_password="hash3",
            is_admin=False
        )
        await db_session.commit()

        # Act
        admin_users = await repo.get_admin_users()

        # Assert
        assert len(admin_users) == 2
        emails = [u.email for u in admin_users]
        assert "admin1@example.com" in emails
        assert "admin2@example.com" in emails
        assert "regular@example.com" not in emails

    async def test_email_exists_true(self, db_session: AsyncSession):
        """Test checking if email exists when it does."""
        # Arrange
        repo = UserRepository(db_session)
        await repo.create(
            email="exists@example.com",
            username="exists",
            hashed_password="hash"
        )
        await db_session.commit()

        # Act
        exists = await repo.email_exists("exists@example.com")

        # Assert
        assert exists is True

    async def test_email_exists_false(self, db_session: AsyncSession):
        """Test checking if email exists when it doesn't."""
        # Arrange
        repo = UserRepository(db_session)

        # Act
        exists = await repo.email_exists("nonexistent@example.com")

        # Assert
        assert exists is False

    async def test_username_exists_true(self, db_session: AsyncSession):
        """Test checking if username exists when it does."""
        # Arrange
        repo = UserRepository(db_session)
        await repo.create(
            email="user@example.com",
            username="existinguser",
            hashed_password="hash"
        )
        await db_session.commit()

        # Act
        exists = await repo.username_exists("existinguser")

        # Assert
        assert exists is True

    async def test_username_exists_false(self, db_session: AsyncSession):
        """Test checking if username exists when it doesn't."""
        # Arrange
        repo = UserRepository(db_session)

        # Act
        exists = await repo.username_exists("nonexistentuser")

        # Assert
        assert exists is False

    async def test_inherits_base_repository_methods(self, db_session: AsyncSession):
        """Test that UserRepository inherits all base repository methods."""
        # Arrange
        repo = UserRepository(db_session)
        user = await repo.create(
            email="inherit@example.com",
            username="inherit",
            hashed_password="hash"
        )
        await db_session.commit()

        # Act - Test get_by_id from base
        found = await repo.get_by_id(user.id)
        assert found is not None
        assert found.email == "inherit@example.com"

        # Act - Test update from base
        updated = await repo.update(user, full_name="Updated Name")
        assert updated.full_name == "Updated Name"

        # Act - Test delete from base
        await repo.delete(user)
        await db_session.commit()
        deleted = await repo.get_by_id(user.id)
        assert deleted is None
