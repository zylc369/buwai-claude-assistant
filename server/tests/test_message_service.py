"""Tests for MessageService."""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project, Workspace, Session, Message
from services.message_service import MessageService
from claude_client import ClaudeClientConfig
from utils.timestamp import get_timestamp_ms


@pytest_asyncio.fixture
async def setup_test_data(db_session: AsyncSession):
    project = Project(
        project_unique_id="proj_svc_001",
        directory="test-path",
        branch="main",
        name="Test Project",
        gmt_create=get_timestamp_ms(),
        gmt_modified=get_timestamp_ms()
    )
    db_session.add(project)
    await db_session.flush()
    
    workspace = Workspace(
        workspace_unique_id="ws_svc_001",
        branch="main",
        directory="test-path",
        project_unique_id="proj_svc_001",
        gmt_create=get_timestamp_ms(),
        gmt_modified=get_timestamp_ms()
    )
    db_session.add(workspace)
    await db_session.flush()
    
    session = Session(
        session_unique_id="sess_svc_001",
        external_session_id="external-sess-svc-001",
        project_unique_id="proj_svc_001",
        workspace_unique_id="ws_svc_001",
        directory="test-path",
        title="Test Session",
        gmt_create=get_timestamp_ms(),
        gmt_modified=get_timestamp_ms()
    )
    db_session.add(session)
    await db_session.flush()
    
    return {
        "project": project,
        "workspace": workspace,
        "session": session
    }


