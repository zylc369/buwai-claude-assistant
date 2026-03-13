"""Tests for TaskService."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Project, Task
from services import UserService, ProjectService, TaskService


@pytest_asyncio.fixture
async def task_service_user(db_session: AsyncSession):
    """Create a test user for task tests."""
    user_service = UserService(db_session)
    user = await user_service.create_user(
        email="task_test@example.com",
        username="taskuser",
        password="password123"
    )
    return user


@pytest_asyncio.fixture
async def task_service_project(db_session: AsyncSession, task_service_user):
    """Create a test project for task tests."""
    project_service = ProjectService(db_session)
    project = await project_service.create_project(
        name="Test Project",
        description="For task tests",
        owner_id=task_service_user.id
    )
    return project


class TestTaskServiceCreate:
    """Tests for TaskService.create_task method."""

    @pytest.mark.asyncio
    async def test_create_task_success(self, db_session: AsyncSession, task_service_project):
        """Test creating a task successfully."""
        service = TaskService(db_session)
        
        task = await service.create_task(
            title="Test Task",
            description="Test Description",
            project_id=task_service_project.id
        )
        
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.project_id == task_service_project.id
        assert task.status == "pending"
        assert task.priority == "normal"

    @pytest.mark.asyncio
    async def test_create_task_with_assignee(self, db_session: AsyncSession, task_service_project, task_service_user):
        """Test creating a task with an assignee."""
        service = TaskService(db_session)
        
        task = await service.create_task(
            title="Assigned Task",
            project_id=task_service_project.id,
            assignee_id=task_service_user.id
        )
        
        assert task.assignee_id == task_service_user.id

    @pytest.mark.asyncio
    async def test_create_task_with_due_date(self, db_session: AsyncSession, task_service_project):
        """Test creating a task with a due date."""
        service = TaskService(db_session)
        
        due_date = datetime.utcnow() + timedelta(days=7)
        
        task = await service.create_task(
            title="Timed Task",
            project_id=task_service_project.id,
            due_date=due_date
        )
        
        assert task.due_date is not None

    @pytest.mark.asyncio
    async def test_create_task_invalid_status(self, db_session: AsyncSession, task_service_project):
        """Test creating a task with invalid status raises ValueError."""
        service = TaskService(db_session)
        
        with pytest.raises(ValueError, match="Invalid status"):
            await service.create_task(
                title="Invalid Task",
                project_id=task_service_project.id,
                status="invalid_status"
            )

    @pytest.mark.asyncio
    async def test_create_task_invalid_priority(self, db_session: AsyncSession, task_service_project):
        """Test creating a task with invalid priority raises ValueError."""
        service = TaskService(db_session)
        
        with pytest.raises(ValueError, match="Invalid priority"):
            await service.create_task(
                title="Invalid Task",
                project_id=task_service_project.id,
                priority="invalid_priority"
            )


class TestTaskServiceGet:
    """Tests for TaskService get methods."""

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, db_session: AsyncSession, task_service_project):
        """Test getting task by ID."""
        service = TaskService(db_session)
        
        created = await service.create_task(
            title="Test Task",
            project_id=task_service_project.id
        )
        
        found = await service.get_task(created.id)
        
        assert found is not None
        assert found.id == created.id
        assert found.title == "Test Task"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, db_session: AsyncSession):
        """Test getting non-existent task returns None."""
        service = TaskService(db_session)
        
        found = await service.get_task(999)
        
        assert found is None

    @pytest.mark.asyncio
    async def test_get_project_tasks(self, db_session: AsyncSession, task_service_project):
        """Test getting all tasks for a project."""
        service = TaskService(db_session)
        
        await service.create_task(
            title="Task 1",
            project_id=task_service_project.id
        )
        await service.create_task(
            title="Task 2",
            project_id=task_service_project.id
        )
        
        tasks = await service.get_project_tasks(task_service_project.id)
        
        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_get_user_tasks(self, db_session: AsyncSession, task_service_project, task_service_user):
        """Test getting all tasks assigned to a user."""
        service = TaskService(db_session)
        
        await service.create_task(
            title="Assigned Task",
            project_id=task_service_project.id,
            assignee_id=task_service_user.id
        )
        
        tasks = await service.get_user_tasks(task_service_user.id)
        
        assert len(tasks) == 1
        assert tasks[0].assignee_id == task_service_user.id


class TestTaskServiceUpdate:
    """Tests for TaskService.update_task method."""

    @pytest.mark.asyncio
    async def test_update_task_status(self, db_session: AsyncSession, task_service_project):
        """Test updating task status."""
        service = TaskService(db_session)
        
        task = await service.create_task(
            title="Test Task",
            project_id=task_service_project.id
        )
        
        updated = await service.update_task(task.id, status="in_progress")
        
        assert updated.status == "in_progress"

    @pytest.mark.asyncio
    async def test_update_task_priority(self, db_session: AsyncSession, task_service_project):
        """Test updating task priority."""
        service = TaskService(db_session)
        
        task = await service.create_task(
            title="Test Task",
            project_id=task_service_project.id
        )
        
        updated = await service.update_task(task.id, priority="high")
        
        assert updated.priority == "high"

    @pytest.mark.asyncio
    async def test_update_task_invalid_status(self, db_session: AsyncSession, task_service_project):
        """Test updating task with invalid status raises ValueError."""
        service = TaskService(db_session)
        
        task = await service.create_task(
            title="Test Task",
            project_id=task_service_project.id
        )
        
        with pytest.raises(ValueError, match="Invalid status"):
            await service.update_task(task.id, status="invalid")

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, db_session: AsyncSession):
        """Test updating non-existent task returns None."""
        service = TaskService(db_session)
        
        updated = await service.update_task(999, status="completed")
        
        assert updated is None


class TestTaskServiceDelete:
    """Tests for TaskService.delete_task method."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, db_session: AsyncSession, task_service_project):
        """Test deleting task successfully."""
        service = TaskService(db_session)
        
        task = await service.create_task(
            title="To Delete",
            project_id=task_service_project.id
        )
        
        result = await service.delete_task(task.id)
        
        assert result is True
        
        # Verify deleted
        found = await service.get_task(task.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, db_session: AsyncSession):
        """Test deleting non-existent task returns False."""
        service = TaskService(db_session)
        
        result = await service.delete_task(999)
        
        assert result is False


