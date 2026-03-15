"""Tests for WorkspaceRepository."""

import time

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from database.models import Base, Project, Workspace
from repositories.workspace_repository import WorkspaceRepository


def create_test_workspace(**kwargs):
    """Create a Workspace with required timestamp fields."""
    current_time = int(time.time() * 1000)
    defaults = {
        'gmt_create': current_time,
        'gmt_modified': current_time,
        'latest_active_time': current_time,
        'directory': 'test-workspace',
        'test': True,
    }
    defaults.update(kwargs)
    return Workspace(**defaults)


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
        directory="worktree",
        branch="main",
        name="Test Project",
        gmt_create=1000000,
        gmt_modified=1000000,
        test=True
    )
    db_session.add(project)
    await db_session.commit()
    return project


    
@pytest_asyncio.fixture
async def sample_project2(db_session: AsyncSession):
    """Create a second sample project for testing."""
    project = Project(
        project_unique_id="proj-002",
        directory="worktree2",
        branch="develop",
        name="Another Project",
        gmt_create=1000000,
        gmt_modified=1000000,
        test=True
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
        ws1 = create_test_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="workspace1",
            branch="main"
        )
        ws2 = create_test_workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-001",
            directory="workspace2",
            branch="develop"
        )
        db_session.add_all([ws1, ws2])
        await db_session.commit()

        # Test
        workspaces = await repo.get_by_project_unique_id("proj-001", test=True)
        assert len(workspaces) == 2
        assert any(w.directory == "workspace1" for w in workspaces)
        assert any(w.directory == "workspace2" for w in workspaces)

    @pytest.mark.asyncio
    async def test_get_by_project_unique_id_empty(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test getting workspaces for project with no workspaces."""
        repo = WorkspaceRepository(db_session)

        workspaces = await repo.get_by_project_unique_id("proj-001", test=True)
        assert len(workspaces) == 0


class TestWorkspaceRepositoryGetByUniqueId:
    """Tests for get_by_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_unique_id(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test getting workspace by unique_id."""
        repo = WorkspaceRepository(db_session)

        workspace = create_test_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace",
            branch="main"
        )
        db_session.add(workspace)
        await db_session.commit()

        result = await repo.get_by_unique_id("ws-001", test=True)
        assert result is not None
        assert result.workspace_unique_id == "ws-001"
        assert result.directory == "test-workspace"

    @pytest.mark.asyncio
    async def test_get_by_unique_id_not_found(self, db_session: AsyncSession):
        """Test getting workspace by non-existent unique_id."""
        repo = WorkspaceRepository(db_session)

        result = await repo.get_by_unique_id("non-existent", test=True)
        assert result is None


class TestWorkspaceRepositoryList:
    """Tests for list method."""

    @pytest.mark.asyncio
    async def test_list_basic(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test basic list with pagination."""
        repo = WorkspaceRepository(db_session)

        for i in range(5):
            ws = create_test_workspace(
                workspace_unique_id=f"ws-{i:03d}",
                project_unique_id="proj-001",
                directory=f"workspace{i}",
                branch="main"
            )
            db_session.add(ws)
        await db_session.commit()

        results = await repo.list("proj-001", offset=0, limit=3, test=True)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_list_filters_by_project(
        self, db_session: AsyncSession, sample_project: Project, sample_project2: Project
    ):
        """Test list filters by project."""
        repo = WorkspaceRepository(db_session)

        ws1 = create_test_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="workspace1",
            branch="main"
        )
        ws2 = create_test_workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-002",
            directory="workspace2",
            branch="main"
        )
        db_session.add_all([ws1, ws2])
        await db_session.commit()

        results = await repo.list("proj-001", test=True)
        assert len(results) == 1
        assert results[0].project_unique_id == "proj-001"


class TestWorkspaceRepositoryCRUD:

    @pytest.mark.asyncio
    async def test_create_workspace(
        self, db_session: AsyncSession, sample_project: Project
    ):
        repo = WorkspaceRepository(db_session)

        current_time = int(time.time() * 1000)
        created = await repo.create(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace",
            branch="main",
            gmt_create=current_time,
            gmt_modified=current_time,
            latest_active_time=current_time,
            test=True
        )
        await db_session.commit()

        assert created.id is not None
        assert created.workspace_unique_id == "ws-001"

    @pytest.mark.asyncio
    async def test_update_workspace(
        self, db_session: AsyncSession, sample_project: Project
    ):
        repo = WorkspaceRepository(db_session)

        workspace = create_test_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace",
            branch="main"
        )
        db_session.add(workspace)
        await db_session.commit()

        updated = await repo.update(workspace, branch="updated-branch", test=True)
        await db_session.commit()

        assert updated.branch == "updated-branch"

    @pytest.mark.asyncio
    async def test_delete_workspace(
        self, db_session: AsyncSession, sample_project: Project
    ):
        repo = WorkspaceRepository(db_session)

        workspace = create_test_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace",
            branch="main"
        )
        db_session.add(workspace)
        await db_session.commit()

        await repo.delete(workspace)
        await db_session.commit()

        result = await repo.get_by_unique_id("ws-001", test=True)
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
            ws = create_test_workspace(
                workspace_unique_id=f"ws-{i:03d}",
                project_unique_id="proj-001",
                directory=f"workspace{i}",
                branch="main"
            )
            db_session.add(ws)
        await db_session.commit()

        count = await repo.count(test=True)
        assert count == 3


class TestWorkspaceRepositoryExists:
    """Tests for exists operations."""

    @pytest.mark.asyncio
    async def test_exists(
        self, db_session: AsyncSession, sample_project: Project
    ):
        """Test checking if workspace exists."""
        repo = WorkspaceRepository(db_session)

        workspace = create_test_workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-001",
            directory="test-workspace",
            branch="main"
        )
        db_session.add(workspace)
        await db_session.commit()

        exists = await repo.exists(workspace.id, test=True)
        assert exists is True
