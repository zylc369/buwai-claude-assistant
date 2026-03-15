"""Tests for AI Resources API endpoints."""

import pytest
import pytest_asyncio
import time
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database.models import Base, AiResource
from database import get_db_session


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
    from app import app as fastapi_app
    
    async def override_get_db():
        yield test_session
    
    fastapi_app.dependency_overrides[get_db_session] = override_get_db
    
    yield fastapi_app
    
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    from httpx import ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


class TestAIResourcesAPIList:
    """Tests for GET /ai-resources/ endpoint."""

    @pytest.mark.asyncio
    async def test_list_resources_empty(self, client: AsyncClient):
        response = await client.get("/ai-resources/?test=true")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_resources_with_data(self, client: AsyncClient, test_session: AsyncSession):
        now = int(time.time() * 1000)

        resource = AiResource(
            resource_unique_id="api-list-001",
            name="test-skill",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "test"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        test_session.add(resource)
        await test_session.commit()

        response = await client.get("/ai-resources/?test=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestAIResourcesAPICreate:
    """Tests for POST /ai-resources/ endpoint."""

    @pytest.mark.asyncio
    async def test_create_resource_success(self, client: AsyncClient):
        response = await client.post(
            "/ai-resources/?test=true",
            json={
                "resource_unique_id": "api-create-001",
                "name": "new-skill",
                "type": "SKILL",
                "sub_type": "",
                "owner": None,
                "disabled": False,
                "content": {"type": "MD", "data": "test content"},
                "test": True
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "new-skill"
        assert data["type"] == "SKILL"

    @pytest.mark.asyncio
    async def test_create_resource_with_owner(self, client: AsyncClient):
        response = await client.post(
            "/ai-resources/?test=true",
            json={
                "resource_unique_id": "api-create-002",
                "name": "owner-skill",
                "type": "COMMAND",
                "sub_type": "git",
                "owner": "workspace-123",
                "disabled": False,
                "content": {"type": "SHELL", "data": "echo hello"},
                "test": True
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["owner"] == "workspace-123"

    @pytest.mark.asyncio
    async def test_create_resource_invalid_type(self, client: AsyncClient):
        response = await client.post(
            "/ai-resources/?test=true",
            json={
                "resource_unique_id": "api-create-003",
                "name": "invalid-type",
                "type": "INVALID",
                "sub_type": "",
                "content": {"type": "MD", "data": "test"},
                "test": True
            }
        )
        assert response.status_code == 422


class TestAIResourcesAPIGet:
    """Tests for GET /ai-resources/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_resource_by_id_found(self, client: AsyncClient, test_session: AsyncSession):
        now = int(time.time() * 1000)

        resource = AiResource(
            resource_unique_id="api-get-001",
            name="get-test-skill",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "get test"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        test_session.add(resource)
        await test_session.commit()

        response = await client.get("/ai-resources/api-get-001?test=true")
        assert response.status_code == 200
        data = response.json()
        assert data["resource_unique_id"] == "api-get-001"

    @pytest.mark.asyncio
    async def test_get_resource_by_id_not_found(self, client: AsyncClient):
        response = await client.get("/ai-resources/nonexistent?test=true")
        assert response.status_code == 404


class TestAIResourcesAPIUpdate:
    """Tests for PUT /ai-resources/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_resource_success(self, client: AsyncClient, test_session: AsyncSession):
        now = int(time.time() * 1000)

        resource = AiResource(
            resource_unique_id="api-update-001",
            name="original-name",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "original"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        test_session.add(resource)
        await test_session.commit()

        response = await client.put(
            "/ai-resources/api-update-001?test=true",
            json={"name": "updated-name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-name"

    @pytest.mark.asyncio
    async def test_update_resource_toggle_disabled(self, client: AsyncClient, test_session: AsyncSession):
        now = int(time.time() * 1000)

        resource = AiResource(
            resource_unique_id="api-update-002",
            name="toggle-test",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "test"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        test_session.add(resource)
        await test_session.commit()

        response = await client.put(
            "/ai-resources/api-update-002?test=true",
            json={"disabled": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["disabled"] is True


class TestAIResourcesAPIDelete:
    """Tests for DELETE /ai-resources/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_resource_success(self, client: AsyncClient, test_session: AsyncSession):
        now = int(time.time() * 1000)

        resource = AiResource(
            resource_unique_id="api-delete-001",
            name="to-delete",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "delete me"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        test_session.add(resource)
        await test_session.commit()

        response = await client.delete("/ai-resources/api-delete-001?test=true")
        assert response.status_code == 204

        verify = await client.get("/ai-resources/api-delete-001?test=true")
        assert verify.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_resource_not_found(self, client: AsyncClient):
        response = await client.delete("/ai-resources/nonexistent?test=true")
        assert response.status_code == 404
