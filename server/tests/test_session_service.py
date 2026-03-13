"""Tests for SessionService."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services import UserService, SessionService


@pytest_asyncio.fixture
async def session_service_user(db_session: AsyncSession):
    """Create a test user for session tests."""
    user_service = UserService(db_session)
    user = await user_service.create_user(
        email="session_test@example.com",
        username="sessionuser",
        password="password123"
    )
    return user


class TestSessionServiceCreate:
    """Tests for SessionService.create_session method."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, db_session: AsyncSession, session_service_user):
        """Test creating a session successfully."""
        service = SessionService(db_session)
        
        session = await service.create_session(
            user_id=session_service_user.id,
            expires_in_hours=24
        )
        
        assert session.id is not None
        assert session.user_id == session_service_user.id
        assert session.token is not None
        assert len(session.token) > 0

    @pytest.mark.asyncio
    async def test_create_session_with_metadata(self, db_session: AsyncSession, session_service_user):
        """Test creating a session with IP and user agent."""
        service = SessionService(db_session)
        
        session = await service.create_session(
            user_id=session_service_user.id,
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )
        
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "Test Agent"

    @pytest.mark.asyncio
    async def test_create_session_custom_expiry(self, db_session: AsyncSession, session_service_user):
        """Test creating a session with custom expiry."""
        service = SessionService(db_session)
        
        session = await service.create_session(
            user_id=session_service_user.id,
            expires_in_hours=48
        )
        
        assert session.expires_at is not None


class TestSessionServiceValidate:
    """Tests for SessionService.validate_session method."""

    @pytest.mark.asyncio
    async def test_validate_session_valid(self, db_session: AsyncSession, session_service_user):
        """Test validating a valid session."""
        service = SessionService(db_session)
        
        created = await service.create_session(user_id=session_service_user.id)
        
        validated = await service.validate_session(created.token)
        
        assert validated is not None
        assert validated.id == created.id

    @pytest.mark.asyncio
    async def test_validate_session_invalid_token(self, db_session: AsyncSession):
        """Test validating with invalid token returns None."""
        service = SessionService(db_session)
        
        validated = await service.validate_session("invalid_token")
        
        assert validated is None


class TestSessionServiceEnd:
    """Tests for SessionService.end_session method."""

    @pytest.mark.asyncio
    async def test_end_session_success(self, db_session: AsyncSession, session_service_user):
        """Test ending a session successfully."""
        service = SessionService(db_session)
        
        created = await service.create_session(user_id=session_service_user.id)
        
        result = await service.end_session(created.token)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_end_session_not_found(self, db_session: AsyncSession):
        """Test ending non-existent session returns False."""
        service = SessionService(db_session)
        
        result = await service.end_session("nonexistent_token")
        
        assert result is False


class TestSessionServiceCleanup:
    """Tests for SessionService.cleanup_expired_sessions method."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, db_session: AsyncSession, session_service_user):
        """Test cleaning up expired sessions."""
        service = SessionService(db_session)
        
        # Create an expired session directly via repo
        from database.models import Session
        from repositories.session_repository import SessionRepository
        
        repo = SessionRepository(db_session)
        expired_session = await repo.create(
            user_id=session_service_user.id,
            token="expired_token_123",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        await db_session.commit()
        
        count = await service.cleanup_expired_sessions()
        
        assert count >= 1
