"""Tests for ProjectRepository."""

import pytest
import time
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project, Workspace, Session, Message
from repositories.project_repository import ProjectRepository


# Helper function to create test projects
async def create_test_project(
    repo: ProjectRepository,
    project_unique_id: str,
    worktree: str,
    name: str = None,
    branch: str = None,
) -> Project:
    """Create a test project."""
    current_time = int(time.time())
    return await repo.create(
        project_unique_id=project_unique_id,
        worktree=worktree,
        name=name,
        branch=branch,
        time_initialized=current_time,
        time_created=current_time,
        time_updated=current_time,
    )


class TestProjectRepositoryCreate:
    """Tests for ProjectRepository.create method."""

    @pytest.mark.asyncio
    async def test_create_project(self, db_session: AsyncSession):
        """Test creating a project."""
        repo = ProjectRepository(db_session)
        
        project = await create_test_project(
            repo,
            project_unique_id="proj-001",
            worktree="/path/to/worktree",
            name="Test Project",
            branch="main",
        )
        await db_session.commit()
        
        assert project.id is not None
        assert project.project_unique_id == "proj-001"
        assert project.worktree == "/path/to/worktree"
        assert project.name == "Test Project"
        assert project.branch == "main"

    @pytest.mark.asyncio
    async def test_create_project_with_nullable_fields(self, db_session: AsyncSession):
        """Test creating a project with nullable fields as None."""
        repo = ProjectRepository(db_session)
        
        project = await create_test_project(
            repo,
            project_unique_id="proj-002",
            worktree="/path/to/worktree2",
            name=None,
            branch=None,
        )
        await db_session.commit()
        
        assert project.id is not None
        assert project.name is None
        assert project.branch is None


class TestProjectRepositoryGetById:
    """Tests for ProjectRepository.get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, db_session: AsyncSession):
        """Test getting an existing project by ID."""
        repo = ProjectRepository(db_session)
        
        project = await create_test_project(
            repo,
            project_unique_id="proj-003",
            worktree="/path/to/worktree3",
            name="Find By ID",
        )
        await db_session.commit()
        
        result = await repo.get_by_id(project.id)
        
        assert result is not None
        assert result.id == project.id
        assert result.project_unique_id == "proj-003"
        assert result.name == "Find By ID"

    @pytest.mark.asyncio
    async def test_get_by_id_not_exists(self, db_session: AsyncSession):
        """Test getting a non-existent project by ID."""
        repo = ProjectRepository(db_session)
        
        result = await repo.get_by_id(99999)
        
        assert result is None


class TestProjectRepositoryGetByUniqueId:
    """Tests for ProjectRepository.get_by_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_unique_id_exists(self, db_session: AsyncSession):
        """Test getting an existing project by unique ID."""
        repo = ProjectRepository(db_session)
        
        project = await create_test_project(
            repo,
            project_unique_id="unique-proj-001",
            worktree="/path/to/worktree",
            name="Unique Project",
        )
        await db_session.commit()
        
        result = await repo.get_by_unique_id("unique-proj-001")
        
        assert result is not None
        assert result.project_unique_id == "unique-proj-001"
        assert result.name == "Unique Project"

    @pytest.mark.asyncio
    async def test_get_by_unique_id_not_exists(self, db_session: AsyncSession):
        """Test getting a non-existent project by unique ID."""
        repo = ProjectRepository(db_session)
        
        result = await repo.get_by_unique_id("non-existent-unique-id")
        
        assert result is None


