"""Tests for ConversationSessionService."""

import os
import shutil
import pytest
import pytest_asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config import get_config
from database.models import Base, Project, Workspace, Session
from services.conversation_session_service import ConversationSessionService

PROJECTS_ROOT = get_config().projects.root


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def sample_project(db_session: AsyncSession):
    """Create a sample project for testing."""
    project_dir = Path(PROJECTS_ROOT) / "session-test-project"
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    
    project = Project(
        project_unique_id="proj-session-001",
        directory="session-test-project",
        branch="main",
        name="Test Project for Sessions",
        gmt_create=1000000,
        gmt_modified=1000000,
        test=True
    )
    db_session.add(project)
    await db_session.commit()
    yield project
    if project_dir.exists():
        shutil.rmtree(project_dir)


@pytest_asyncio.fixture
async def sample_workspace(db_session: AsyncSession, sample_project: Project):
    """Create a sample workspace for testing."""
    workspace = Workspace(
        workspace_unique_id="ws-session-001",
        project_unique_id="proj-session-001",
        directory="session-test-workspace",
        branch="main",
        gmt_create=1000000,
        gmt_modified=1000000,
        test=True
    )
    db_session.add(workspace)
    await db_session.commit()
    return workspace


class TestValidateExternalSessionId:
    """Tests for validate_new_session_external_id method."""

    @pytest.mark.asyncio
    async def test_validate_external_id_unique(
        self, db_session: AsyncSession, sample_project: Project, sample_workspace: Workspace
    ):
        """Test validation passes when external_session_id doesn't exist."""
        service = ConversationSessionService(db_session)

        # external_id that doesn't exist yet
        await service.validate_new_session_external_id(
            "external-id-new", test=True
        )

        # Should not raise any exception - implicitly passes

    @pytest.mark.asyncio
    async def test_validate_external_id_duplicate(
        self, db_session: AsyncSession, sample_project: Project, sample_workspace: Workspace
    ):
        """Test validation raises ValueError when external_session_id already exists."""
        service = ConversationSessionService(db_session)

        # Create a session with an external_session_id
        await service.create_session(
            session_unique_id="sess-001",
            external_session_id="external-id-existing",
            project_unique_id="proj-session-001",
            workspace_unique_id="ws-session-001",
            directory="test-dir",
            title="Test Session",
            test=True
        )

        # Try to validate the same external_session_id - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await service.validate_new_session_external_id(
                "external-id-existing", test=True
            )

        assert "external_session_id 'external-id-existing' already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_external_id_with_test_flag(
        self, db_session: AsyncSession, sample_project: Project, sample_workspace: Workspace
    ):
        """Test validation works correctly with test=True flag for isolation."""
        service = ConversationSessionService(db_session)

        # Create a session with test=True
        await service.create_session(
            session_unique_id="sess-test-001",
            external_session_id="external-id-test-only",
            project_unique_id="proj-session-001",
            workspace_unique_id="ws-session-001",
            directory="test-dir",
            title="Test Session",
            test=True
        )

        # Validation with test=True should find the duplicate and raise
        with pytest.raises(ValueError) as exc_info:
            await service.validate_new_session_external_id(
                "external-id-test-only", test=True
            )

        assert "external_session_id 'external-id-test-only' already exists" in str(exc_info.value)

        # Validation with test=False should NOT find the test session
        # (because test data is isolated)
        await service.validate_new_session_external_id(
            "external-id-test-only", test=False
        )
        # Should not raise - implicitly passes


class TestConversationSessionServiceCreate:
    """Tests for create_session method."""

    @pytest.mark.asyncio
    async def test_create_session(
        self, db_session: AsyncSession, sample_project: Project, sample_workspace: Workspace
    ):
        """Test creating a session."""
        service = ConversationSessionService(db_session)

        session = await service.create_session(
            session_unique_id="sess-001",
            external_session_id="external-sess-001",
            project_unique_id="proj-session-001",
            workspace_unique_id="ws-session-001",
            directory="test-dir",
            title="Test Session",
            test=True
        )

        assert session.id is not None
        assert session.session_unique_id == "sess-001"
        assert session.external_session_id == "external-sess-001"
        assert session.project_unique_id == "proj-session-001"


class TestConversationSessionServiceGetByUniqueId:
    """Tests for get_by_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_unique_id(
        self, db_session: AsyncSession, sample_project: Project, sample_workspace: Workspace
    ):
        """Test getting a session by unique_id."""
        service = ConversationSessionService(db_session)

        await service.create_session(
            session_unique_id="sess-001",
            external_session_id="external-sess-001",
            project_unique_id="proj-session-001",
            workspace_unique_id="ws-session-001",
            directory="test-dir",
            title="Test Session",
            test=True
        )

        found = await service.get_by_unique_id("sess-001", test=True)

        assert found is not None
        assert found.session_unique_id == "sess-001"

    @pytest.mark.asyncio
    async def test_get_by_unique_id_not_found(self, db_session: AsyncSession):
        """Test getting a session by non-existent unique_id."""
        service = ConversationSessionService(db_session)

        found = await service.get_by_unique_id("non-existent", test=True)

        assert found is None


class TestConversationSessionServiceGetByExternalId:
    """Tests for get_session_by_external_id method."""

    @pytest.mark.asyncio
    async def test_get_session_by_external_id(
        self, db_session: AsyncSession, sample_project: Project, sample_workspace: Workspace
    ):
        """Test getting a session by external_session_id."""
        service = ConversationSessionService(db_session)

        await service.create_session(
            session_unique_id="sess-001",
            external_session_id="external-sess-001",
            project_unique_id="proj-session-001",
            workspace_unique_id="ws-session-001",
            directory="test-dir",
            title="Test Session",
            test=True
        )

        found = await service.get_session_by_external_id("external-sess-001", test=True)

        assert found is not None
        assert found.external_session_id == "external-sess-001"

    @pytest.mark.asyncio
    async def test_get_session_by_external_id_not_found(self, db_session: AsyncSession):
        """Test getting a session by non-existent external_session_id."""
        service = ConversationSessionService(db_session)

        found = await service.get_session_by_external_id("non-existent", test=True)

        assert found is None


class TestConversationSessionServiceDelete:
    """Tests for delete_session method."""

    @pytest.mark.asyncio
    async def test_delete_session(
        self, db_session: AsyncSession, sample_project: Project, sample_workspace: Workspace
    ):
        """Test deleting a session."""
        service = ConversationSessionService(db_session)

        await service.create_session(
            session_unique_id="sess-001",
            external_session_id="external-sess-001",
            project_unique_id="proj-session-001",
            workspace_unique_id="ws-session-001",
            directory="test-dir",
            title="Test Session",
            test=True
        )

        result = await service.delete_session("sess-001", test=True)

        assert result is True

        found = await service.get_by_unique_id("sess-001", test=True)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, db_session: AsyncSession):
        """Test deleting a non-existent session."""
        service = ConversationSessionService(db_session)

        result = await service.delete_session("non-existent", test=True)

        assert result is False