class TestTaskServiceOverdue:
    """Tests for TaskService.get_overdue_tasks method."""

    @pytest.mark.asyncio
    async def test_get_overdue_tasks(self, db_session: AsyncSession, task_service_project):
        """Test getting overdue tasks."""
        service = TaskService(db_session)
        
        # Create overdue task
        await service.create_task(
            title="Overdue Task",
            project_id=task_service_project.id,
            due_date=datetime.utcnow() - timedelta(days=1)
        )
        
        # Create future task
        await service.create_task(
            title="Future Task",
            project_id=task_service_project.id,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        
        overdue = await service.get_overdue_tasks()
        
        assert len(overdue) >= 1
        assert all(t.title == "Overdue Task" for t in overdue)


class TestTaskServiceStatus:
    """Tests for TaskService.get_tasks_by_status method."""

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, db_session: AsyncSession, task_service_project):
        """Test getting tasks by status."""
        service = TaskService(db_session)
        
        await service.create_task(
            title="Pending Task",
            project_id=task_service_project.id,
            status="pending"
        )
        
        await service.create_task(
            title="In Progress Task",
            project_id=task_service_project.id,
            status="in_progress"
        )
        
        pending = await service.get_tasks_by_status("pending")
        
        assert len(pending) >= 1
        assert all(t.status == "pending" for t in pending)

    @pytest.mark.asyncio
    async def test_get_tasks_by_status_invalid(self, db_session: AsyncSession):
        """Test getting tasks with invalid status raises ValueError."""
        service = TaskService(db_session)
        
        with pytest.raises(ValueError, match="Invalid status"):
            await service.get_tasks_by_status("invalid")