class TestProjectRepositoryGetByName:
    """Tests for ProjectRepository.get_by_name method."""

    @pytest.mark.asyncio
    async def test_get_by_name_exact_match(self, db_session: AsyncSession):
        """Test getting projects by exact name match."""
        repo = ProjectRepository(db_session)
        
        await create_test_project(
            repo,
            project_unique_id="proj-exact-001",
            worktree="/path/to/worktree1",
            name="Exact Match Project",
        )
        await create_test_project(
            repo,
            project_unique_id="proj-exact-002",
            worktree="/path/to/worktree2",
            name="Different Project",
        )
        await db_session.commit()
        
        results = await repo.get_by_name("Exact Match Project", exact=True)
        
        assert len(results) == 1
        assert results[0].name == "Exact Match Project"

    @pytest.mark.asyncio
    async def test_get_by_name_fuzzy_match(self, db_session: AsyncSession):
        """Test getting projects by fuzzy name match."""
        repo = ProjectRepository(db_session)
        
        await create_test_project(
            repo,
            project_unique_id="proj-fuzzy-001",
            worktree="/path/to/worktree1",
            name="My Awesome Project",
        )
        await create_test_project(
            repo,
            project_unique_id="proj-fuzzy-002",
            worktree="/path/to/worktree2",
            name="Another Awesome App",
        )
        await create_test_project(
            repo,
            project_unique_id="proj-fuzzy-003",
            worktree="/path/to/worktree3",
            name="Different Thing",
        )
        await db_session.commit()
        
        results = await repo.get_by_name("awesome", exact=False)
        
        assert len(results) == 2
        names = [p.name for p in results]
        assert "My Awesome Project" in names
        assert "Another Awesome App" in names
        assert "Different Thing" not in names

    @pytest.mark.asyncio
    async def test_get_by_name_case_insensitive(self, db_session: AsyncSession):
        """Test that fuzzy name match is case-insensitive."""
        repo = ProjectRepository(db_session)
        
        await create_test_project(
            repo,
            project_unique_id="proj-case-001",
            worktree="/path/to/worktree",
            name="MyProject",
        )
        await db_session.commit()
        
        # Test lowercase search
        results = await repo.get_by_name("myproject", exact=False)
        assert len(results) == 1
        
        # Test uppercase search
        results = await repo.get_by_name("MYPROJECT", exact=False)
        assert len(results) == 1
        
        # Test mixed case search
        results = await repo.get_by_name("MyPrOjEcT", exact=False)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_name_no_match(self, db_session: AsyncSession):
        """Test getting projects by name with no match."""
        repo = ProjectRepository(db_session)
        
        await create_test_project(
            repo,
            project_unique_id="proj-nomatch-001",
            worktree="/path/to/worktree",
            name="Some Project",
        )
        await db_session.commit()
        
        results = await repo.get_by_name("nonexistent", exact=False)
        
        assert len(results) == 0


class TestProjectRepositoryList:
    """Tests for ProjectRepository.list method."""

    @pytest.mark.asyncio
    async def test_list_all_projects(self, db_session: AsyncSession):
        """Test listing all projects."""
        repo = ProjectRepository(db_session)
        
        for i in range(5):
            await create_test_project(
                repo,
                project_unique_id=f"proj-list-{i:03d}",
                worktree=f"/path/to/worktree{i}",
                name=f"Project {i}",
            )
        await db_session.commit()
        
        results = await repo.list()
        
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, db_session: AsyncSession):
        """Test listing projects with pagination."""
        repo = ProjectRepository(db_session)
        
        for i in range(10):
            await create_test_project(
                repo,
                project_unique_id=f"proj-page-{i:03d}",
                worktree=f"/path/to/worktree{i}",
                name=f"Project {i}",
            )
        await db_session.commit()
        
        # Get first page
        page1 = await repo.list(offset=0, limit=3)
        assert len(page1) == 3
        
        # Get second page
        page2 = await repo.list(offset=3, limit=3)
        assert len(page2) == 3
        
        # Get last page
        last_page = await repo.list(offset=9, limit=3)
        assert len(last_page) == 1

    @pytest.mark.asyncio
    async def test_list_with_name_filter(self, db_session: AsyncSession):
        """Test listing projects with name filter."""
        repo = ProjectRepository(db_session)
        
        await create_test_project(
            repo,
            project_unique_id="proj-filter-001",
            worktree="/path/to/worktree1",
            name="Alpha Project",
        )
        await create_test_project(
            repo,
            project_unique_id="proj-filter-002",
            worktree="/path/to/worktree2",
            name="Beta Project",
        )
        await create_test_project(
            repo,
            project_unique_id="proj-filter-003",
            worktree="/path/to/worktree3",
            name="Alpha App",
        )
        await db_session.commit()
        
        results = await repo.list(name="alpha")
        
        assert len(results) == 2
        names = [p.name for p in results]
        assert "Alpha Project" in names
        assert "Alpha App" in names
        assert "Beta Project" not in names

    @pytest.mark.asyncio
    async def test_list_with_pagination_and_filter(self, db_session: AsyncSession):
        """Test listing projects with both pagination and name filter."""
        repo = ProjectRepository(db_session)
        
        for i in range(10):
            await create_test_project(
                repo,
                project_unique_id=f"proj-pf-{i:03d}",
                worktree=f"/path/to/worktree{i}",
                name=f"Test Project {i}",
            )
        await db_session.commit()
        
        # Get first page of filtered results
        results = await repo.list(offset=0, limit=2, name="Test")
        assert len(results) == 2


