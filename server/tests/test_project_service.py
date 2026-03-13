"""Tests for ProjectService."""

import pytest
import time as time_module
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project, Workspace, Session, Message
from services.project_service import ProjectService


class TestProjectServiceCreate:
    """Tests for ProjectService.create_project method."""

    @pytest.mark.asyncio
    async def test_create_project_minimal(self, db_session: AsyncSession):
        """Test creating a project with minimal required fields."""
        service = ProjectService(db_session)
        
        before = int(time_module.time())
        project = await service.create_project(
            project_unique_id="proj-001",
            worktree="/path/to/worktree",
        )
        
        assert project.id is not None
        assert project.project_unique_id == "proj-001"
        assert project.worktree == "/path/to/worktree"
        assert project.name is None
        assert project.branch is None
        assert project.time_initialized is None
        assert project.time_created >= before
        assert project.time_updated >= before

    @pytest.mark.asyncio
    async def test_create_project_with_all_fields(self, db_session: AsyncSession):
        """Test creating a project with all fields."""
        service = ProjectService(db_session)
        init_time = int(time_module.time()) - 1000
        
        project = await service.create_project(
            project_unique_id="proj-002",
            worktree="/path/to/worktree",
            name="My Project",
            branch="main",
            time_initialized=init_time,
        )
        
        assert project.project_unique_id == "proj-002"
        assert project.name == "My Project"
        assert project.branch == "main"
        assert project.time_initialized == init_time

    @pytest.mark.asyncio
    async def test_create_project_auto_timestamps(self, db_session: AsyncSession):
        """Test that create_project auto-sets timestamps."""
        service = ProjectService(db_session)
        
        before = int(time_module.time())
        project = await service.create_project(
            project_unique_id="proj-003",
            worktree="/path/to/worktree",
        )
        after = int(time_module.time())
        
        assert project.time_created >= before
        assert project.time_created <= after
        assert project.time_updated == project.time_created


class TestProjectServiceGetById:
    """Tests for ProjectService.get_project_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, db_session: AsyncSession):
        """Test getting an existing project by ID."""
        service = ProjectService(db_session)
        
        created = await service.create_project(
            project_unique_id="proj-010",
            worktree="/path/to/worktree",
            name="Test Project",
        )
        
        result = await service.get_project_by_id(created.id)
        
        assert result is not None
        assert result.id == created.id
        assert result.project_unique_id == "proj-010"

    @pytest.mark.asyncio
    async def test_get_by_id_not_exists(self, db_session: AsyncSession):
        """Test getting a non-existent project by ID."""
        service = ProjectService(db_session)
        
        result = await service.get_project_by_id(99999)
        
        assert result is None


class TestProjectServiceGetByUniqueId:
    """Tests for ProjectService.get_project_by_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_unique_id_exists(self, db_session: AsyncSession):
        """Test getting an existing project by unique ID."""
        service = ProjectService(db_session)
        
        await service.create_project(
            project_unique_id="unique-proj-001",
            worktree="/path/to/worktree",
            name="Unique Project",
        )
        
        result = await service.get_project_by_unique_id("unique-proj-001")
        
        assert result is not None
        assert result.project_unique_id == "unique-proj-001"

    @pytest.mark.asyncio
    async def test_get_by_unique_id_not_exists(self, db_session: AsyncSession):
        """Test getting a non-existent project by unique ID."""
        service = ProjectService(db_session)
        
        result = await service.get_project_by_unique_id("non-existent-id")
        
        assert result is None


class TestProjectServiceList:
    """Tests for ProjectService.list_projects method."""

    @pytest.mark.asyncio
    async def test_list_all_projects(self, db_session: AsyncSession):
        """Test listing all projects."""
        service = ProjectService(db_session)
        
        for i in range(5):
            await service.create_project(
                project_unique_id=f"proj-list-{i:03d}",
                worktree=f"/path/to/worktree{i}",
            )
        
        results = await service.list_projects()
        
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, db_session: AsyncSession):
        """Test listing projects with pagination."""
        service = ProjectService(db_session)
        
        for i in range(10):
            await service.create_project(
                project_unique_id=f"proj-page-{i:03d}",
                worktree=f"/path/to/worktree{i}",
            )
        
        page1 = await service.list_projects(offset=0, limit=3)
        assert len(page1) == 3
        
        page2 = await service.list_projects(offset=3, limit=3)
        assert len(page2) == 3
        
        last = await service.list_projects(offset=9, limit=3)
        assert len(last) == 1

    @pytest.mark.asyncio
    async def test_list_with_name_filter(self, db_session: AsyncSession):
        """Test listing projects with name filter."""
        service = ProjectService(db_session)
        
        await service.create_project(
            project_unique_id="proj-filter-001",
            worktree="/path/to/worktree1",
            name="Alpha Project",
        )
        await service.create_project(
            project_unique_id="proj-filter-002",
            worktree="/path/to/worktree2",
            name="Beta Project",
        )
        await service.create_project(
            project_unique_id="proj-filter-003",
            worktree="/path/to/worktree3",
            name="Alpha App",
        )
        
        results = await service.list_projects(name="alpha")
        
        assert len(results) == 2
        names = [p.name for p in results]
        assert "Alpha Project" in names
        assert "Alpha App" in names

    @pytest.mark.asyncio
    async def test_list_with_pagination_and_filter(self, db_session: AsyncSession):
        """Test listing projects with pagination and filter combined."""
        service = ProjectService(db_session)
        
        for i in range(10):
            await service.create_project(
                project_unique_id=f"proj-pf-{i:03d}",
                worktree=f"/path/to/worktree{i}",
                name=f"Test Project {i}",
            )
        
        results = await service.list_projects(offset=0, limit=2, name="Test")
        assert len(results) == 2


