"""Tests for Workspace API endpoints."""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database.models import Base, Project, Workspace
from database import get_db_session

import sys
import importlib.util
spec = importlib.util.spec_from_file_location("workspaces_router", "routers/workspaces.py")
workspaces_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspaces_module)
workspaces_router = workspaces_module.router


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
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
    fastapi_app = FastAPI()
    fastapi_app.include_router(workspaces_router)
    
    async def override_get_db():
        yield test_session
    
    fastapi_app.dependency_overrides[get_db_session] = override_get_db
    
    yield fastapi_app
    
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_project(test_session: AsyncSession):
    project = Project(
        project_unique_id="proj-router-001",
        worktree="/path/to/worktree",
        branch="main",
        name="Router Test Project",
        time_created=1000000,
        time_updated=1000000
    )
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_project2(test_session: AsyncSession):
    project = Project(
        project_unique_id="proj-router-002",
        worktree="/path/to/worktree2",
        branch="develop",
        name="Router Test Project 2",
        time_created=1000000,
        time_updated=1000000
    )
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_workspace(test_session: AsyncSession, test_project: Project):
    workspace = Workspace(
        workspace_unique_id="ws-router-001",
        project_unique_id=test_project.project_unique_id,
        name="Router Test Workspace",
        branch="feature/test",
        directory="/path/to/workspace"
    )
    test_session.add(workspace)
    await test_session.commit()
    await test_session.refresh(workspace)
    return workspace


class TestCreateWorkspace:

    @pytest.mark.asyncio
    async def test_create_workspace_minimal(
        self, client: AsyncClient, test_project: Project
    ):
        response = await client.post(
            "/workspaces/",
            json={
                "workspace_unique_id": "ws-new-001",
                "project_unique_id": test_project.project_unique_id
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["workspace_unique_id"] == "ws-new-001"
        assert data["project_unique_id"] == test_project.project_unique_id

    @pytest.mark.asyncio
    async def test_create_workspace_with_all_fields(
        self, client: AsyncClient, test_project: Project
    ):
        response = await client.post(
            "/workspaces/",
            json={
                "workspace_unique_id": "ws-new-002",
                "project_unique_id": test_project.project_unique_id,
                "name": "Development Workspace",
                "branch": "feature/test",
                "directory": "/path/to/workspace",
                "extra": '{"key": "value"}'
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["workspace_unique_id"] == "ws-new-002"
        assert data["name"] == "Development Workspace"
        assert data["branch"] == "feature/test"
        assert data["directory"] == "/path/to/workspace"
        assert data["extra"] == '{"key": "value"}'


class TestListWorkspaces:

    @pytest.mark.asyncio
    async def test_list_workspaces(
        self, client: AsyncClient, test_project: Project, test_workspace: Workspace
    ):
        response = await client.get(
            "/workspaces/",
            params={"project_unique_id": test_project.project_unique_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_workspaces_empty(
        self, client: AsyncClient, test_project2: Project
    ):
        response = await client.get(
            "/workspaces/",
            params={"project_unique_id": test_project2.project_unique_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_workspaces_filters_by_project(
        self,
        client: AsyncClient,
        test_project: Project,
        test_project2: Project,
        test_workspace: Workspace
    ):
        await client.post(
            "/workspaces/",
            json={
                "workspace_unique_id": "ws-filter-001",
                "project_unique_id": test_project2.project_unique_id,
                "name": "Other Workspace"
            }
        )
        
        response = await client.get(
            "/workspaces/",
            params={"project_unique_id": test_project.project_unique_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(ws["project_unique_id"] == test_project.project_unique_id for ws in data)

    @pytest.mark.asyncio
    async def test_list_workspaces_pagination(
        self, client: AsyncClient, test_project: Project
    ):
        for i in range(5):
            await client.post(
                "/workspaces/",
                json={
                    "workspace_unique_id": f"ws-page-{i:03d}",
                    "project_unique_id": test_project.project_unique_id,
                    "name": f"Workspace {i}"
                }
            )
        
        response1 = await client.get(
            "/workspaces/",
            params={
                "project_unique_id": test_project.project_unique_id,
                "offset": 0,
                "limit": 2
            }
        )
        response2 = await client.get(
            "/workspaces/",
            params={
                "project_unique_id": test_project.project_unique_id,
                "offset": 2,
                "limit": 2
            }
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(response1.json()) == 2
        assert len(response2.json()) == 2


class TestGetWorkspace:

    @pytest.mark.asyncio
    async def test_get_workspace_by_unique_id(
        self, client: AsyncClient, test_workspace: Workspace
    ):
        response = await client.get(f"/workspaces/{test_workspace.workspace_unique_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_unique_id"] == test_workspace.workspace_unique_id
        assert data["name"] == test_workspace.name

    @pytest.mark.asyncio
    async def test_get_workspace_not_found(self, client: AsyncClient):
        response = await client.get("/workspaces/non-existent-ws")
        
        assert response.status_code == 404


class TestUpdateWorkspace:

    @pytest.mark.asyncio
    async def test_update_workspace(
        self, client: AsyncClient, test_workspace: Workspace
    ):
        response = await client.put(
            f"/workspaces/{test_workspace.workspace_unique_id}",
            json={
                "name": "Updated Workspace Name",
                "branch": "updated-branch"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Workspace Name"
        assert data["branch"] == "updated-branch"

    @pytest.mark.asyncio
    async def test_update_workspace_not_found(self, client: AsyncClient):
        response = await client.put(
            "/workspaces/non-existent-ws",
            json={"name": "New Name"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_workspace_partial(
        self, client: AsyncClient, test_workspace: Workspace
    ):
        original_branch = test_workspace.branch
        
        response = await client.put(
            f"/workspaces/{test_workspace.workspace_unique_id}",
            json={"name": "Only Name Updated"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Only Name Updated"
        assert data["branch"] == original_branch


class TestDeleteWorkspace:

    @pytest.mark.asyncio
    async def test_delete_workspace(
        self, client: AsyncClient, test_project: Project
    ):
        create_response = await client.post(
            "/workspaces/",
            json={
                "workspace_unique_id": "ws-to-delete",
                "project_unique_id": test_project.project_unique_id,
                "name": "Workspace to Delete"
            }
        )
        assert create_response.status_code == 201
        
        delete_response = await client.delete("/workspaces/ws-to-delete")
        
        assert delete_response.status_code == 204
        
        get_response = await client.get("/workspaces/ws-to-delete")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_workspace_not_found(self, client: AsyncClient):
        response = await client.delete("/workspaces/non-existent-ws")
        
        assert response.status_code == 404
