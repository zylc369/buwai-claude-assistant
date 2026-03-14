"""Tests for SSEService."""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from services.sse_service import SSEService, SSEEventType
from claude_client import ClaudeClientConfig


class TestSSEEventType:
    def test_event_type_values(self):
        assert SSEEventType.MESSAGE.value == "message"
        assert SSEEventType.ERROR.value == "error"
        assert SSEEventType.DONE.value == "done"
        assert SSEEventType.TOOL_USE.value == "tool_use"
        assert SSEEventType.THINKING.value == "thinking"
        assert SSEEventType.CONNECTED.value == "connected"
        assert SSEEventType.DISCONNECTED.value == "disconnected"
        assert SSEEventType.HEARTBEAT.value == "heartbeat"


class TestSSEServiceWithoutDB:
    def test_send_event_basic(self):
        service = SSEService(db=None)
        
        result = service.send_event("message", {"text": "Hello"})
        
        assert "event: message" in result
        assert '"text": "Hello"' in result
        assert result.endswith("\n\n")
    
    def test_send_event_with_id(self):
        service = SSEService(db=None)
        
        result = service.send_event("message", {"text": "Test"}, event_id="evt_123")
        
        assert "id: evt_123" in result
        assert "event: message" in result
    
    def test_send_event_with_retry(self):
        service = SSEService(db=None)
        
        result = service.send_event("message", {"text": "Test"}, retry=5000)
        
        assert "retry: 5000" in result
        assert "event: message" in result
    
    def test_send_event_string_data(self):
        service = SSEService(db=None)
        
        result = service.send_event("message", "plain text")
        
        assert "data: plain text" in result
    
    def test_send_event_multiline_string(self):
        service = SSEService(db=None)
        
        result = service.send_event("message", "line1\nline2")
        
        assert "data: line1" in result
        assert "data: line2" in result
    
    def test_complete_stream(self):
        service = SSEService(db=None)
        
        result = service.complete_stream()
        
        assert "event: done" in result
        assert '"status": "complete"' in result
    
    def test_response_to_sse_text_block(self):
        service = SSEService(db=None)
        
        mock_response = MagicMock()
        mock_response.type = "text"
        mock_response.text = "Hello world"
        
        result = service._response_to_sse(mock_response)
        
        assert "event: message" in result
        assert '"text": "Hello world"' in result
    
    def test_response_to_sse_tool_use(self):
        service = SSEService(db=None)
        
        mock_response = MagicMock()
        mock_response.type = "tool_use"
        mock_response.name = "read_file"
        mock_response.input = {"path": "/test.py"}
        
        result = service._response_to_sse(mock_response)
        
        assert "event: tool_use" in result
        assert '"name": "read_file"' in result
        assert '"path": "/test.py"' in result
    
    def test_response_to_sse_thinking(self):
        service = SSEService(db=None)
        
        mock_response = MagicMock()
        mock_response.type = "thinking"
        mock_response.thinking = "Let me analyze this..."
        
        result = service._response_to_sse(mock_response)
        
        assert "event: thinking" in result
        assert '"thinking": "Let me analyze this..."' in result
    
    def test_response_to_sse_fallback_string(self):
        service = SSEService(db=None)
        
        result = service._response_to_sse("plain string")
        
        assert "event: message" in result
        assert '"text": "plain string"' in result
    
    def test_response_to_sse_fallback_no_type(self):
        service = SSEService(db=None)
        
        mock_response = MagicMock(spec=[])
        
        result = service._response_to_sse(mock_response)
        
        assert "event: message" in result
    
    def test_error_to_sse(self):
        service = SSEService(db=None)
        
        result = service._error_to_sse("Connection failed")
        
        assert "event: error" in result
        assert '"error": "Connection failed"' in result


class TestSSEServiceWrapAIResponse:
    @pytest.mark.asyncio
    async def test_wrap_ai_response_yields_sse_events(self):
        service = SSEService(db=None)
        
        async def mock_iterator():
            yield MagicMock(type="text", text="Hello")
            yield MagicMock(type="text", text=" World")
        
        results = []
        async for event in service.wrap_ai_response(mock_iterator()):
            results.append(event)
        
        assert len(results) == 3
        assert "event: message" in results[0]
        assert "Hello" in results[0]
        assert "event: message" in results[1]
        assert "World" in results[1]
        assert "event: done" in results[2]
    
    @pytest.mark.asyncio
    async def test_wrap_ai_response_handles_error(self):
        service = SSEService(db=None)
        
        async def mock_iterator():
            yield MagicMock(type="text", text="Hello")
            raise Exception("Stream error")
        
        results = []
        async for event in service.wrap_ai_response(mock_iterator()):
            results.append(event)
        
        assert len(results) == 2
        assert "event: message" in results[0]
        assert "event: error" in results[1]
        assert "Stream error" in results[1]