class TestProjectServiceUpdate:
    """Tests for ProjectService.update_project method."""

    @pytest.mark.asyncio
    async def test_update_project_name(self, db_session: AsyncSession):
        """Test updating project name."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            project_unique_id="proj-update-001",
            worktree="/path/to/worktree",
            name="Original Name",
        )
        original_updated = project.time_updated
        
        updated = await service.update_project(project.id, name="Updated Name")
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.time_updated >= original_updated

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, db_session: AsyncSession):
        """Test updating multiple project fields."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            project_unique_id="proj-update-002",
            worktree="/original/path",
            name="Original",
            branch="main",
        )
        
        new_worktree = "/new/path"
        updated = await service.update_project(
            project.id,
            worktree=new_worktree,
            name="Updated",
            branch="develop",
        )
        
        assert updated.worktree == new_worktree
        assert updated.name == "Updated"
        assert updated.branch == "develop"

    @pytest.mark.asyncio
    async def test_update_auto_time_updated(self, db_session: AsyncSession):
        """Test that update_project auto-updates time_updated."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            project_unique_id="proj-update-003",
            worktree="/path/to/worktree",
        )
        original_time = project.time_updated
        
        before = int(time_module.time())
        updated = await service.update_project(project.id, name="New Name")
        after = int(time_module.time())
        
        assert updated.time_updated >= original_time
        assert updated.time_updated >= before
        assert updated.time_updated <= after

    @pytest.mark.asyncio
    async def test_update_not_found(self, db_session: AsyncSession):
        """Test updating a non-existent project."""
        service = ProjectService(db_session)
        
        result = await service.update_project(99999, name="New Name")
        
        assert result is None


class TestProjectServiceDelete:
    """Tests for ProjectService.delete_project method."""

    @pytest.mark.asyncio
    async def test_delete_project(self, db_session: AsyncSession):
        """Test deleting a project."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            project_unique_id="proj-delete-001",
            worktree="/path/to/worktree",
        )
        project_id = project.id
        
        result = await service.delete_project(project_id)
        
        assert result is True
        assert await service.get_project_by_id(project_id) is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, db_session: AsyncSession):
        """Test deleting a non-existent project."""
        service = ProjectService(db_session)
        
        result = await service.delete_project(99999)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_cascades_to_workspaces(self, db_session: AsyncSession):
        """Test that deleting a project cascades to related workspaces."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            project_unique_id="proj-cascade-001",
            worktree="/path/to/worktree",
        )
        
        workspace = Workspace(
            workspace_unique_id="ws-cascade-001",
            project_unique_id="proj-cascade-001",
            name="Test Workspace",
            directory="/test/dir",
        )
        db_session.add(workspace)
        await db_session.commit()
        
        await service.delete_project(project.id)
        
        from sqlalchemy import select
        result = await db_session.execute(
            select(Workspace).where(Workspace.workspace_unique_id == "ws-cascade-001")
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_cascades_to_sessions(self, db_session: AsyncSession):
        """Test that deleting a project cascades to related sessions."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            project_unique_id="proj-cascade-002",
            worktree="/path/to/worktree",
        )
        
        workspace = Workspace(
            workspace_unique_id="ws-cascade-002",
            project_unique_id="proj-cascade-002",
            name="Test Workspace",
            directory="/test/dir",
        )
        db_session.add(workspace)
        await db_session.flush()
        
        current_time = int(time_module.time())
        session = Session(
            session_unique_id="sess-cascade-001",
            external_session_id="external-sess-cascade-001",
            project_unique_id="proj-cascade-002",
            workspace_unique_id="ws-cascade-002",
            directory="/test/dir",
            title="Test Session",
            time_created=current_time,
            time_updated=current_time,
        )
        db_session.add(session)
        await db_session.commit()
        
        await service.delete_project(project.id)
        
        from sqlalchemy import select
        result = await db_session.execute(
            select(Session).where(Session.session_unique_id == "sess-cascade-001")
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_cascades_to_messages(self, db_session: AsyncSession):
        """Test that deleting a project cascades to related messages."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            project_unique_id="proj-cascade-003",
            worktree="/path/to/worktree",
        )
        
        workspace = Workspace(
            workspace_unique_id="ws-cascade-003",
            project_unique_id="proj-cascade-003",
            name="Test Workspace",
            directory="/test/dir",
        )
        db_session.add(workspace)
        await db_session.flush()
        
        current_time = int(time_module.time())
        session = Session(
            session_unique_id="sess-cascade-002",
            external_session_id="external-sess-cascade-002",
            project_unique_id="proj-cascade-003",
            workspace_unique_id="ws-cascade-003",
            directory="/test/dir",
            title="Test Session",
            time_created=current_time,
            time_updated=current_time,
        )
        db_session.add(session)
        await db_session.flush()
        
        message = Message(
            message_unique_id="msg-cascade-001",
            session_unique_id="sess-cascade-002",
            time_created=current_time,
            time_updated=current_time,
            data='{"content": "test message"}',
        )
        db_session.add(message)
        await db_session.commit()
        
        await service.delete_project(project.id)
        
        from sqlalchemy import select
        result = await db_session.execute(
            select(Message).where(Message.message_unique_id == "msg-cascade-001")
        )
        assert result.scalar_one_or_none() is None