@pytest.mark.asyncio
async def test_create_message(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    message_data = {
        "role": "user",
        "content": "Hello from service!"
    }
    
    message = await service.create_message(
        message_unique_id="msg_svc_001",
        session_unique_id="sess_svc_001",
        data=message_data
    )
    
    assert message.id is not None
    assert message.message_unique_id == "msg_svc_001"
    assert message.session_unique_id == "sess_svc_001"
    assert message.gmt_create is not None
    assert message.gmt_modified is not None
    
    parsed_data = json.loads(message.data)
    assert parsed_data["role"] == "user"
    assert parsed_data["content"] == "Hello from service!"


@pytest.mark.asyncio
async def test_create_message_with_custom_timestamps(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    custom_time = 1700000000
    message = await service.create_message(
        message_unique_id="msg_svc_002",
        session_unique_id="sess_svc_001",
        data={"role": "assistant", "content": "Response"},
        gmt_create=custom_time,
        gmt_modified=custom_time + 100
    )
    
    assert message.gmt_create == custom_time
    assert message.gmt_modified == custom_time + 100


@pytest.mark.asyncio
async def test_get_message_by_id(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    created = await service.create_message(
        message_unique_id="msg_svc_get_id",
        session_unique_id="sess_svc_001",
        data={"role": "user", "content": "Test"}
    )
    
    found = await service.get_message_by_id(created.id)
    
    assert found is not None
    assert found.id == created.id
    assert found.message_unique_id == "msg_svc_get_id"


@pytest.mark.asyncio
async def test_get_message_by_id_not_found(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    found = await service.get_message_by_id(99999)
    
    assert found is None


@pytest.mark.asyncio
async def test_get_message_by_unique_id(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    await service.create_message(
        message_unique_id="msg_unique_test",
        session_unique_id="sess_svc_001",
        data={"role": "user", "content": "Unique test"}
    )
    
    found = await service.get_message_by_unique_id("msg_unique_test")
    
    assert found is not None
    assert found.message_unique_id == "msg_unique_test"


@pytest.mark.asyncio
async def test_get_message_by_unique_id_not_found(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    found = await service.get_message_by_unique_id("non_existent_id")
    
    assert found is None


@pytest.mark.asyncio
async def test_list_messages(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    for i in range(5):
        await service.create_message(
            message_unique_id=f"msg_list_{i}",
            session_unique_id="sess_svc_001",
            data={"role": "user", "content": f"Message {i}"}
        )
    
    messages = await service.list_messages(session_unique_id="sess_svc_001")
    
    assert len(messages) == 5
    contents = [json.loads(m.data)["content"] for m in messages]
    assert "Message 0" in contents
    assert "Message 4" in contents


@pytest.mark.asyncio
async def test_list_messages_with_pagination(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    for i in range(10):
        await service.create_message(
            message_unique_id=f"msg_page_{i}",
            session_unique_id="sess_svc_001",
            data={"role": "user", "content": f"Message {i}"}
        )
    
    first_page = await service.list_messages(
        session_unique_id="sess_svc_001",
        offset=0,
        limit=5
    )
    assert len(first_page) == 5
    
    second_page = await service.list_messages(
        session_unique_id="sess_svc_001",
        offset=5,
        limit=5
    )
    assert len(second_page) == 5


@pytest.mark.asyncio
async def test_list_messages_empty_session(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    new_session = Session(
        session_unique_id="sess_empty",
        external_session_id="external-sess-empty",
        project_unique_id="proj_svc_001",
        workspace_unique_id="ws_svc_001",
        directory="test-path",
        title="Empty Session",
        gmt_create=get_timestamp_ms(),
        gmt_modified=get_timestamp_ms()
    )
    db_session.add(new_session)
    await db_session.flush()
    
    messages = await service.list_messages(session_unique_id="sess_empty")
    
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_count_messages(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    for i in range(7):
        await service.create_message(
            message_unique_id=f"msg_count_{i}",
            session_unique_id="sess_svc_001",
            data={"role": "user", "content": f"Count {i}"}
        )
    
    count = await service.count_messages(session_unique_id="sess_svc_001")
    
    assert count == 7


@pytest.mark.asyncio
async def test_update_message(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    await service.create_message(
        message_unique_id="msg_to_update",
        session_unique_id="sess_svc_001",
        data={"role": "user", "content": "Original"}
    )
    
    updated = await service.update_message(
        message_unique_id="msg_to_update",
        data={"role": "assistant", "content": "Updated"}
    )
    
    assert updated is not None
    parsed_data = json.loads(updated.data)
    assert parsed_data["content"] == "Updated"
    assert parsed_data["role"] == "assistant"


@pytest.mark.asyncio
async def test_update_message_not_found(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    result = await service.update_message(
        message_unique_id="non_existent",
        data={"role": "user", "content": "Test"}
    )
    
    assert result is None


@pytest.mark.asyncio
async def test_delete_message(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    await service.create_message(
        message_unique_id="msg_to_delete",
        session_unique_id="sess_svc_001",
        data={"role": "user", "content": "To delete"}
    )
    
    deleted = await service.delete_message("msg_to_delete")
    assert deleted is True
    
    found = await service.get_message_by_unique_id("msg_to_delete")
    assert found is None


@pytest.mark.asyncio
async def test_delete_message_not_found(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    deleted = await service.delete_message("non_existent_id")
    assert deleted is False


@pytest.mark.asyncio
async def test_send_ai_prompt_without_pool(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    mock_client = AsyncMock()
    mock_client.query = AsyncMock()
    
    async def mock_receive_response_gen():
        for chunk in ["Hello", " ", "World"]:
            yield chunk
    
    async def mock_receive_response():
        return mock_receive_response_gen()
    
    mock_client.receive_response = AsyncMock(side_effect=mock_receive_response)
    
    config = ClaudeClientConfig(
        cwd="/test",
        settings="/tmp/test_settings.json"
    )
    
    with patch('services.message_service.ClaudeClient') as MockClaudeClient:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        MockClaudeClient.return_value = mock_context
        
        results = []
        async for response in service.send_ai_prompt(
            prompt="Test prompt",
            session_unique_id="sess_svc_001",
            client_config=config
        ):
            results.append(response)
        
        assert len(results) == 3
        assert results == ["Hello", " ", "World"]
        mock_client.query.assert_called_once_with("Test prompt", "sess_svc_001")


@pytest.mark.asyncio
async def test_send_ai_prompt_with_pool(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    mock_client = AsyncMock()
    mock_client.query = AsyncMock()
    
    async def mock_receive_response_gen():
        for chunk in ["AI", " Response"]:
            yield chunk
    
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
    async for response in service.send_ai_prompt(
        prompt="Pooled prompt",
        session_unique_id="sess_pool_001",
        client_config=config,
        pool=mock_pool
    ):
        results.append(response)
    
    assert len(results) == 2
    assert results == ["AI", " Response"]
    mock_pool.get_client.assert_called_once_with("sess_pool_001", config)
    mock_client.query.assert_called_once_with("Pooled prompt", "sess_pool_001")
    mock_pool.release_client.assert_called_once_with("sess_pool_001")


@pytest.mark.asyncio
async def test_send_ai_prompt_pool_releases_on_error(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    mock_client = AsyncMock()
    mock_client.query = AsyncMock(side_effect=Exception("Connection error"))
    
    mock_pool = AsyncMock()
    mock_pool.get_client = AsyncMock(return_value=mock_client)
    mock_pool.release_client = AsyncMock()
    
    config = ClaudeClientConfig(
        cwd="/test",
        settings="/tmp/test_settings.json"
    )
    
    with pytest.raises(Exception, match="Connection error"):
        async for _ in service.send_ai_prompt(
            prompt="Error test",
            session_unique_id="sess_error",
            client_config=config,
            pool=mock_pool
        ):
            pass
    
    mock_pool.release_client.assert_called_once_with("sess_error")


@pytest.mark.asyncio
async def test_send_ai_prompt_updates_latest_active_time(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    mock_client = AsyncMock()
    mock_client.query = AsyncMock()
    
    async def mock_receive_response_gen():
        for chunk in ["Response"]:
            yield chunk
    
    async def mock_receive_response():
        return mock_receive_response_gen()
    
    mock_client.receive_response = AsyncMock(side_effect=mock_receive_response)
    
    config = ClaudeClientConfig(
        cwd="/test",
        settings="/tmp/test_settings.json"
    )
    
    with patch('services.message_service.ClaudeClient') as MockClaudeClient:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        MockClaudeClient.return_value = mock_context
        
        results = []
        async for response in service.send_ai_prompt(
            prompt="Test prompt with activity tracking",
            session_unique_id="sess_svc_001",
            client_config=config,
            project_unique_id="proj_svc_001",
            workspace_unique_id="ws_svc_001"
        ):
            results.append(response)
        
        assert len(results) == 1
        
    await db_session.refresh(setup_test_data["project"])
    await db_session.refresh(setup_test_data["workspace"])
    
    assert setup_test_data["project"].latest_active_time is not None
    assert setup_test_data["workspace"].latest_active_time is not None


@pytest.mark.asyncio
async def test_send_ai_prompt_with_project_only(db_session: AsyncSession, setup_test_data):
    service = MessageService(db_session)
    
    mock_client = AsyncMock()
    mock_client.query = AsyncMock()
    
    async def mock_receive_response_gen():
        for chunk in ["Response"]:
            yield chunk
    
    async def mock_receive_response():
        return mock_receive_response_gen()
    
    mock_client.receive_response = AsyncMock(side_effect=mock_receive_response)
    
    config = ClaudeClientConfig(
        cwd="/test",
        settings="/tmp/test_settings.json"
    )
    
    with patch('services.message_service.ClaudeClient') as MockClaudeClient:
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        MockClaudeClient.return_value = mock_context
        
        results = []
        async for response in service.send_ai_prompt(
            prompt="Test prompt",
            session_unique_id="sess_svc_001",
            client_config=config,
            project_unique_id="proj_svc_001"
        ):
            results.append(response)
        
        assert len(results) == 1
        
    await db_session.refresh(setup_test_data["project"])
    
    assert setup_test_data["project"].latest_active_time is not None
