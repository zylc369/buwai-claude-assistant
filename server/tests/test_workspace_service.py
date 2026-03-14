"""Tests for WorkspaceService."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database.models import Base, Project, Workspace, Session
from services.workspace_service import WorkspaceService


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
    project = Project(
        project_unique_id="proj-001",
        directory="/path/to/worktree",
        branch="main",
        name="Test Project",
        gmt_create=1000000,
        gmt_modified=1000000
    )
    db_session.add(project)
    await db_session.commit()
    return project


@pytest_asyncio.fixture
async def sample_project2(db_session: AsyncSession):
    """Create a second sample project for testing."""
    project = Project(
        project_unique_id="proj-002",
        directory="/path/to/worktree2",
        branch="develop",
        name="Another Project",
        gmt_create=1000000,
        gmt_modified=1000000
    )
    db_session.add(project)
    await db_session.commit()
    return project


class TestWorkspaceServiceCreate:
    """Tests for create_workspace method."""

    @pytest.mark.asyncio
    async def test_create_workspace_minimal(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test creating a workspace with minimal required fields."""
        service = WorkspaceService(db_session)

        workspace = await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="/test/workspace"
        )

        assert workspace.id is not None
        assert workspace.workspace_unique_id == "ws-001"
        assert workspace.project_unique_id == "proj-001"

    @pytest.mark.asyncio
    async def test_create_workspace_with_all_fields(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test creating a workspace with all fields."""
        service = WorkspaceService(db_session)

        workspace = await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            branch="feature/test",
            directory="/path/to/workspace",
            extra='{"key": "value"}'
        )

        assert workspace.id is not None
        assert workspace.workspace_unique_id == "ws-001"
        assert workspace.branch == "feature/test"
        assert workspace.directory == "/path/to/workspace"
        assert workspace.extra == '{"key": "value"}'


class TestWorkspaceServiceGetById:
    """Tests for get_workspace_by_id method."""

    @pytest.mark.asyncio
    async def test_get_workspace_by_id(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test getting a workspace by ID."""
        service = WorkspaceService(db_session)

        created = await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="/test/workspace"
        )

        found = await service.get_workspace_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.workspace_unique_id == "ws-001"

    @pytest.mark.asyncio
    async def test_get_workspace_by_id_not_found(self, db_session: AsyncSession):
        """Test getting a workspace by non-existent ID."""
        service = WorkspaceService(db_session)

        found = await service.get_workspace_by_id(999)

        assert found is None


class TestWorkspaceServiceGetByUniqueId:
    """Tests for get_workspace_by_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_workspace_by_unique_id(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test getting a workspace by unique_id."""
        service = WorkspaceService(db_session)

        await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace"
        )

        found = await service.get_workspace_by_unique_id("ws-001")

        assert found is not None
        assert found.workspace_unique_id == "ws-001"

    @pytest.mark.asyncio
    async def test_get_workspace_by_unique_id_not_found(
        self, db_session: AsyncSession
    ):
        """Test getting a workspace by non-existent unique_id."""
        service = WorkspaceService(db_session)

        found = await service.get_workspace_by_unique_id("non-existent")

        assert found is None


