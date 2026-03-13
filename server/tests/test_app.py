"""Tests for FastAPI app endpoints."""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database.models import Base
from database import get_db_session
from services import UserService, ProjectService, TaskService


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def app(test_session: AsyncSession):
    """Create FastAPI app with test database override."""
    from app import app as fastapi_app
    from database import get_db_session
    
    # Override the database dependency to use test session
    async def override_get_db():
        yield test_session
    
    fastapi_app.dependency_overrides[get_db_session] = override_get_db
    
    yield fastapi_app
    
    # Clean up override
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession):
    """Create a test user."""
    service = UserService(test_session)
    user = await service.create_user(
        email="test@example.com",
        username="testuser",
        password="password123",
        full_name="Test User"
    )
    return user


@pytest_asyncio.fixture
async def test_project(test_session: AsyncSession, test_user):
    """Create a test project."""
    service = ProjectService(test_session)
    project = await service.create_project(
        name="Test Project",
        description="Test Description",
        owner_id=test_user.id
    )
    return project


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root_returns_info(self, client: AsyncClient):
        """Test root endpoint returns server info."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Claude Assistant Web Server"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check returns healthy status."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestUserEndpoints:
    """Tests for user API endpoints."""

    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient):
        """Test creating a user via API."""
        response = await client.post(
            "/users/",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, client: AsyncClient, test_user):
        """Test creating user with duplicate email fails."""
        response = await client.post(
            "/users/",
            json={
                "email": test_user.email,
                "username": "different",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_users(self, client: AsyncClient, test_user):
        """Test listing users."""
        response = await client.get("/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client: AsyncClient, test_user):
        """Test getting user by ID."""
        response = await client.get(f"/users/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient):
        """Test getting non-existent user returns 404."""
        response = await client.get("/users/99999")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, test_user):
        """Test updating user."""
        response = await client.put(
            f"/users/{test_user.id}",
            json={"full_name": "Updated Name"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, test_user):
        """Test deleting user."""
        response = await client.delete(f"/users/{test_user.id}")
        
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client: AsyncClient):
        """Test deleting non-existent user returns 404."""
        response = await client.delete("/users/99999")
        
        assert response.status_code == 404


class TestProjectEndpoints:
    """Tests for project API endpoints."""

    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient, test_user):
        """Test creating a project via API."""
        response = await client.post(
            "/projects/",
            json={
                "name": "New Project",
                "description": "Project Description",
                "owner_id": test_user.id
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["owner_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient, test_user):
        """Test listing projects."""
        # Create a project via API first
        await client.post(
            "/projects/",
            json={
                "name": "Test Project",
                "description": "Test Description",
                "owner_id": test_user.id
            }
        )
        
        response = await client.get(f"/projects/?owner_id={test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_project_by_id(self, client: AsyncClient, test_project):
        """Test getting project by ID."""
        response = await client.get(f"/projects/{test_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client: AsyncClient):
        """Test getting non-existent project returns 404."""
        response = await client.get("/projects/99999")
        
        assert response.status_code == 404


class TestTaskEndpoints:
    """Tests for task API endpoints."""

    @pytest.mark.asyncio
    async def test_create_task(self, client: AsyncClient, test_project):
        """Test creating a task via API."""
        response = await client.post(
            "/tasks/",
            json={
                "title": "New Task",
                "description": "Task Description",
                "project_id": test_project.id,
                "status": "pending",
                "priority": "normal"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["project_id"] == test_project.id

    @pytest.mark.asyncio
    async def test_list_tasks(self, client: AsyncClient, test_project):
        """Test listing tasks."""
        # Create a task via API first
        await client.post(
            "/tasks/",
            json={
                "title": "Test Task",
                "description": "Task Description",
                "project_id": test_project.id,
                "status": "pending",
                "priority": "normal"
            }
        )
        
        response = await client.get(f"/tasks/?project_id={test_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: AsyncClient):
        """Test getting non-existent task returns 404."""
        response = await client.get("/tasks/99999")
        
        assert response.status_code == 404


class TestDocsEndpoint:
    """Tests for API documentation endpoint."""

    @pytest.mark.asyncio
    async def test_docs_accessible(self, client: AsyncClient):
        """Test that API docs are accessible."""
        response = await client.get("/docs")
        
        assert response.status_code == 200
