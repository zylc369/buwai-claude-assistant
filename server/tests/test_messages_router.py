"""Tests for Message API endpoints."""

import json
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi import FastAPI

from database.models import Base, Project, Workspace, Session, Message
from database import get_db_session
import importlib.util
import sys
from pathlib import Path
from utils.timestamp import get_timestamp_ms

spec = importlib.util.spec_from_file_location(
    "messages_router",
    Path(__file__).parent.parent / "routers" / "messages.py"
)
messages_module = importlib.util.module_from_spec(spec)
sys.modules["routers.messages"] = messages_module
spec.loader.exec_module(messages_module)
messages_router = messages_module.router


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
    fastapi_app = FastAPI()
    fastapi_app.include_router(messages_router)
    
    async def override_get_db():
        yield db_session
    
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
async def setup_test_data(db_session: AsyncSession):
    current_time = get_timestamp_ms()
    
    project = Project(
        project_unique_id="proj_msg_001",
        directory="test-path",
        branch="main",
        name="Test Project",
        gmt_create=current_time,
        gmt_modified=current_time
    )
    db_session.add(project)
    await db_session.flush()
    
    workspace = Workspace(
        workspace_unique_id="ws_msg_001",
        branch="main",
        directory="test-path",
        project_unique_id="proj_msg_001",
        gmt_create=current_time,
        gmt_modified=current_time
    )
    db_session.add(workspace)
    await db_session.flush()
    
    session = Session(
        session_unique_id="sess_msg_001",
        external_session_id="external-sess-msg-001",
        project_unique_id="proj_msg_001",
        workspace_unique_id="ws_msg_001",
        directory="test-path",
        title="Test Session",
        gmt_create=current_time,
        gmt_modified=current_time
    )
    db_session.add(session)
    await db_session.flush()
    
    return {
        "project": project,
        "workspace": workspace,
        "session": session
    }


@pytest_asyncio.fixture
async def test_message(db_session: AsyncSession, setup_test_data):
    current_time = get_timestamp_ms()
    
    message = Message(
        message_unique_id="msg_test_001",
        session_unique_id="sess_msg_001",
        gmt_create=current_time,
        gmt_modified=current_time,
        data=json.dumps({"role": "user", "content": "Hello test"})
    )
    db_session.add(message)
    await db_session.flush()
    
    return message


