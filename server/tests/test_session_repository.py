"""Tests for SessionRepository."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Session
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository


@pytest.mark.asyncio
class TestSessionRepository:
    """Test suite for SessionRepository."""

    async def _create_test_user(self, db_session: AsyncSession) -> User:
        """Helper to create a test user."""
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed123"
        )
        await db_session.commit()
        return user

    async def test_get_by_token_existing_session(self, db_session: AsyncSession):
        """Test retrieving a session by token when it exists."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = SessionRepository(db_session)
        session = await repo.create(
            user_id=user.id,
            token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        await db_session.commit()

        # Act
        found_session = await repo.get_by_token("test_token_123")

        # Assert
        assert found_session is not None
        assert found_session.token == "test_token_123"
        assert found_session.user_id == user.id
        assert found_session.id == session.id

    async def test_get_by_token_nonexistent_session(self, db_session: AsyncSession):
        """Test retrieving a session by token when it doesn't exist."""
        # Arrange
        repo = SessionRepository(db_session)

        # Act
        found_session = await repo.get_by_token("nonexistent_token")

        # Assert
        assert found_session is None

    async def test_get_valid_sessions_for_user(self, db_session: AsyncSession):
        """Test retrieving only valid (non-expired) sessions for a user."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = SessionRepository(db_session)
        
        # Create valid session
        await repo.create(
            user_id=user.id,
            token="valid_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Create expired session
        await repo.create(
            user_id=user.id,
            token="expired_token",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        await db_session.commit()

        # Act
        valid_sessions = await repo.get_valid_sessions_for_user(user.id)

        # Assert
        assert len(valid_sessions) == 1
        assert valid_sessions[0].token == "valid_token"

    async def test_get_valid_sessions_excludes_expired(self, db_session: AsyncSession):
        """Test that expired sessions are excluded from valid sessions."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = SessionRepository(db_session)
        
        # Create multiple expired sessions
        for i in range(3):
            await repo.create(
                user_id=user.id,
                token=f"expired_{i}",
                expires_at=datetime.utcnow() - timedelta(hours=i+1)
            )
        
        await db_session.commit()

        # Act
        valid_sessions = await repo.get_valid_sessions_for_user(user.id)

        # Assert
        assert len(valid_sessions) == 0

    async def test_delete_expired_sessions(self, db_session: AsyncSession):
        """Test deleting all expired sessions."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = SessionRepository(db_session)
        
        # Create expired sessions
        await repo.create(
            user_id=user.id,
            token="expired1",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        await repo.create(
            user_id=user.id,
            token="expired2",
            expires_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        # Create valid session
        await repo.create(
            user_id=user.id,
            token="valid",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        await db_session.commit()

        # Act
        deleted_count = await repo.delete_expired_sessions()
        await db_session.commit()

        # Assert
        assert deleted_count == 2
        
        # Verify only valid session remains
        all_sessions = await repo.get_all(user_id=user.id)
        assert len(all_sessions) == 1
        assert all_sessions[0].token == "valid"

    async def test_is_valid_token_true(self, db_session: AsyncSession):
        """Test checking if a token is valid when it's not expired."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = SessionRepository(db_session)
        await repo.create(
            user_id=user.id,
            token="valid_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        await db_session.commit()

        # Act
        is_valid = await repo.is_valid_token("valid_token")

        # Assert
        assert is_valid is True

    async def test_is_valid_token_false_expired(self, db_session: AsyncSession):
        """Test checking if a token is valid when it's expired."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = SessionRepository(db_session)
        await repo.create(
            user_id=user.id,
            token="expired_token",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        await db_session.commit()

        # Act
        is_valid = await repo.is_valid_token("expired_token")

        # Assert
        assert is_valid is False

    async def test_is_valid_token_false_nonexistent(self, db_session: AsyncSession):
        """Test checking if a token is valid when it doesn't exist."""
        # Arrange
        repo = SessionRepository(db_session)

        # Act
        is_valid = await repo.is_valid_token("nonexistent_token")

        # Assert
        assert is_valid is False

    async def test_delete_sessions_for_user(self, db_session: AsyncSession):
        """Test deleting all sessions for a specific user."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = SessionRepository(db_session)
        
        # Create multiple sessions
        for i in range(3):
            await repo.create(
                user_id=user.id,
                token=f"token_{i}",
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
        
        await db_session.commit()

        # Act
        deleted_count = await repo.delete_sessions_for_user(user.id)
        await db_session.commit()

        # Assert
        assert deleted_count == 3
        
        # Verify sessions are deleted
        remaining = await repo.get_all(user_id=user.id)
        assert len(remaining) == 0

    async def test_inherits_base_repository_methods(self, db_session: AsyncSession):
        """Test that SessionRepository inherits all base repository methods."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = SessionRepository(db_session)
        session = await repo.create(
            user_id=user.id,
            token="inherit_test",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        await db_session.commit()

        # Act - Test get_by_id from base
        found = await repo.get_by_id(session.id)
        assert found is not None
        assert found.token == "inherit_test"

        # Act - Test update from base
        updated = await repo.update(session, ip_address="192.168.1.1")
        assert updated.ip_address == "192.168.1.1"

        # Act - Test delete from base
        await repo.delete(session)
        await db_session.commit()
        deleted = await repo.get_by_id(session.id)
        assert deleted is None
