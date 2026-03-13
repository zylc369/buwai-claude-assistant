import pytest
import pytest_asyncio
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Project
from services import UserService, ProjectService


@pytest_asyncio.fixture
async def project_service_user(db_session: AsyncSession):
    """Create a test user for project tests."""
    user_service = UserService(db_session)
    user = await user_service.create_user(
        email="project_test@example.com",
        username="projectuser",
        password="password123"
    )
    return user


class TestProjectServiceCreate:
    """Tests for ProjectService.create_project method."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, db_session: AsyncSession, project_service_user):
        """Test creating a project successfully."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            name="Test Project",
            description="Test Description",
            owner_id=project_service_user.id
        )
        
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "Test Description"
        assert project.owner_id == project_service_user.id

    @pytest.mark.asyncio
    async def test_create_project_minimal(self, db_session: AsyncSession, project_service_user):
        """Test creating a project with minimal data."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            name="Minimal Project",
            owner_id=project_service_user.id
        )
        
        assert project.description is None


class TestProjectServiceGet:
    """Tests for ProjectService get methods."""

    @pytest.mark.asyncio
    async def test_get_project_by_id(self, db_session: AsyncSession, project_service_user):
        """Test getting project by ID."""
        service = ProjectService(db_session)
        
        created = await service.create_project(
            name="Test Project",
            owner_id=project_service_user.id
        )
        
        found = await service.get_project(created.id)
        
        assert found is not None
        assert found.id == created.id
        assert found.name == "Test Project"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, db_session: AsyncSession):
        """Test getting non-existent project returns None."""
        service = ProjectService(db_session)
        
        found = await service.get_project(999)
        
        assert found is None

    @pytest.mark.asyncio
    async def test_get_user_projects(self, db_session: AsyncSession, project_service_user):
        """Test getting all projects for a user."""
        service = ProjectService(db_session)
        
        # Create multiple projects
        await service.create_project(
            name="Project 1",
            owner_id=project_service_user.id
        )
        await service.create_project(
            name="Project 2",
            owner_id=project_service_user.id
        )
        
        projects = await service.get_user_projects(project_service_user.id)
        
        assert len(projects) == 2
        assert projects[0].name == "Project 1"
        assert projects[1].name == "Project 2"

    @pytest.mark.asyncio
    async def test_search_projects(self, db_session: AsyncSession, project_service_user):
        """Test searching projects by name."""
        service = ProjectService(db_session)
        
        await service.create_project(
            name="Alpha Project",
            owner_id=project_service_user.id
        )
        await service.create_project(
            name="Beta Project",
            owner_id=project_service_user.id
        )
        
        results = await service.search_projects("Alpha")
        
        assert len(results) == 1
        assert results[0].name == "Alpha Project"


class TestProjectServiceUpdate:
    """Tests for ProjectService.update_project method."""

    @pytest.mark.asyncio
    async def test_update_project_name(self, db_session: AsyncSession, project_service_user):
        """Test updating project name."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            name="Old Name",
            owner_id=project_service_user.id
        )
        
        updated = await service.update_project(project.id, name="New Name")
        
        assert updated.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_project_description(self, db_session: AsyncSession, project_service_user):
        """Test updating project description."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            name="Test Project",
            description="Old Description",
            owner_id=project_service_user.id
        )
        
        updated = await service.update_project(project.id, description="New Description")
        
        assert updated.description == "New Description"

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, db_session: AsyncSession):
        """Test updating non-existent project returns None."""
        service = ProjectService(db_session)
        
        updated = await service.update_project(999, name="New Name")
        
        assert updated is None


class TestProjectServiceDelete:
    """Tests for ProjectService.delete_project method."""

    @pytest.mark.asyncio
    async def test_delete_project_success(self, db_session: AsyncSession, project_service_user):
        """Test deleting project successfully."""
        service = ProjectService(db_session)
        
        project = await service.create_project(
            name="To Delete",
            owner_id=project_service_user.id
        )
        
        result = await service.delete_project(project.id)
        
        assert result is True
        
        # Verify deleted
        found = await service.get_project(project.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, db_session: AsyncSession):
        """Test deleting non-existent project returns False."""
        service = ProjectService(db_session)
        
        result = await service.delete_project(999)
        
        assert result is False
