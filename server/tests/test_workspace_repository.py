"""Tests for WorkspaceRepository."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from database.models import Base, Project, Workspace
from repositories.workspace_repository import WorkspaceRepository


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session_local = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_local() as session:
        yield session


@pytest_asyncio.fixture
async def sample_project(db_session: AsyncSession):
    """Create a sample project for testing."""
    project = Project(
        project_unique_id="proj-001",
        worktree="/path/to/worktree",
        branch="main",
        name="Test Project",
        time_created=1000000,
        time_updated=1000000
    )
    db_session.add(project)
    await db_session.commit()
    return project


    
@pytest_asyncio.fixture
async def sample_project2(db_session: AsyncSession):
    """Create a second sample project for testing."""
    project = Project(
        project_unique_id="proj-002",
        worktree="/path/to/worktree2",
        branch="develop",
        name="Another Project",
        time_created=1000000,
        time_updated=1000000
    )
    db_session.add(project)
    await db_session.commit()
    return project


class TestWorkspaceRepositoryGetByProjectUniqueId:
    """Tests for get_by_project_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_project_unique_id(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test getting workspaces by project_unique_id."""
        repo = WorkspaceRepository(db_session)

        # Create workspaces
        ws1 = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="Workspace 1",
            branch="main"
        )
        ws2 = Workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-001",
            name="Workspace 2",
            branch="develop"
        )
        db_session.add_all([ws1, ws2])
        await db_session.commit()

        # Test
        workspaces = await repo.get_by_project_unique_id("proj-001")
        assert len(workspaces) == 2
        assert any(w.name == "Workspace 1" for w in workspaces)
        assert any(w.name == "Workspace 2" for w in workspaces)

    @pytest.mark.asyncio
    async def test_get_by_project_unique_id_empty(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test getting workspaces for project with no workspaces."""
        repo = WorkspaceRepository(db_session)

        workspaces = await repo.get_by_project_unique_id("proj-001")
        assert len(workspaces) == 0


class TestWorkspaceRepositoryGetByUniqueId:
    """Tests for get_by_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_unique_id(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test getting workspace by unique_id."""
        repo = WorkspaceRepository(db_session)

        workspace = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="Test Workspace",
            branch="main"
        )
        db_session.add(workspace)
        await db_session.commit()

        result = await repo.get_by_unique_id("ws-001")
        assert result is not None
        assert result.workspace_unique_id == "ws-001"
        assert result.name == "Test Workspace"

    @pytest.mark.asyncio
    async def test_get_by_unique_id_not_found(self, db_session: AsyncSession):
        """Test getting workspace by non-existent unique_id."""
        repo = WorkspaceRepository(db_session)

        result = await repo.get_by_unique_id("non-existent")
        assert result is None


class TestWorkspaceRepositoryGetByName:
    """Tests for get_by_name method."""

    @pytest.mark.asyncio
    async def test_get_by_name(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test searching workspaces by name."""
        repo = WorkspaceRepository(db_session)

        ws1 = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="Development Workspace",
            branch="main"
        )
        ws2 = Workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-001",
            name="Production Workspace",
            branch="main"
        )
        db_session.add_all([ws1, ws2])
        await db_session.commit()

        results = await repo.get_by_name("Development")
        assert len(results) == 1
        assert results[0].name == "Development Workspace"

    @pytest.mark.asyncio
    async def test_get_by_name_with_project_filter(
        self, db_session: AsyncSession, sample_project: Project, sample_project2: Project
    ):
        """Test searching workspaces by name with project filter."""
        repo = WorkspaceRepository(db_session)

        ws1 = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="Test Workspace",
            branch="main"
        )
        ws2 = Workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-002",
            name="Test Workspace 2",
            branch="main"
        )
        db_session.add_all([ws1, ws2])
        await db_session.commit()

        results = await repo.get_by_name("Test", project_unique_id="proj-001")
        assert len(results) == 1
        assert results[0].project_unique_id == "proj-001"

    @pytest.mark.asyncio
    async def test_get_by_name_case_insensitive(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test case-insensitive name search."""
        repo = WorkspaceRepository(db_session)

        workspace = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="Test Workspace",
            branch="main"
        )
        db_session.add(workspace)
        await db_session.commit()

        results = await repo.get_by_name("TEST")
        assert len(results) == 1
        assert results[0].name == "Test Workspace"


class TestWorkspaceRepositoryList:
    """Tests for list method."""

    @pytest.mark.asyncio
    async def test_list_basic(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test basic list with pagination."""
        repo = WorkspaceRepository(db_session)

        for i in range(5):
            ws = Workspace(
                workspace_unique_id=f"ws-{i:03d}",
                project_unique_id="proj-001",
                name=f"Workspace {i}",
                branch="main"
            )
            db_session.add(ws)
        await db_session.commit()

        results = await repo.list("proj-001", offset=0, limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_list_filters_by_project(
        self, db_session: AsyncSession, sample_project: Project, sample_project2: Project
    ):
        """Test list filters by project."""
        repo = WorkspaceRepository(db_session)

        ws1 = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="Workspace 1",
            branch="main"
        )
        ws2 = Workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-002",
            name="Workspace 2",
            branch="main"
        )
        db_session.add_all([ws1, ws2])
        await db_session.commit()

        results = await repo.list("proj-001")
        assert len(results) == 1
        assert results[0].project_unique_id == "proj-001"


class TestWorkspaceRepositoryCRUD:
    """Tests for basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_workspace(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test creating a workspace."""
        repo = WorkspaceRepository(db_session)

        workspace = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="New Workspace",
            branch="main"
        )
        created = await repo.create(workspace)
        await db_session.commit()

        assert created.id is not None
        assert created.workspace_unique_id == "ws-001"

    @pytest.mark.asyncio
    async def test_update_workspace(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test updating a workspace."""
        repo = WorkspaceRepository(db_session)

        workspace = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="Original Name",
            branch="main"
        )
        db_session.add(workspace)
        await db_session.commit()

        updated = await repo.update(workspace, name="Updated Name")
        await db_session.commit()

        assert updated.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_workspace(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test deleting a workspace."""
        repo = WorkspaceRepository(db_session)

        workspace = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="To Delete",
            branch="main"
        )
        db_session.add(workspace)
        await db_session.commit()

        await repo.delete(workspace)
        await db_session.commit()

        result = await repo.get_by_unique_id("ws-001")
        assert result is None


class TestWorkspaceRepositoryCount:
    """Tests for count operations."""

    @pytest.mark.asyncio
    async def test_count_workspaces(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test counting workspaces."""
        repo = WorkspaceRepository(db_session)

        for i in range(3):
            ws = Workspace(
                workspace_unique_id=f"ws-{i:03d}",
                project_unique_id="proj-001",
                name=f"Workspace {i}",
                branch="main"
            )
            db_session.add(ws)
        await db_session.commit()

        count = await repo.count()
        assert count == 3


class TestWorkspaceRepositoryExists:
    """Tests for exists operations."""

    @pytest.mark.asyncio
    async def test_exists(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test checking if workspace exists."""
        repo = WorkspaceRepository(db_session)

        workspace = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            name="Test Workspace",
            branch="main"
        )
        db_session.add(workspace)
        await db_session.commit()

        exists = await repo.exists(workspace.id)
        assert exists is True
