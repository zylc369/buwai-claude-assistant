"""Tests for Conversation Session API endpoints."""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database.models import Base, Project, Workspace, Session, Message
from database import get_db_session
from services import ConversationSessionService
from routers.sessions import router as sessions_router


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
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    SessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with SessionLocal() as session:
        yield session


@pytest.fixture
def app(db_session: AsyncSession):
    test_app = FastAPI()
    
    async def override_get_db():
        yield db_session
    
    test_app.dependency_overrides[get_db_session] = override_get_db
    test_app.include_router(sessions_router)
    
    yield test_app
    
    test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession):
    project = Project(
        project_unique_id="proj-test-001",
        directory="/test/worktree",
        name="Test Project",
        gmt_create=1000,
        gmt_modified=1000,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_workspace(db_session: AsyncSession, test_project: Project):
    workspace = Workspace(
        workspace_unique_id="ws-test-001",
        project_unique_id=test_project.project_unique_id,
        name="Test Workspace",
        directory="/test/dir",
        gmt_create=1000,
        gmt_modified=1000,
    )
    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)
    return workspace


@pytest_asyncio.fixture
async def test_conversation_session(db_session: AsyncSession, test_project: Project, test_workspace: Workspace):
    session = Session(
        session_unique_id="sess-test-001",
        external_session_id="external-sess-test-001",
        project_unique_id=test_project.project_unique_id,
        workspace_unique_id=test_workspace.workspace_unique_id,
        directory="/test/dir",
        title="Test Session",
        gmt_create=1000,
        gmt_modified=1000,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


class TestCreateSession:
    
    @pytest.mark.asyncio
    async def test_create_session(
        self,
        client: AsyncClient,
        test_project: Project,
        test_workspace: Workspace
    ):
        response = await client.post(
            "/sessions/",
            json={
                "session_unique_id": "sess-new-001",
                "external_session_id": "external-sess-new-001",
                "project_unique_id": test_project.project_unique_id,
                "workspace_unique_id": test_workspace.workspace_unique_id,
                "directory": "/test/dir",
                "title": "New Session",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["session_unique_id"] == "sess-new-001"
        assert data["title"] == "New Session"
        assert data["project_unique_id"] == test_project.project_unique_id
        assert data["workspace_unique_id"] == test_workspace.workspace_unique_id
    
    @pytest.mark.asyncio
    async def test_create_session_auto_timestamps(
        self,
        client: AsyncClient,
        test_project: Project,
        test_workspace: Workspace
    ):
        response = await client.post(
            "/sessions/",
            json={
                "session_unique_id": "sess-ts-001",
                "external_session_id": "external-sess-ts-001",
                "project_unique_id": test_project.project_unique_id,
                "workspace_unique_id": test_workspace.workspace_unique_id,
                "directory": "/test/dir",
                "title": "Timestamp Test",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["gmt_create"] is not None
        assert data["gmt_modified"] is not None


class TestListSessions:
    
    @pytest.mark.asyncio
    async def test_list_sessions(
        self,
        client: AsyncClient,
        test_project: Project,
        test_workspace: Workspace,
        test_conversation_session: Session
    ):
        response = await client.get(
            "/sessions/",
            params={
                "project_unique_id": test_project.project_unique_id,
                "workspace_unique_id": test_workspace.workspace_unique_id,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    @pytest.mark.asyncio
    async def test_list_sessions_excludes_archived_by_default(
        self,
        client: AsyncClient,
        test_project: Project,
        test_workspace: Workspace,
        db_session: AsyncSession
    ):
        archived_session = Session(
            session_unique_id="sess-archived-001",
            external_session_id="external-sess-archived-001",
            project_unique_id=test_project.project_unique_id,
            workspace_unique_id=test_workspace.workspace_unique_id,
            directory="/test/dir",
            title="Archived Session",
            gmt_create=1000,
            gmt_modified=1000,
            time_archived=2000,
        )
        db_session.add(archived_session)
        await db_session.commit()
        
        response = await client.get(
            "/sessions/",
            params={
                "project_unique_id": test_project.project_unique_id,
                "workspace_unique_id": test_workspace.workspace_unique_id,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        session_ids = [s["session_unique_id"] for s in data]
        assert "sess-archived-001" not in session_ids
    
    @pytest.mark.asyncio
    async def test_list_sessions_include_archived(
        self,
        client: AsyncClient,
        test_project: Project,
        test_workspace: Workspace,
        db_session: AsyncSession
    ):
        archived_session = Session(
            session_unique_id="sess-archived-002",
            external_session_id="external-sess-archived-002",
            project_unique_id=test_project.project_unique_id,
            workspace_unique_id=test_workspace.workspace_unique_id,
            directory="/test/dir",
            title="Archived Session 2",
            gmt_create=1000,
            gmt_modified=1000,
            time_archived=2000,
        )
        db_session.add(archived_session)
        await db_session.commit()
        
        response = await client.get(
            "/sessions/",
            params={
                "project_unique_id": test_project.project_unique_id,
                "workspace_unique_id": test_workspace.workspace_unique_id,
                "include_archived": True,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        session_ids = [s["session_unique_id"] for s in data]
        assert "sess-archived-002" in session_ids


class TestGetSession:
    
    @pytest.mark.asyncio
    async def test_get_session_by_unique_id(
        self,
        client: AsyncClient,
        test_conversation_session: Session
    ):
        response = await client.get(f"/sessions/{test_conversation_session.session_unique_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_unique_id"] == test_conversation_session.session_unique_id
        assert data["title"] == test_conversation_session.title
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client: AsyncClient):
        response = await client.get("/sessions/non-existent-id")
        
        assert response.status_code == 404


class TestUpdateSession:
    
    @pytest.mark.asyncio
    async def test_update_session_title(
        self,
        client: AsyncClient,
        test_conversation_session: Session
    ):
        response = await client.put(
            f"/sessions/{test_conversation_session.session_unique_id}",
            json={"title": "Updated Title"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    
    @pytest.mark.asyncio
    async def test_update_session_auto_gmt_modified(
        self,
        client: AsyncClient,
        test_conversation_session: Session
    ):
        original_time = test_conversation_session.gmt_modified

        response = await client.put(
            f"/sessions/{test_conversation_session.session_unique_id}",
            json={"title": "New Title"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["gmt_modified"] >= original_time
    
    @pytest.mark.asyncio
    async def test_update_session_not_found(self, client: AsyncClient):
        response = await client.put(
            "/sessions/non-existent-id",
            json={"title": "New Title"}
        )
        
        assert response.status_code == 404


class TestDeleteSession:
    
    @pytest.mark.asyncio
    async def test_delete_session(
        self,
        client: AsyncClient,
        test_conversation_session: Session
    ):
        response = await client.delete(f"/sessions/{test_conversation_session.session_unique_id}")
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, client: AsyncClient):
        response = await client.delete("/sessions/non-existent-id")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_session_cascades_to_messages(
        self,
        client: AsyncClient,
        test_conversation_session: Session,
        db_session: AsyncSession
    ):
        message = Message(
            message_unique_id="msg-cascade-001",
            session_unique_id=test_conversation_session.session_unique_id,
            gmt_create=1000,
            gmt_modified=1000,
            data='{"content": "test"}',
        )
        db_session.add(message)
        await db_session.commit()
        
        response = await client.delete(f"/sessions/{test_conversation_session.session_unique_id}")
        assert response.status_code == 204
        
        from sqlalchemy import select
        result = await db_session.execute(
            select(Message).where(Message.message_unique_id == "msg-cascade-001")
        )
        assert result.scalar_one_or_none() is None


class TestArchiveSession:
    
    @pytest.mark.asyncio
    async def test_archive_session(
        self,
        client: AsyncClient,
        test_conversation_session: Session
    ):
        assert test_conversation_session.time_archived is None
        
        response = await client.post(
            f"/sessions/{test_conversation_session.session_unique_id}/archive"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["time_archived"] is not None
    
    @pytest.mark.asyncio
    async def test_archive_session_not_found(self, client: AsyncClient):
        response = await client.post("/sessions/non-existent-id/archive")
        
        assert response.status_code == 404


class TestUnarchiveSession:
    
    @pytest.mark.asyncio
    async def test_unarchive_session(
        self,
        client: AsyncClient,
        test_project: Project,
        test_workspace: Workspace,
        db_session: AsyncSession
    ):
        archived_session = Session(
            session_unique_id="sess-unarchive-001",
            external_session_id="external-sess-unarchive-001",
            project_unique_id=test_project.project_unique_id,
            workspace_unique_id=test_workspace.workspace_unique_id,
            directory="/test/dir",
            title="Archived Session",
            gmt_create=1000,
            gmt_modified=1000,
            time_archived=2000,
        )
        db_session.add(archived_session)
        await db_session.commit()
        await db_session.refresh(archived_session)
        
        response = await client.post(
            f"/sessions/{archived_session.session_unique_id}/unarchive"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["time_archived"] is None
    
    @pytest.mark.asyncio
    async def test_unarchive_session_not_found(self, client: AsyncClient):
        response = await client.post("/sessions/non-existent-id/unarchive")
        
        assert response.status_code == 404


class TestGetSessionsByExternalSessionId:
    
    @pytest.mark.asyncio
    async def test_get_sessions_by_external_session_id(
        self,
        client: AsyncClient,
        test_project: Project,
        test_workspace: Workspace,
        db_session: AsyncSession
    ):
        session = Session(
            session_unique_id="sess-ext-filter-001",
            external_session_id="ext-session-unique-123",
            project_unique_id=test_project.project_unique_id,
            workspace_unique_id=test_workspace.workspace_unique_id,
            directory="/test/dir",
            title="External Filter Session",
            gmt_create=1000,
            gmt_modified=1000,
        )
        db_session.add(session)
        await db_session.commit()

        other_session = Session(
            session_unique_id="sess-ext-filter-002",
            external_session_id="ext-session-other-456",
            project_unique_id=test_project.project_unique_id,
            workspace_unique_id=test_workspace.workspace_unique_id,
            directory="/test/dir",
            title="Other Session",
            gmt_create=1000,
            gmt_modified=1000,
        )
        db_session.add(other_session)
        await db_session.commit()
        
        response = await client.get(
            "/sessions/",
            params={"external_session_id": "ext-session-unique-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["external_session_id"] == "ext-session-unique-123"
        assert data[0]["session_unique_id"] == "sess-ext-filter-001"
    
    @pytest.mark.asyncio
    async def test_get_sessions_by_external_session_id_not_found(
        self,
        client: AsyncClient
    ):
        response = await client.get(
            "/sessions/",
            params={"external_session_id": "non-existent-external-id"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestSessionResponseFields:
    
    @pytest.mark.asyncio
    async def test_session_response_includes_external_session_id(
        self,
        client: AsyncClient,
        test_conversation_session: Session
    ):
        response = await client.get(
            f"/sessions/{test_conversation_session.session_unique_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "external_session_id" in data
        assert data["external_session_id"] == test_conversation_session.external_session_id
    
    @pytest.mark.asyncio
    async def test_session_response_includes_sdk_session_id(
        self,
        client: AsyncClient,
        test_project: Project,
        test_workspace: Workspace,
        db_session: AsyncSession
    ):
        session = Session(
            session_unique_id="sess-sdk-response-001",
            external_session_id="ext-sess-sdk-response-001",
            sdk_session_id="sdk-session-abc123",
            project_unique_id=test_project.project_unique_id,
            workspace_unique_id=test_workspace.workspace_unique_id,
            directory="/test/dir",
            title="SDK Session Response",
            gmt_create=1000,
            gmt_modified=1000,
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        response = await client.get(
            f"/sessions/{session.session_unique_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sdk_session_id" in data
        assert data["sdk_session_id"] == "sdk-session-abc123"
    
    @pytest.mark.asyncio
    async def test_session_response_sdk_session_id_null_when_not_set(
        self,
        client: AsyncClient,
        test_conversation_session: Session
    ):
        response = await client.get(
            f"/sessions/{test_conversation_session.session_unique_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sdk_session_id" in data
        assert data["sdk_session_id"] is None
