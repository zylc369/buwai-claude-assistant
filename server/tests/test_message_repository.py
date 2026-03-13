"""Tests for MessageRepository."""

import json
import pytest
import pytest_asyncio
import time
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project, Workspace, Session, Message
from repositories.message_repository import MessageRepository


@pytest_asyncio.fixture
async def setup_test_data(db_session: AsyncSession):
    """Create test project, workspace, and session for message tests."""
    # Create project
    project = Project(
        project_unique_id="proj_001",
        worktree="/test/path",
        branch="main",
        name="Test Project",
        time_created=int(time.time()),
        time_updated=int(time.time())
    )
    db_session.add(project)
    await db_session.flush()
    
    # Create workspace
    workspace = Workspace(
        workspace_unique_id="ws_001",
        branch="main",
        name="Test Workspace",
        directory="/test/path",
        project_unique_id="proj_001"
    )
    db_session.add(workspace)
    await db_session.flush()
    
    # Create session
    session = Session(
        session_unique_id="sess_001",
        external_session_id="external-sess-001",
        project_unique_id="proj_001",
        workspace_unique_id="ws_001",
        directory="/test/path",
        title="Test Session",
        time_created=int(time.time()),
        time_updated=int(time.time())
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
    """Test creating a new message."""
    repo = MessageRepository(db_session)
    
    message_data = {
        "role": "user",
        "content": "Hello, world!",
        "metadata": {"key": "value"}
    }
    
    current_time = int(time.time())
    message = await repo.create(
        message_unique_id="msg_001",
        session_unique_id="sess_001",
        time_created=current_time,
        time_updated=current_time,
        data=message_data
    )
    
    assert message.id is not None
    assert message.message_unique_id == "msg_001"
    assert message.session_unique_id == "sess_001"
    assert message.time_created == current_time
    assert message.time_updated == current_time
    
    # Verify data is stored as JSON string
    assert isinstance(message.data, str)
    parsed_data = json.loads(message.data)
    assert parsed_data["role"] == "user"
    assert parsed_data["content"] == "Hello, world!"
    assert parsed_data["metadata"]["key"] == "value"


@pytest.mark.asyncio
async def test_create_message_with_complex_data(db_session: AsyncSession, setup_test_data):
    """Test creating message with complex nested data."""
    repo = MessageRepository(db_session)
    
    message_data = {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Hello!"},
            {"type": "image", "url": "https://example.com/image.png"}
        ],
        "metadata": {
            "model": "claude-3",
            "tokens": {"input": 10, "output": 20}
        }
    }
    
    current_time = int(time.time())
    message = await repo.create(
        message_unique_id="msg_002",
        session_unique_id="sess_001",
        time_created=current_time,
        time_updated=current_time,
        data=message_data
    )
    
    # Verify complex data structure
    parsed_data = json.loads(message.data)
    assert len(parsed_data["content"]) == 2
    assert parsed_data["content"][0]["type"] == "text"
    assert parsed_data["metadata"]["tokens"]["input"] == 10


@pytest.mark.asyncio
async def test_get_by_unique_id_exists(db_session: AsyncSession, setup_test_data):
    """Test getting an existing message by unique ID."""
    repo = MessageRepository(db_session)
    
    # Create a message first
    current_time = int(time.time())
    await repo.create(
        message_unique_id="msg_003",
        session_unique_id="sess_001",
        time_created=current_time,
        time_updated=current_time,
        data={"role": "user", "content": "Test message"}
    )
    
    # Get by unique ID
    result = await repo.get_by_unique_id("msg_003")
    
    assert result is not None
    assert result.message_unique_id == "msg_003"
    assert result.session_unique_id == "sess_001"


@pytest.mark.asyncio
async def test_get_by_unique_id_not_exists(db_session: AsyncSession, setup_test_data):
    """Test getting a non-existent message by unique ID."""
    repo = MessageRepository(db_session)
    
    result = await repo.get_by_unique_id("non_existent_id")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_by_session_unique_id(db_session: AsyncSession, setup_test_data):
    """Test getting all messages for a session."""
    repo = MessageRepository(db_session)
    
    # Create multiple messages
    current_time = int(time.time())
    for i in range(5):
        await repo.create(
            message_unique_id=f"msg_{i+10}",
            session_unique_id="sess_001",
            time_created=current_time + i,
            time_updated=current_time + i,
            data={"role": "user", "content": f"Message {i}"}
        )
    
    # Get messages for session
    result = await repo.get_by_session_unique_id("sess_001")
    
    assert len(result) == 5
    # Messages should be ordered by time_created
    contents = [json.loads(m.data)["content"] for m in result]
    assert "Message 0" in contents
    assert "Message 4" in contents


@pytest.mark.asyncio
async def test_get_by_session_unique_id_with_pagination(db_session: AsyncSession, setup_test_data):
    """Test getting messages for a session with pagination."""
    repo = MessageRepository(db_session)
    
    # Create 10 messages
    current_time = int(time.time())
    for i in range(10):
        await repo.create(
            message_unique_id=f"msg_page_{i}",
            session_unique_id="sess_001",
            time_created=current_time + i,
            time_updated=current_time + i,
            data={"role": "user", "content": f"Message {i}"}
        )
    
    # Get first 5 messages
    result = await repo.get_by_session_unique_id("sess_001", offset=0, limit=5)
    assert len(result) == 5
    
    # Get next 5 messages
    result = await repo.get_by_session_unique_id("sess_001", offset=5, limit=5)
    assert len(result) == 5


