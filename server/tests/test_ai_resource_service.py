"""Tests for AiResourceService."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from services.ai_resource_service import (
    AiResourceService,
    sanitize_filename,
    DEFAULT_REFRESH_INTERVAL_MS,
)
from database.models import AiResource, Workspace


class TestSanitizeFilename:
    """Tests for sanitize_filename utility function."""

    def test_sanitize_normal_name(self):
        result = sanitize_filename("my_resource")
        assert result == "my_resource"

    def test_sanitize_name_with_spaces(self):
        result = sanitize_filename("my resource name")
        assert result == "my_resource_name"

    def test_sanitize_name_with_special_chars(self):
        result = sanitize_filename("resource@#$%name!")
        assert result == "resource____name"

    def test_sanitize_name_with_dots(self):
        result = sanitize_filename("resource...name")
        assert result == "resource_name"

    def test_sanitize_name_trailing_dots(self):
        result = sanitize_filename("..resource..")
        assert result == "resource"

    def test_sanitize_name_empty_after_sanitize(self):
        result = sanitize_filename("@#$%")
        assert result == "unnamed"

    def test_sanitize_name_too_long(self):
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) == 255


class TestAiResourceServiceCreate:
    """Tests for AiResourceService.create_ai_resource."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    @pytest.mark.asyncio
    async def test_create_resource_basic(self, service, mock_session):
        mock_resource = MagicMock(spec=AiResource)
        mock_resource.resource_unique_id = "test-uuid"
        mock_resource.name = "Test Resource"
        
        service.ai_resource_repo.create = AsyncMock(return_value=mock_resource)
        
        result = await service.create_ai_resource(
            name="Test Resource",
            type="skill",
            sub_type="coding",
            owner=None,
            disabled=False,
            content={"key": "value"},
            test=False,
        )
        
        assert result == mock_resource
        service.ai_resource_repo.create.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_resource_with_owner(self, service, mock_session):
        mock_resource = MagicMock(spec=AiResource)
        service.ai_resource_repo.create = AsyncMock(return_value=mock_resource)
        
        result = await service.create_ai_resource(
            name="Test Resource",
            type="command",
            sub_type="general",
            owner="workspace-123",
            disabled=False,
            content={"command": "test"},
            test=False,
        )
        
        assert result == mock_resource
        call_kwargs = service.ai_resource_repo.create.call_args[1]
        assert call_kwargs["owner"] == "workspace-123"

    @pytest.mark.asyncio
    async def test_create_resource_with_custom_unique_id(self, service, mock_session):
        mock_resource = MagicMock(spec=AiResource)
        service.ai_resource_repo.create = AsyncMock(return_value=mock_resource)
        
        result = await service.create_ai_resource(
            name="Test Resource",
            type="skill",
            sub_type="coding",
            owner=None,
            disabled=False,
            content={},
            test=False,
            resource_unique_id="custom-uuid-123",
        )
        
        call_kwargs = service.ai_resource_repo.create.call_args[1]
        assert call_kwargs["resource_unique_id"] == "custom-uuid-123"

    @pytest.mark.asyncio
    async def test_create_resource_serializes_content(self, service, mock_session):
        mock_resource = MagicMock(spec=AiResource)
        service.ai_resource_repo.create = AsyncMock(return_value=mock_resource)
        
        content = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        
        await service.create_ai_resource(
            name="Test",
            type="skill",
            sub_type="test",
            owner=None,
            disabled=False,
            content=content,
            test=False,
        )
        
        call_kwargs = service.ai_resource_repo.create.call_args[1]
        assert call_kwargs["content"] == json.dumps(content)


