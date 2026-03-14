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
            directory="my_project_dir",
            name="Minimal Project",
        )

        assert project.id is not None
        assert project.project_unique_id == "proj-001"
        assert project.directory == "my_project_dir"
        assert project.name == "Minimal Project"
        assert project.branch is None
        assert project.gmt_create >= before
        assert project.gmt_modified >= before

    @pytest.mark.asyncio
    async def test_create_project_with_all_fields(self, db_session: AsyncSession):
        """Test creating a project with all fields."""
        service = ProjectService(db_session)

        project = await service.create_project(
            project_unique_id="proj-002",
            directory="my_project_dir",
            name="My Project",
            branch="main",
        )

        assert project.project_unique_id == "proj-002"
        assert project.name == "My Project"
        assert project.branch == "main"

    @pytest.mark.asyncio
    async def test_create_project_auto_timestamps(self, db_session: AsyncSession):
        """Test that create_project auto-sets timestamps."""
        service = ProjectService(db_session)

        before = int(time_module.time())
        project = await service.create_project(
            project_unique_id="proj-003",
            directory="my_project_dir",
            name="Auto Timestamps Project",
        )
        after = int(time_module.time())

        assert project.gmt_create >= before
        assert project.gmt_create <= after
        assert project.gmt_modified == project.gmt_create

    @pytest.mark.asyncio
    async def test_create_project_auto_uuid(self, db_session: AsyncSession):
        """Test that create_project auto-generates UUID if not provided."""
        service = ProjectService(db_session)

        project = await service.create_project(directory="auto_uuid_dir", name="Auto UUID Project")

        assert project.project_unique_id is not None
        assert len(project.project_unique_id) == 36

    @pytest.mark.asyncio
    async def test_create_project_invalid_directory(self, db_session: AsyncSession):
        """Test that create_project rejects invalid directory names."""
        service = ProjectService(db_session)

        with pytest.raises(ValueError, match="Invalid directory name"):
            await service.create_project(directory="invalid-dir!", name="Test Project")

    @pytest.mark.asyncio
    async def test_create_project_directory_with_spaces_fails(self, db_session: AsyncSession):
        """Test that create_project rejects directory names with spaces."""
        service = ProjectService(db_session)

        with pytest.raises(ValueError, match="Invalid directory name"):
            await service.create_project(directory="invalid dir", name="Test Project")


class TestProjectServiceGetById:
    """Tests for ProjectService.get_project_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, db_session: AsyncSession):
        """Test getting an existing project by ID."""
        service = ProjectService(db_session)
        
        created = await service.create_project(
            project_unique_id="proj-010",
            directory="my_project_dir",
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
            directory="my_project_dir",
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
                directory=f"project_dir_{i}",
                name=f"List Project {i}",
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
                directory=f"project_dir_{i}",
                name=f"Page Project {i}",
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
            directory="project_dir_1",
            name="Alpha Project",
        )
        await service.create_project(
            project_unique_id="proj-filter-002",
            directory="project_dir_1",
            name="Beta Project",
        )
        await service.create_project(
            project_unique_id="proj-filter-003",
            directory="project_dir_2",
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
                directory=f"project_dir_{i}",
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
            directory="my_project_dir",
            name="Original Name",
        )
        original_updated = project.gmt_modified

        updated = await service.update_project(project.id, name="Updated Name")

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.gmt_modified >= original_updated

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, db_session: AsyncSession):
        """Test updating multiple project fields."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            project_unique_id="proj-update-002",
            directory="original_dir",
            name="Original",
            branch="main",
        )
        
        new_directory = "new_dir"
        updated = await service.update_project(
            project.id,
            directory=new_directory,
            name="Updated",
            branch="develop",
        )

        assert updated.directory == new_directory
        assert updated.name == "Updated"
        assert updated.branch == "develop"

    @pytest.mark.asyncio
    async def test_update_auto_gmt_modified(self, db_session: AsyncSession):
        """Test that update_project auto-updates gmt_modified."""
        service = ProjectService(db_session)

        project = await service.create_project(
            project_unique_id="proj-update-003",
            directory="my_project_dir",
            name="Original Name",
        )
        original_time = project.gmt_modified

        before = int(time_module.time())
        updated = await service.update_project(project.id, name="New Name")
        after = int(time_module.time())

        assert updated.gmt_modified >= original_time
        assert updated.gmt_modified >= before
        assert updated.gmt_modified <= after

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
            directory="my_project_dir",
            name="Delete Project",
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
            directory="my_project_dir",
            name="Cascade Project",
        )

        current_time = int(time_module.time())
        workspace = Workspace(
            workspace_unique_id="ws-cascade-001",
            project_unique_id="proj-cascade-001",
            directory="/test/dir",
            gmt_create=current_time,
            gmt_modified=current_time,
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
            directory="my_project_dir",
            name="Cascade Project 2",
        )

        current_time = int(time_module.time())
        workspace = Workspace(
            workspace_unique_id="ws-cascade-002",
            project_unique_id="proj-cascade-002",
            directory="/test/dir",
            gmt_create=current_time,
            gmt_modified=current_time,
        )
        db_session.add(workspace)
        await db_session.flush()

        session = Session(
            session_unique_id="sess-cascade-001",
            external_session_id="external-sess-cascade-001",
            project_unique_id="proj-cascade-002",
            workspace_unique_id="ws-cascade-002",
            directory="/test/dir",
            title="Test Session",
            gmt_create=current_time,
            gmt_modified=current_time,
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
            directory="my_project_dir",
            name="Cascade Project 3",
        )

        current_time = int(time_module.time())
        workspace = Workspace(
            workspace_unique_id="ws-cascade-003",
            project_unique_id="proj-cascade-003",
            directory="/test/dir",
            gmt_create=current_time,
            gmt_modified=current_time,
        )
        db_session.add(workspace)
        await db_session.flush()

        session = Session(
            session_unique_id="sess-cascade-002",
            external_session_id="external-sess-cascade-002",
            project_unique_id="proj-cascade-003",
            workspace_unique_id="ws-cascade-003",
            directory="/test/dir",
            title="Test Session",
            gmt_create=current_time,
            gmt_modified=current_time,
        )
        db_session.add(session)
        await db_session.flush()

        message = Message(
            message_unique_id="msg-cascade-001",
            session_unique_id="sess-cascade-002",
            gmt_create=current_time,
            gmt_modified=current_time,
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