@pytest.mark.asyncio
async def test_get_by_session_unique_id_empty(db_session: AsyncSession, setup_test_data):
    """Test getting messages for a session with no messages."""
    repo = MessageRepository(db_session)
    
    # Create another session
    new_session = Session(
        session_unique_id="sess_002",
        external_session_id="external-sess-002",
        project_unique_id="proj_001",
        workspace_unique_id="ws_001",
        directory="/test/path",
        title="Empty Session",
        time_created=int(time.time()),
        time_updated=int(time.time())
    )
    db_session.add(new_session)
    await db_session.flush()
    
    # Get messages for empty session
    result = await repo.get_by_session_unique_id("sess_002")
    
    assert len(result) == 0


@pytest.mark.asyncio
async def test_list_method(db_session: AsyncSession, setup_test_data):
    """Test that list() method works as alias for get_by_session_unique_id()."""
    repo = MessageRepository(db_session)
    
    # Create messages
    current_time = int(time.time())
    for i in range(3):
        await repo.create(
            message_unique_id=f"msg_list_{i}",
            session_unique_id="sess_001",
            time_created=current_time + i,
            time_updated=current_time + i,
            data={"role": "user", "content": f"List message {i}"}
        )
    
    # Use list method
    result = await repo.list("sess_001")
    
    assert len(result) == 3


@pytest.mark.asyncio
async def test_count_by_session(db_session: AsyncSession, setup_test_data):
    """Test counting messages for a session."""
    repo = MessageRepository(db_session)
    
    # Create messages
    current_time = int(time.time())
    for i in range(7):
        await repo.create(
            message_unique_id=f"msg_count_{i}",
            session_unique_id="sess_001",
            time_created=current_time + i,
            time_updated=current_time + i,
            data={"role": "user", "content": f"Count message {i}"}
        )
    
    # Count messages
    count = await repo.count_by_session("sess_001")
    
    assert count == 7


@pytest.mark.asyncio
async def test_count_by_session_empty(db_session: AsyncSession, setup_test_data):
    """Test counting messages for a session with no messages."""
    repo = MessageRepository(db_session)
    
    # Create another session
    new_session = Session(
        session_unique_id="sess_count_empty",
        external_session_id="external-sess-count-empty",
        project_unique_id="proj_001",
        workspace_unique_id="ws_001",
        directory="/test/path",
        title="Count Empty Session",
        time_created=int(time.time()),
        time_updated=int(time.time())
    )
    db_session.add(new_session)
    await db_session.flush()
    
    # Count messages for empty session
    count = await repo.count_by_session("sess_count_empty")
    
    assert count == 0


@pytest.mark.asyncio
async def test_data_field_json_serialization(db_session: AsyncSession, setup_test_data):
    """Test that data field correctly stores and retrieves JSON."""
    repo = MessageRepository(db_session)
    
    # Create message with various data types
    message_data = {
        "string": "value",
        "number": 42,
        "float": 3.14,
        "boolean": True,
        "null": None,
        "array": [1, 2, 3],
        "nested": {"a": {"b": {"c": "deep"}}}
    }
    
    current_time = int(time.time())
    message = await repo.create(
        message_unique_id="msg_json_test",
        session_unique_id="sess_001",
        time_created=current_time,
        time_updated=current_time,
        data=message_data
    )
    
    # Retrieve and verify
    retrieved = await repo.get_by_unique_id("msg_json_test")
    parsed_data = json.loads(retrieved.data)
    
    assert parsed_data["string"] == "value"
    assert parsed_data["number"] == 42
    assert parsed_data["float"] == 3.14
    assert parsed_data["boolean"] is True
    assert parsed_data["null"] is None
    assert parsed_data["array"] == [1, 2, 3]
    assert parsed_data["nested"]["a"]["b"]["c"] == "deep"


@pytest.mark.asyncio
async def test_update_message(db_session: AsyncSession, setup_test_data):
    """Test updating an existing message."""
    repo = MessageRepository(db_session)
    
    # Create message
    current_time = int(time.time())
    message = await repo.create(
        message_unique_id="msg_update_test",
        session_unique_id="sess_001",
        time_created=current_time,
        time_updated=current_time,
        data={"role": "user", "content": "Original content"}
    )
    
    # Update message data
    new_data = {"role": "assistant", "content": "Updated content"}
    updated = await repo.update(
        message,
        data=json.dumps(new_data),
        time_updated=current_time + 100
    )
    
    parsed_data = json.loads(updated.data)
    assert parsed_data["content"] == "Updated content"
    assert updated.time_updated == current_time + 100


@pytest.mark.asyncio
async def test_delete_message(db_session: AsyncSession, setup_test_data):
    """Test deleting a message."""
    repo = MessageRepository(db_session)
    
    # Create message
    current_time = int(time.time())
    message = await repo.create(
        message_unique_id="msg_delete_test",
        session_unique_id="sess_001",
        time_created=current_time,
        time_updated=current_time,
        data={"role": "user", "content": "To be deleted"}
    )
    
    # Verify it exists
    result = await repo.get_by_unique_id("msg_delete_test")
    assert result is not None
    
    # Delete message
    await repo.delete(message)
    
    # Verify it's deleted
    result = await repo.get_by_unique_id("msg_delete_test")
    assert result is None