class TestAiResourceServiceGet:
    """Tests for AiResourceService get methods."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_unique_id_found(self, service):
        mock_resource = MagicMock(spec=AiResource)
        service.ai_resource_repo.get_by_unique_id = AsyncMock(return_value=mock_resource)
        
        result = await service.get_ai_resource_by_unique_id("test-uuid", test=False)
        
        assert result == mock_resource
        service.ai_resource_repo.get_by_unique_id.assert_called_once_with("test-uuid", test=False)

    @pytest.mark.asyncio
    async def test_get_by_unique_id_not_found(self, service):
        service.ai_resource_repo.get_by_unique_id = AsyncMock(return_value=None)
        
        result = await service.get_ai_resource_by_unique_id("nonexistent", test=False)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, service):
        mock_resource = MagicMock(spec=AiResource)
        service.ai_resource_repo.get_by_id = AsyncMock(return_value=mock_resource)
        
        result = await service.get_ai_resource_by_id(1, test=False)
        
        assert result == mock_resource

    @pytest.mark.asyncio
    async def test_list_resources(self, service):
        mock_resources = [MagicMock(spec=AiResource), MagicMock(spec=AiResource)]
        service.ai_resource_repo.get_all = AsyncMock(return_value=mock_resources)
        
        result = await service.list_ai_resources(offset=0, limit=10, test=False)
        
        assert result == mock_resources
        service.ai_resource_repo.get_all.assert_called_once_with(offset=0, limit=10, test=False)


class TestAiResourceServiceUpdate:
    """Tests for AiResourceService.update_ai_resource."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    @pytest.mark.asyncio
    async def test_update_resource_found(self, service, mock_session):
        mock_resource = MagicMock(spec=AiResource)
        mock_resource.resource_unique_id = "test-uuid"
        
        service.ai_resource_repo.get_by_unique_id = AsyncMock(return_value=mock_resource)
        service.ai_resource_repo.update = AsyncMock(return_value=mock_resource)
        
        result = await service.update_ai_resource(
            resource_unique_id="test-uuid",
            test=False,
            name="Updated Name",
        )
        
        assert result == mock_resource
        service.ai_resource_repo.update.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_resource_not_found(self, service, mock_session):
        service.ai_resource_repo.get_by_unique_id = AsyncMock(return_value=None)
        
        result = await service.update_ai_resource(
            resource_unique_id="nonexistent",
            test=False,
            name="Updated Name",
        )
        
        assert result is None
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_resource_serializes_content(self, service, mock_session):
        mock_resource = MagicMock(spec=AiResource)
        
        service.ai_resource_repo.get_by_unique_id = AsyncMock(return_value=mock_resource)
        service.ai_resource_repo.update = AsyncMock(return_value=mock_resource)
        
        new_content = {"updated": "content"}
        
        await service.update_ai_resource(
            resource_unique_id="test-uuid",
            test=False,
            content=new_content,
        )
        
        call_kwargs = service.ai_resource_repo.update.call_args[1]
        assert call_kwargs["content"] == json.dumps(new_content)


class TestAiResourceServiceDelete:
    """Tests for AiResourceService.delete_ai_resource."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    @pytest.mark.asyncio
    async def test_delete_resource_found(self, service, mock_session):
        mock_resource = MagicMock(spec=AiResource)
        
        service.ai_resource_repo.get_by_unique_id = AsyncMock(return_value=mock_resource)
        service.ai_resource_repo.delete = AsyncMock()
        
        result = await service.delete_ai_resource("test-uuid", test=False)
        
        assert result is True
        service.ai_resource_repo.delete.assert_called_once_with(mock_resource)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_resource_not_found(self, service, mock_session):
        service.ai_resource_repo.get_by_unique_id = AsyncMock(return_value=None)
        
        result = await service.delete_ai_resource("nonexistent", test=False)
        
        assert result is False
        mock_session.commit.assert_not_called()


class TestAiResourceServiceShouldSync:
    """Tests for AiResourceService._should_sync."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    def test_should_sync_never_synced(self, service):
        mock_workspace = MagicMock(spec=Workspace)
        mock_workspace.directory = "test-workspace"
        mock_workspace.latest_active_time = None
        
        result = service._should_sync(mock_workspace, DEFAULT_REFRESH_INTERVAL_MS)
        
        assert result is True

    def test_should_sync_expired(self, service):
        mock_workspace = MagicMock(spec=Workspace)
        mock_workspace.directory = "test-workspace"
        mock_workspace.latest_active_time = 0  # Very old
        
        result = service._should_sync(mock_workspace, 1000)  # 1 second interval
        
        assert result is True

    @patch("services.ai_resource_service.get_timestamp_ms")
    def test_should_sync_not_expired(self, mock_timestamp, service):
        mock_timestamp.return_value = 5000
        
        mock_workspace = MagicMock(spec=Workspace)
        mock_workspace.directory = "test-workspace"
        mock_workspace.latest_active_time = 4000  # 1 second ago
        
        result = service._should_sync(mock_workspace, 10000)  # 10 second interval
        
        assert result is False
