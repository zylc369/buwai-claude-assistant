"""Tests for ProjectRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Project
from repositories.project_repository import ProjectRepository
from repositories.user_repository import UserRepository


@pytest.mark.asyncio
class TestProjectRepository:
    """Test suite for ProjectRepository."""

    async def _create_test_user(self, db_session: AsyncSession) -> User:
        """Helper to create a test user."""
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="owner@example.com",
            username="owner",
            hashed_password="hashed123"
        )
        await db_session.commit()
        return user

    async def test_get_by_owner(self, db_session: AsyncSession):
        """Test retrieving projects by owner."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = ProjectRepository(db_session)
        
        project1 = await repo.create(
            name="Project 1",
            description="First project",
            owner_id=user.id
        )
        project2 = await repo.create(
            name="Project 2",
            description="Second project",
            owner_id=user.id
        )
        await db_session.commit()

        # Act
        projects = await repo.get_by_owner(user.id)

        # Assert
        assert len(projects) == 2
        names = [p.name for p in projects]
        assert "Project 1" in names
        assert "Project 2" in names

    async def test_get_by_owner_no_projects(self, db_session: AsyncSession):
        """Test retrieving projects when user has none."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = ProjectRepository(db_session)

        # Act
        projects = await repo.get_by_owner(user.id)

        # Assert
        assert len(projects) == 0

    async def test_search_by_name(self, db_session: AsyncSession):
        """Test searching projects by name (case-insensitive)."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = ProjectRepository(db_session)
        
        await repo.create(name="Web Application", owner_id=user.id)
        await repo.create(name="Mobile App", owner_id=user.id)
        await repo.create(name="API Service", owner_id=user.id)
        await db_session.commit()

        # Act
        results = await repo.search_by_name("app")

        # Assert
        assert len(results) == 2
        names = [p.name for p in results]
        assert "Web Application" in names
        assert "Mobile App" in names
        assert "API Service" not in names

    async def test_search_by_name_no_matches(self, db_session: AsyncSession):
        """Test searching projects with no matches."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = ProjectRepository(db_session)
        await repo.create(name="Project Alpha", owner_id=user.id)
        await db_session.commit()

        # Act
        results = await repo.search_by_name("nonexistent")

        # Assert
        assert len(results) == 0

    async def test_count_projects_by_owner(self, db_session: AsyncSession):
        """Test counting projects for a specific owner."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = ProjectRepository(db_session)
        
        await repo.create(name="Project 1", owner_id=user.id)
        await repo.create(name="Project 2", owner_id=user.id)
        await repo.create(name="Project 3", owner_id=user.id)
        await db_session.commit()

        # Act
        count = await repo.count_projects_by_owner(user.id)

        # Assert
        assert count == 3

    async def test_inherits_base_repository_methods(self, db_session: AsyncSession):
        """Test that ProjectRepository inherits all base repository methods."""
        # Arrange
        user = await self._create_test_user(db_session)
        repo = ProjectRepository(db_session)
        project = await repo.create(
            name="Test Project",
            description="Test description",
            owner_id=user.id
        )
        await db_session.commit()

        # Act - Test get_by_id from base
        found = await repo.get_by_id(project.id)
        assert found is not None
        assert found.name == "Test Project"

        # Act - Test update from base
        updated = await repo.update(project, description="Updated description")
        assert updated.description == "Updated description"

        # Act - Test delete from base
        await repo.delete(project)
        await db_session.commit()
        deleted = await repo.get_by_id(project.id)
        assert deleted is None