class TestProjectRepositoryUpdate:
    """Tests for ProjectRepository.update method."""

    @pytest.mark.asyncio
    async def test_update_project_name(self, db_session: AsyncSession):
        """Test updating project name."""
        repo = ProjectRepository(db_session)
        
        project = await create_test_project(
            repo,
            project_unique_id="proj-update-001",
            worktree="/path/to/worktree",
            name="Original Name",
        )
        await db_session.commit()
        
        updated = await repo.update(project, name="Updated Name")
        await db_session.commit()
        
        assert updated.name == "Updated Name"
        assert updated.project_unique_id == "proj-update-001"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, db_session: AsyncSession):
        """Test updating multiple project fields."""
        repo = ProjectRepository(db_session)
        
        project = await create_test_project(
            repo,
            project_unique_id="proj-update-002",
            worktree="/original/path",
            name="Original",
            branch="main",
        )
        await db_session.commit()
        
        new_time = int(time.time()) + 1000
        updated = await repo.update(
            project,
            worktree="/new/path",
            name="Updated",
            branch="develop",
            time_updated=new_time,
        )
        await db_session.commit()
        
        assert updated.worktree == "/new/path"
        assert updated.name == "Updated"
        assert updated.branch == "develop"
        assert updated.time_updated == new_time


class TestProjectRepositoryDelete:
    """Tests for ProjectRepository.delete method."""

    @pytest.mark.asyncio
    async def test_delete_project(self, db_session: AsyncSession):
        """Test deleting a project."""
        repo = ProjectRepository(db_session)
        
        project = await create_test_project(
            repo,
            project_unique_id="proj-delete-001",
            worktree="/path/to/worktree",
            name="To Delete",
        )
        await db_session.commit()
        project_id = project.id
        
        await repo.delete(project)
        await db_session.commit()
        
        result = await repo.get_by_id(project_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_cascades_to_workspaces(self, db_session: AsyncSession):
        """Test that deleting a project cascades to related workspaces."""
        repo = ProjectRepository(db_session)
        
        # Create project
        project = await create_test_project(
            repo,
            project_unique_id="proj-cascade-001",
            worktree="/path/to/worktree",
            name="Cascade Project",
        )
        await db_session.flush()
        
        # Create workspace for the project
        current_time = int(time.time())
        workspace = Workspace(
            workspace_unique_id="ws-001",
            project_unique_id="proj-cascade-001",
            name="Test Workspace",
            directory="/test/dir",
        )
        db_session.add(workspace)
        await db_session.commit()
        
        # Delete the project
        await repo.delete(project)
        await db_session.commit()
        
        # Verify workspace is also deleted
        from sqlalchemy import select
        result = await db_session.execute(
            select(Workspace).where(Workspace.workspace_unique_id == "ws-001")
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_cascades_to_sessions(self, db_session: AsyncSession):
        """Test that deleting a project cascades to related sessions."""
        repo = ProjectRepository(db_session)
        
        # Create project
        project = await create_test_project(
            repo,
            project_unique_id="proj-cascade-002",
            worktree="/path/to/worktree",
            name="Cascade Project 2",
        )
        await db_session.flush()
        
        # Create workspace
        workspace = Workspace(
            workspace_unique_id="ws-002",
            project_unique_id="proj-cascade-002",
            name="Test Workspace",
            directory="/test/dir",
        )
        db_session.add(workspace)
        await db_session.flush()
        
        # Create session
        current_time = int(time.time())
        session = Session(
            session_unique_id="sess-001",
            external_session_id="external-sess-001",
            project_unique_id="proj-cascade-002",
            workspace_unique_id="ws-002",
            directory="/test/dir",
            title="Test Session",
            time_created=current_time,
            time_updated=current_time,
        )
        db_session.add(session)
        await db_session.commit()
        
        # Delete the project
        await repo.delete(project)
        await db_session.commit()
        
        # Verify session is also deleted
        from sqlalchemy import select
        result = await db_session.execute(
            select(Session).where(Session.session_unique_id == "sess-001")
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_cascades_to_messages(self, db_session: AsyncSession):
        """Test that deleting a project cascades to related messages."""
        repo = ProjectRepository(db_session)
        
        # Create project
        project = await create_test_project(
            repo,
            project_unique_id="proj-cascade-003",
            worktree="/path/to/worktree",
            name="Cascade Project 3",
        )
        await db_session.flush()
        
        # Create workspace
        workspace = Workspace(
            workspace_unique_id="ws-003",
            project_unique_id="proj-cascade-003",
            name="Test Workspace",
            directory="/test/dir",
        )
        db_session.add(workspace)
        await db_session.flush()
        
        # Create session
        current_time = int(time.time())
        session = Session(
            session_unique_id="sess-002",
            external_session_id="external-sess-002",
            project_unique_id="proj-cascade-003",
            workspace_unique_id="ws-003",
            directory="/test/dir",
            title="Test Session",
            time_created=current_time,
            time_updated=current_time,
        )
        db_session.add(session)
        await db_session.flush()
        
        # Create message
        message = Message(
            message_unique_id="msg-001",
            session_unique_id="sess-002",
            time_created=current_time,
            time_updated=current_time,
            data='{"content": "test message"}',
        )
        db_session.add(message)
        await db_session.commit()
        
        # Delete the project
        await repo.delete(project)
        await db_session.commit()
        
        # Verify message is also deleted
        from sqlalchemy import select
        result = await db_session.execute(
            select(Message).where(Message.message_unique_id == "msg-001")
        )
        assert result.scalar_one_or_none() is None


class TestProjectRepositoryCount:
    """Tests for ProjectRepository.count method."""

    @pytest.mark.asyncio
    async def test_count_all_projects(self, db_session: AsyncSession):
        """Test counting all projects."""
        repo = ProjectRepository(db_session)
        
        for i in range(5):
            await create_test_project(
                repo,
                project_unique_id=f"proj-count-{i:03d}",
                worktree=f"/path/to/worktree{i}",
                name=f"Project {i}",
            )
        await db_session.commit()
        
        count = await repo.count()
        
        assert count == 5

    @pytest.mark.asyncio
    async def test_count_with_filter(self, db_session: AsyncSession):
        """Test counting projects with filter."""
        repo = ProjectRepository(db_session)
        
        await create_test_project(
            repo,
            project_unique_id="proj-count-filter-001",
            worktree="/path/to/worktree1",
            name="Alpha",
        )
        await create_test_project(
            repo,
            project_unique_id="proj-count-filter-002",
            worktree="/path/to/worktree2",
            name="Beta",
        )
        await create_test_project(
            repo,
            project_unique_id="proj-count-filter-003",
            worktree="/path/to/worktree3",
            name="Alpha",
        )
        await db_session.commit()
        
        count = await repo.count(name="Alpha")
        assert count == 2
        
        count = await repo.count(name="Beta")
        assert count == 1


class TestProjectRepositoryExists:
    """Tests for ProjectRepository.exists method."""

    @pytest.mark.asyncio
    async def test_exists_true(self, db_session: AsyncSession):
        """Test checking if project exists (True case)."""
        repo = ProjectRepository(db_session)
        
        project = await create_test_project(
            repo,
            project_unique_id="proj-exists-001",
            worktree="/path/to/worktree",
            name="Existing Project",
        )
        await db_session.commit()
        
        assert await repo.exists(project.id) is True

    @pytest.mark.asyncio
    async def test_exists_false(self, db_session: AsyncSession):
        """Test checking if project exists (False case)."""
        repo = ProjectRepository(db_session)
        
        assert await repo.exists(99999) is False