class TestListMessages:
    
    @pytest.mark.asyncio
    async def test_list_messages(self, client: AsyncClient, test_message):
        response = await client.get(
            "/messages/",
            params={"session_unique_id": "sess_msg_001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["message_unique_id"] == "msg_test_001"
    
    @pytest.mark.asyncio
    async def test_list_messages_empty(self, client: AsyncClient, db_session: AsyncSession, setup_test_data):
        current_time = get_timestamp_ms()
        
        new_session = Session(
            session_unique_id="sess_empty_msg",
            external_session_id="external-sess-empty-msg",
            project_unique_id="proj_msg_001",
            workspace_unique_id="ws_msg_001",
            directory="test-path",
            title="Empty Session",
            gmt_create=current_time,
            gmt_modified=current_time
        )
        db_session.add(new_session)
        await db_session.flush()
        
        response = await client.get(
            "/messages/",
            params={"session_unique_id": "sess_empty_msg"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_list_messages_with_pagination(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        setup_test_data
    ):
        current_time = get_timestamp_ms()
        
        for i in range(5):
            msg = Message(
                message_unique_id=f"msg_page_{i}",
                session_unique_id="sess_msg_001",
                gmt_create=current_time + i,
                gmt_modified=current_time + i,
                data=json.dumps({"role": "user", "content": f"Message {i}"})
            )
            db_session.add(msg)
        await db_session.flush()
        
        response = await client.get(
            "/messages/",
            params={
                "session_unique_id": "sess_msg_001",
                "offset": 0,
                "limit": 3
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestGetMessage:
    
    @pytest.mark.asyncio
    async def test_get_message_by_unique_id(self, client: AsyncClient, test_message):
        response = await client.get(f"/messages/{test_message.message_unique_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message_unique_id"] == test_message.message_unique_id
        assert data["session_unique_id"] == "sess_msg_001"
    
    @pytest.mark.asyncio
    async def test_get_message_not_found(self, client: AsyncClient):
        response = await client.get("/messages/non_existent_id")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Message not found"


class TestUpdateMessage:
    
    @pytest.mark.asyncio
    async def test_update_message(self, client: AsyncClient, test_message):
        response = await client.put(
            f"/messages/{test_message.message_unique_id}",
            json={"data": {"role": "assistant", "content": "Updated content"}}
        )
        
        assert response.status_code == 200
        data = response.json()
        parsed = json.loads(data["data"])
        assert parsed["content"] == "Updated content"
        assert parsed["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_update_message_not_found(self, client: AsyncClient):
        response = await client.put(
            "/messages/non_existent_id",
            json={"data": {"role": "user", "content": "Test"}}
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Message not found"


class TestDeleteMessage:
    
    @pytest.mark.asyncio
    async def test_delete_message(self, client: AsyncClient, test_message):
        response = await client.delete(f"/messages/{test_message.message_unique_id}")
        
        assert response.status_code == 204
        
        get_response = await client.get(f"/messages/{test_message.message_unique_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, client: AsyncClient):
        response = await client.delete("/messages/non_existent_id")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Message not found"


class TestSendAIPrompt:
    
    @pytest.mark.asyncio
    async def test_send_ai_prompt_returns_streaming_response(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        async def mock_send_ai_prompt(*args, **kwargs):
            yield "Hello"
            yield " "
            yield "World"
        
        with patch('services.message_service.MessageService.send_ai_prompt') as mock_send:
            mock_send.return_value = mock_send_ai_prompt()
            
            response = await client.post(
                "/messages/send",
                json={
                    "prompt": "Test prompt",
                    "session_unique_id": "sess_msg_001",
                    "cwd": "/tmp",
                    "settings": "/tmp/test_settings.json",
                    "system_prompt": "You are a test assistant"
                }
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            content = response.text
            assert "data:" in content
            assert '"type"' in content
            assert '"chunk"' in content
            assert '"done"' in content
    
    @pytest.mark.asyncio
    async def test_send_ai_prompt_with_error(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        async def mock_send_ai_prompt(*args, **kwargs):
            raise Exception("Connection error")
            yield  # pragma: no cover
        
        with patch('services.message_service.MessageService.send_ai_prompt') as mock_send:
            mock_send.return_value = mock_send_ai_prompt()
            
            response = await client.post(
                "/messages/send",
                json={
                    "prompt": "Test prompt",
                    "session_unique_id": "sess_msg_001",
                    "cwd": "/tmp",
                    "settings": "/tmp/test_settings.json"
                }
            )
            
            assert response.status_code == 200
            
            content = response.text
            assert "data:" in content
            assert '"type"' in content
            assert '"error"' in content
            assert "Connection error" in content
    
    @pytest.mark.asyncio
    async def test_send_ai_prompt_serializes_chunks_correctly(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        async def mock_send_ai_prompt(*args, **kwargs):
            yield {"text": "chunk1"}
            yield "plain_string"
            yield 123
        
        with patch('services.message_service.MessageService.send_ai_prompt') as mock_send:
            mock_send.return_value = mock_send_ai_prompt()
            
            response = await client.post(
                "/messages/send",
                json={
                    "prompt": "Test",
                    "session_unique_id": "sess_test_001",
                    "cwd": "/tmp",
                    "settings": "/tmp/test.json"
                }
            )
            
            assert response.status_code == 200
            content = response.text
            
            assert '"type"' in content
            assert '"chunk"' in content
            lines = [l for l in content.split('\n') if l.startswith('data:')]
            assert len(lines) >= 4


class TestSendAIPromptV2:
    """Tests for the /messages/send-v2 endpoint."""
    
    @pytest.mark.asyncio
    async def test_send_v2_new_session_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        setup_test_data
    ):
        """Test creating a new session and returning session_unique_id."""
        async def mock_send_ai_prompt(*args, **kwargs):
            yield "Hello"
            yield " "
            yield "World"
        
        with patch('services.message_service.MessageService.send_ai_prompt') as mock_send:
            mock_send.return_value = mock_send_ai_prompt()
            
            response = await client.post(
                "/messages/send-v2",
                json={
                    "prompt": "Test prompt for new session",
                    "session_unique_id": None,
                    "external_session_id": "ext-sess-new-001",
                    "project_unique_id": "proj_msg_001",
                    "workspace_unique_id": "ws_msg_001",
                    "directory": "test-path",
                    "cwd": "/tmp",
                    "settings": "/tmp/test_settings.json",
                    "system_prompt": "You are a test assistant"
                }
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            content = response.text
            
            assert "data:" in content
            assert '"type"' in content
            assert '"chunk"' in content
            assert '"done"' in content
            assert '"session_unique_id"' in content
            
            lines = [l for l in content.split('\n') if l.startswith('data:')]
            done_line = next((l for l in lines if '"done"' in l), None)
            assert done_line is not None
            done_data = json.loads(done_line.replace('data: ', ''))
            assert 'session_unique_id' in done_data
            assert done_data['session_unique_id'] is not None
    
    @pytest.mark.asyncio
    async def test_send_v2_existing_session_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        setup_test_data
    ):
        """Test using an existing session."""
        async def mock_send_ai_prompt(*args, **kwargs):
            yield "Response"
            yield " "
            yield "content"
        
        with patch('services.message_service.MessageService.send_ai_prompt') as mock_send:
            mock_send.return_value = mock_send_ai_prompt()
            
            response = await client.post(
                "/messages/send-v2",
                json={
                    "prompt": "Test prompt for existing session",
                    "session_unique_id": "sess_msg_001",
                    "external_session_id": "external-sess-msg-001",
                    "project_unique_id": "proj_msg_001",
                    "workspace_unique_id": "ws_msg_001",
                    "directory": "test-path",
                    "cwd": "/tmp",
                    "settings": "/tmp/test_settings.json",
                    "system_prompt": "You are a test assistant"
                }
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            content = response.text
            
            assert "data:" in content
            assert '"type"' in content
            assert '"done"' in content
            
            lines = [l for l in content.split('\n') if l.startswith('data:')]
            done_line = next((l for l in lines if '"done"' in l), None)
            assert done_line is not None
            done_data = json.loads(done_line.replace('data: ', ''))
            assert done_data['session_unique_id'] == "sess_msg_001"
    
    @pytest.mark.asyncio
    async def test_send_v2_invalid_workspace(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test returns 400 if workspace doesn't exist."""
        async def mock_send_ai_prompt(*args, **kwargs):
            yield "Should not be called"
        
        with patch('services.message_service.MessageService.send_ai_prompt') as mock_send:
            mock_send.return_value = mock_send_ai_prompt()
            
            response = await client.post(
                "/messages/send-v2",
                json={
                    "prompt": "Test prompt",
                    "session_unique_id": None,
                    "external_session_id": "ext-sess-ws-001",
                    "project_unique_id": "proj_msg_001",
                    "workspace_unique_id": "non_existent_workspace",
                    "directory": "test-path",
                    "cwd": "/tmp",
                    "settings": "/tmp/test_settings.json",
                    "system_prompt": "You are a test assistant"
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Workspace not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_send_v2_duplicate_external_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        setup_test_data
    ):
        """Test returns 400 if external_session_id already exists."""
        async def mock_send_ai_prompt(*args, **kwargs):
            yield "Should not be called"
        
        with patch('services.message_service.MessageService.send_ai_prompt') as mock_send:
            mock_send.return_value = mock_send_ai_prompt()
            
            response = await client.post(
                "/messages/send-v2",
                json={
                    "prompt": "Test prompt with duplicate external id",
                    "session_unique_id": None,
                    "external_session_id": "external-sess-msg-001",
                    "project_unique_id": "proj_msg_001",
                    "workspace_unique_id": "ws_msg_001",
                    "directory": "test-path",
                    "cwd": "/tmp",
                    "settings": "/tmp/test_settings.json",
                    "system_prompt": "You are a test assistant"
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "already exists" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_send_v2_sse_streaming(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        setup_test_data
    ):
        """Test verifies SSE response format with session_unique_id in done event."""
        async def mock_send_ai_prompt(*args, **kwargs):
            yield {"text": "chunk1"}
            yield "plain_string"
            yield {"content": "final chunk"}
        
        with patch('services.message_service.MessageService.send_ai_prompt') as mock_send:
            mock_send.return_value = mock_send_ai_prompt()
            
            response = await client.post(
                "/messages/send-v2",
                json={
                    "prompt": "Test SSE streaming",
                    "session_unique_id": "sess_msg_001",
                    "external_session_id": "external-sess-msg-001",
                    "project_unique_id": "proj_msg_001",
                    "workspace_unique_id": "ws_msg_001",
                    "directory": "test-path",
                    "cwd": "/tmp",
                    "settings": "/tmp/test.json"
                }
            )
            
            assert response.status_code == 200
            content = response.text
            
            assert "data:" in content
            assert '"type"' in content
            
            lines = [l for l in content.split('\n') if l.strip() and l.startswith('data:')]
            assert len(lines) >= 2
            
            chunk_lines = [l for l in lines if '"chunk"' in l]
            assert len(chunk_lines) >= 3
            
            done_lines = [l for l in lines if '"done"' in l]
            assert len(done_lines) == 1
            
            done_data = json.loads(done_lines[0].replace('data: ', ''))
            assert done_data["type"] == "done"
            assert "session_unique_id" in done_data
            assert done_data["session_unique_id"] == "sess_msg_001"
            
            error_lines = [l for l in lines if '"error"' in l]
            assert len(error_lines) == 0
    
    @pytest.mark.asyncio
    async def test_send_v2_nonexistent_session_returns_404(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test returns 404 if session_unique_id is provided but session doesn't exist."""
        async def mock_send_ai_prompt(*args, **kwargs):
            yield "Should not be called"
        
        with patch('services.message_service.MessageService.send_ai_prompt') as mock_send:
            mock_send.return_value = mock_send_ai_prompt()
            
            response = await client.post(
                "/messages/send-v2",
                json={
                    "prompt": "Test prompt",
                    "session_unique_id": "non_existent_session_id",
                    "external_session_id": "ext-sess-404",
                    "project_unique_id": "proj_msg_001",
                    "workspace_unique_id": "ws_msg_001",
                    "directory": "test-path",
                    "cwd": "/tmp",
                    "settings": "/tmp/test_settings.json",
                    "system_prompt": "You are a test assistant"
                }
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "Session not found" in data["detail"]
