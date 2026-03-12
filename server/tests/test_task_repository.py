"""Tests for TaskRepository."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Project, Task
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from repositories.project_repository import ProjectRepository


@pytest.mark.asyncio
class TestTaskRepository:
    """Test suite for TaskRepository."""

    async def _create_test_data(self, db_session: AsyncSession) -> tuple[User, Project]:
        """Helper to create test user and project."""
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="user@example.com",
            username="testuser",
            hashed_password="hashed123"
        )
        
        project_repo = ProjectRepository(db_session)
        project = await project_repo.create(
            name="Test Project",
            owner_id=user.id
        )
        
        await db_session.commit()
        return user, project

    async def test_get_by_project(self, db_session: AsyncSession):
        """Test retrieving tasks by project."""
        # Arrange
        user, project = await self._create_test_data(db_session)
        repo = TaskRepository(db_session)
        
        task1 = await repo.create(
            title="Task 1",
            project_id=project.id
        )
        task2 = await repo.create(
            title="Task 2",
            project_id=project.id
        )
        await db_session.commit()

        # Act
        tasks = await repo.get_by_project(project.id)

        # Assert
        assert len(tasks) == 2
        titles = [t.title for t in tasks]
        assert "Task 1" in titles
        assert "Task 2" in titles

    async def test_get_by_assignee(self, db_session: AsyncSession):
        """Test retrieving tasks assigned to a user."""
        # Arrange
        user, project = await self._create_test_data(db_session)
        repo = TaskRepository(db_session)
        
        task1 = await repo.create(
            title="Assigned Task 1",
            project_id=project.id,
            assignee_id=user.id
        )
        task2 = await repo.create(
            title="Assigned Task 2",
            project_id=project.id,
            assignee_id=user.id
        )
        task3 = await repo.create(
            title="Unassigned Task",
            project_id=project.id
        )
        await db_session.commit()

        # Act
        tasks = await repo.get_by_assignee(user.id)

        # Assert
        assert len(tasks) == 2
        titles = [t.title for t in tasks]
        assert "Assigned Task 1" in titles
        assert "Assigned Task 2" in titles
        assert "Unassigned Task" not in titles

    async def test_get_by_status(self, db_session: AsyncSession):
        """Test retrieving tasks by status."""
        # Arrange
        user, project = await self._create_test_data(db_session)
        repo = TaskRepository(db_session)
        
        await repo.create(title="Pending Task", project_id=project.id, status="pending")
        await repo.create(title="In Progress Task", project_id=project.id, status="in_progress")
        await repo.create(title="Completed Task", project_id=project.id, status="completed")
        await db_session.commit()

        # Act
        pending_tasks = await repo.get_by_status("pending")
        completed_tasks = await repo.get_by_status("completed")

        # Assert
        assert len(pending_tasks) == 1
        assert pending_tasks[0].title == "Pending Task"
        
        assert len(completed_tasks) == 1
        assert completed_tasks[0].title == "Completed Task"

    async def test_get_by_priority(self, db_session: AsyncSession):
        """Test retrieving tasks by priority."""
        # Arrange
        user, project = await self._create_test_data(db_session)
        repo = TaskRepository(db_session)
        
        await repo.create(title="High Priority", project_id=project.id, priority="high")
        await repo.create(title="Normal Priority", project_id=project.id, priority="normal")
        await repo.create(title="Low Priority", project_id=project.id, priority="low")
        await db_session.commit()

        # Act
        high_tasks = await repo.get_by_priority("high")

        # Assert
        assert len(high_tasks) == 1
        assert high_tasks[0].title == "High Priority"

    async def test_get_overdue_tasks(self, db_session: AsyncSession):
        """Test retrieving overdue tasks."""
        # Arrange
        user, project = await self._create_test_data(db_session)
        repo = TaskRepository(db_session)
        
        # Create overdue task
        await repo.create(
            title="Overdue Task",
            project_id=project.id,
            due_date=datetime.utcnow() - timedelta(days=1)
        )
        
        # Create future task
        await repo.create(
            title="Future Task",
            project_id=project.id,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        
        await db_session.commit()

        # Act
        overdue_tasks = await repo.get_overdue_tasks()

        # Assert
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].title == "Overdue Task"

    async def test_count_tasks_by_project(self, db_session: AsyncSession):
        """Test counting tasks for a project."""
        # Arrange
        user, project = await self._create_test_data(db_session)
        repo = TaskRepository(db_session)
        
        await repo.create(title="Task 1", project_id=project.id)
        await repo.create(title="Task 2", project_id=project.id)
        await repo.create(title="Task 3", project_id=project.id)
        await db_session.commit()

        # Act
        count = await repo.count_tasks_by_project(project.id)

        # Assert
        assert count == 3

    async def test_inherits_base_repository_methods(self, db_session: AsyncSession):
        """Test that TaskRepository inherits all base repository methods."""
        # Arrange
        user, project = await self._create_test_data(db_session)
        repo = TaskRepository(db_session)
        task = await repo.create(
            title="Test Task",
            description="Test description",
            project_id=project.id
        )
        await db_session.commit()

        # Act - Test get_by_id from base
        found = await repo.get_by_id(task.id)
        assert found is not None
        assert found.title == "Test Task"

        # Act - Test update from base
        updated = await repo.update(task, status="completed")
        assert updated.status == "completed"

        # Act - Test delete from base
        await repo.delete(task)
        await db_session.commit()
        deleted = await repo.get_by_id(task.id)
        assert deleted is None