class TestWorkspaceServiceList:
    """Tests for list_workspaces method."""

    @pytest.mark.asyncio
    async def test_list_workspaces(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test listing workspaces for a project."""
        service = WorkspaceService(db_session)

        await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="/test/workspace1"
        )
        await service.create_workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-001",
            directory="workspace2"
        )

        workspaces = await service.list_workspaces("proj-001")

        assert len(workspaces) == 2

    @pytest.mark.asyncio
    async def test_list_workspaces_empty(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test listing workspaces when project has none."""
        service = WorkspaceService(db_session)

        workspaces = await service.list_workspaces("proj-001")

        assert len(workspaces) == 0

    @pytest.mark.asyncio
    async def test_list_workspaces_filters_by_project(
        self,
        db_session: AsyncSession,
        sample_project: Project,
        sample_project2: Project
    ):
        """Test that list filters by project."""
        service = WorkspaceService(db_session)

        await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="/test/workspace1"
        )
        await service.create_workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-002",
            directory="workspace2"
        )

        workspaces = await service.list_workspaces("proj-001")

        assert len(workspaces) == 1
        assert workspaces[0].project_unique_id == "proj-001"

    @pytest.mark.asyncio
    async def test_list_workspaces_pagination(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test list pagination."""
        service = WorkspaceService(db_session)

        for i in range(5):
            await service.create_workspace(
                workspace_unique_id=f"ws-{i:03d}",
                project_unique_id="proj-001",
                directory=f"workspace{i}"
            )

        page1 = await service.list_workspaces("proj-001", offset=0, limit=2)
        page2 = await service.list_workspaces("proj-001", offset=2, limit=2)
        page3 = await service.list_workspaces("proj-001", offset=4, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1


class TestWorkspaceServiceUpdate:
    """Tests for update_workspace method."""

    @pytest.mark.asyncio
    async def test_update_workspace(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test updating a workspace."""
        service = WorkspaceService(db_session)

        created = await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace"
        )

        updated = await service.update_workspace(
            created.id,
            branch="new-branch"
        )

        assert updated is not None
        assert updated.branch == "new-branch"

    @pytest.mark.asyncio
    async def test_update_workspace_not_found(self, db_session: AsyncSession):
        """Test updating a non-existent workspace."""
        service = WorkspaceService(db_session)

        updated = await service.update_workspace(999, name="New Name")

        assert updated is None


class TestWorkspaceServiceDelete:
    """Tests for delete_workspace method."""

    @pytest.mark.asyncio
    async def test_delete_workspace(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test deleting a workspace."""
        service = WorkspaceService(db_session)

        created = await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="/test/workspace"
        )

        result = await service.delete_workspace(created.id)

        assert result is True

        found = await service.get_workspace_by_id(created.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_workspace_not_found(self, db_session: AsyncSession):
        """Test deleting a non-existent workspace."""
        service = WorkspaceService(db_session)

        result = await service.delete_workspace(999)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_workspace_cascades_sessions(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test that deleting workspace cascades to sessions."""
        service = WorkspaceService(db_session)

        workspace = await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace"
        )

        session = Session(
            session_unique_id="sess-001",
            external_session_id="external-sess-001",
            project_unique_id="proj-001",
            workspace_unique_id="ws-001",
            directory="test-workspace",
            title="Test Session",
            gmt_create=1000000,
            gmt_modified=1000000
        )
        db_session.add(session)
        await db_session.commit()

        await service.delete_workspace(workspace.id)

        from sqlalchemy import select
        stmt = select(Session).where(Session.session_unique_id == "sess-001")
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None


class TestWorkspaceServiceSearch:
    """Tests for search_workspaces method."""

    @pytest.mark.asyncio
    async def test_search_workspaces_by_name(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test searching workspaces by name."""
        service = WorkspaceService(db_session)

        await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="workspace1"
        )
        await service.create_workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-001",
            directory="workspace2"
        )

        results = await service.search_workspaces("workspace1")

        assert len(results) == 1
        assert results[0].directory == "workspace1"

    @pytest.mark.asyncio
    async def test_search_workspaces_case_insensitive(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test case-insensitive search."""
        service = WorkspaceService(db_session)

        await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace"
        )

        results = await service.search_workspaces("WORKSPACE")

        assert len(results) == 1
        assert results[0].directory == "test-workspace"

    @pytest.mark.asyncio
    async def test_search_workspaces_with_project_filter(
        self,
        db_session: AsyncSession,
        sample_project: Project,
        sample_project2: Project
    ):
        """Test search with project filter."""
        service = WorkspaceService(db_session)

        await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="workspace1"
        )
        await service.create_workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-002",
            directory="workspace2"
        )

        results = await service.search_workspaces("workspace1", project_unique_id="proj-001")

        assert len(results) == 1
        assert results[0].project_unique_id == "proj-001"

    @pytest.mark.asyncio
    async def test_search_workspaces_partial_match(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test partial name matching."""
        service = WorkspaceService(db_session)

        await service.create_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace"
        )

        results = await service.search_workspaces("work")

        assert len(results) == 1
        assert results[0].directory == "test-workspace"