class TestSSEServiceCreateStream:
    @pytest.mark.asyncio
    async def test_create_stream_without_pool(self):
        service = SSEService(db=None)
        
        mock_client = AsyncMock()
        mock_client.query = AsyncMock()
        
        async def mock_receive_response_gen():
            yield MagicMock(type="text", text="AI response")
        
        async def mock_receive_response():
            return mock_receive_response_gen()
        
        mock_client.receive_response = AsyncMock(side_effect=mock_receive_response)
        
        config = ClaudeClientConfig(
            cwd="/test",
            settings="/tmp/test_settings.json"
        )
        
        with patch('services.sse_service.ClaudeClient') as MockClaudeClient:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            MockClaudeClient.return_value = mock_context
            
            results = []
            async for event in service.create_stream(
                prompt="Hello",
                session_unique_id="session_123",
                client_config=config
            ):
                results.append(event)
            
            assert len(results) == 2
            assert "event: message" in results[0]
            assert "event: done" in results[1]
            mock_client.query.assert_called_once_with("Hello", "session_123")
    
    @pytest.mark.asyncio
    async def test_create_stream_with_pool(self):
        service = SSEService(db=None)
        
        mock_client = AsyncMock()
        mock_client.query = AsyncMock()
        
        async def mock_receive_response_gen():
            yield MagicMock(type="text", text="Pooled response")
        
        async def mock_receive_response():
            return mock_receive_response_gen()
        
        mock_client.receive_response = AsyncMock(side_effect=mock_receive_response)
        
        mock_pool = AsyncMock()
        mock_pool.get_client = AsyncMock(return_value=mock_client)
        mock_pool.release_client = AsyncMock()
        
        config = ClaudeClientConfig(
            cwd="/test",
            settings="/tmp/test_settings.json"
        )
        
        results = []
        async for event in service.create_stream(
            prompt="Test prompt",
            session_unique_id="session_pool",
            client_config=config,
            pool=mock_pool
        ):
            results.append(event)
        
        assert len(results) == 2
        assert "event: message" in results[0]
        assert "event: done" in results[1]
        mock_pool.get_client.assert_called_once_with("session_pool", config)
        mock_client.query.assert_called_once_with("Test prompt", "session_pool")
        mock_pool.release_client.assert_called_once_with("session_pool")
    
    @pytest.mark.asyncio
    async def test_create_stream_pool_releases_on_error(self):
        service = SSEService(db=None)
        
        mock_client = AsyncMock()
        mock_client.query = AsyncMock(side_effect=Exception("Connection error"))
        
        mock_pool = AsyncMock()
        mock_pool.get_client = AsyncMock(return_value=mock_client)
        mock_pool.release_client = AsyncMock()
        
        config = ClaudeClientConfig(
            cwd="/test",
            settings="/tmp/test_settings.json"
        )
        
        results = []
        async for event in service.create_stream(
            prompt="Error test",
            session_unique_id="session_error",
            client_config=config,
            pool=mock_pool
        ):
            results.append(event)
        
        assert len(results) == 1
        assert "event: error" in results[0]
        assert "Connection error" in results[0]
        mock_pool.release_client.assert_called_once_with("session_error")


class TestSSEServiceFormatEvent:
    def test_format_event_basic(self):
        service = SSEService(db=None)
        
        result = service._format_event("test", {"key": "value"})
        
        assert result == 'event: test\ndata: {"key": "value"}\n\n'
    
    def test_format_event_with_special_chars(self):
        service = SSEService(db=None)
        
        result = service._format_event("message", {"text": "Hello 世界"})
        
        assert "世界" in result


class TestSSEServiceWithDatabase:
    @pytest_asyncio.fixture
    async def setup_session_data(self, db_session: AsyncSession):
        from database.models import Project, Workspace, Session
        import time
        
        project = Project(
            project_unique_id="proj_sse_001",
            directory="/test/path",
            branch="main",
            name="Test Project",
            gmt_create=int(time.time()),
            gmt_modified=int(time.time())
        )
        db_session.add(project)
        await db_session.flush()
        
        workspace = Workspace(
            workspace_unique_id="ws_sse_001",
            branch="main",
            name="Test Workspace",
            directory="/test/path",
            project_unique_id="proj_sse_001",
            gmt_create=int(time.time()),
            gmt_modified=int(time.time())
        )
        db_session.add(workspace)
        await db_session.flush()
        
        session = Session(
            session_unique_id="sess_sse_001",
            external_session_id="external-sess-sse-001",
            project_unique_id="proj_sse_001",
            workspace_unique_id="ws_sse_001",
            directory="/test/path",
            title="Test Session",
            gmt_create=int(time.time()),
            gmt_modified=int(time.time())
        )
        db_session.add(session)
        await db_session.flush()
        
        return {
            "project": project,
            "workspace": workspace,
            "session": session
        }
    
    @pytest.mark.asyncio
    async def test_get_session_stream_session_not_found(self, db_session: AsyncSession):
        service = SSEService(db_session)
        
        results = []
        async for event in service.get_session_stream("nonexistent"):
            results.append(event)
        
        assert len(results) == 1
        assert "event: error" in results[0]
        assert "not found" in results[0]
    
    @pytest.mark.asyncio
    async def test_get_session_stream_sends_connected(self, db_session: AsyncSession, setup_session_data):
        service = SSEService(db_session)
        
        results = []
        async for event in service.get_session_stream("sess_sse_001"):
            results.append(event)
            if len(results) >= 1:
                break
        
        assert len(results) >= 1
        assert "event: connected" in results[0]
        assert "sess_sse_001" in results[0]
    
    @pytest.mark.asyncio
    async def test_push_event_to_active_stream(self, db_session: AsyncSession, setup_session_data):
        service = SSEService(db_session)
        
        stream_ready = asyncio.Event()
        
        async def start_stream():
            async for event in service.get_session_stream("sess_sse_001"):
                stream_ready.set()
                break
        
        task = asyncio.create_task(start_stream())
        
        try:
            await asyncio.wait_for(stream_ready.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            task.cancel()
            raise
        
        pushed = await service.push_event(
            session_unique_id="sess_sse_001",
            event_type="test_event",
            data={"message": "pushed"}
        )
        
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        assert pushed is True
    
    @pytest.mark.asyncio
    async def test_push_event_no_active_stream(self, db_session: AsyncSession):
        service = SSEService(db_session)
        
        pushed = await service.push_event(
            session_unique_id="no_stream_session",
            event_type="test",
            data={"message": "test"}
        )
        
        assert pushed is False
