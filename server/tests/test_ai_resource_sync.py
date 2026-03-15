"""Tests for AI resource sync logic."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from services.ai_resource_service import AiResourceService, TYPE_DIR_MAP
from database.models import AiResource, Workspace


class TestWriteAtomically:
    """Tests for _write_atomically method."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    @pytest.mark.asyncio
    async def test_write_atomically_creates_file(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.md"
            await service._write_atomically(filepath, "test content")
            assert filepath.exists()
            assert filepath.read_text() == "test content"

    @pytest.mark.asyncio
    async def test_write_atomically_creates_parent_dirs(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "nested" / "dir" / "test.md"
            await service._write_atomically(filepath, "content")
            assert filepath.exists()

    @pytest.mark.asyncio
    async def test_write_atomically_atomic_write(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.md"
            await service._write_atomically(filepath, "initial")
            await service._write_atomically(filepath, "updated")
            assert filepath.read_text() == "updated"


class TestCreateSymlinkSafe:
    """Tests for _create_symlink_safe method."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    def test_create_symlink_creates_new(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"
            target.mkdir()
            link = Path(tmpdir) / "link"
            
            result = service._create_symlink_safe(target, link)
            
            assert result is True
            assert link.is_symlink()
            assert os.readlink(str(link)) == str(target.resolve())

    def test_create_symlink_existing_symlink_returns_true(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"
            target.mkdir()
            link = Path(tmpdir) / "link"
            os.symlink(str(target), str(link))
            
            result = service._create_symlink_safe(target, link)
            
            assert result is True

    def test_create_symlink_existing_file_returns_false(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"
            target.mkdir()
            link = Path(tmpdir) / "link"
            link.write_text("existing file")
            
            result = service._create_symlink_safe(target, link)
            
            assert result is False

    def test_create_symlink_missing_target_returns_false(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "nonexistent"
            link = Path(tmpdir) / "link"
            
            result = service._create_symlink_safe(target, link)
            
            assert result is False


class TestWriteResourceFiles:
    """Tests for _write_resource_files method."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    def _make_resource(self, name, type, sub_type, content):
        resource = MagicMock(spec=AiResource)
        resource.name = name
        resource.type = type
        resource.sub_type = sub_type
        resource.content = content
        resource.disabled = False
        return resource

    @pytest.mark.asyncio
    async def test_write_skill_files(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            root_path = Path(tmpdir)
            resource = self._make_resource("test-skill", "skill", "coding", "# Skill content")
            
            written_paths = await service._write_resource_files(
                resources=[resource],
                root_path=root_path,
                owner="workspace-1",
            )
            
            assert len(written_paths) == 1
            expected_path = root_path / "workspace-1" / "skills" / "coding" / "test-skill.md"
            assert expected_path in written_paths
            assert expected_path.read_text() == "# Skill content"

    @pytest.mark.asyncio
    async def test_write_command_files(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            root_path = Path(tmpdir)
            resource = self._make_resource("test-cmd", "command", "general", "echo hello")
            
            written_paths = await service._write_resource_files(
                resources=[resource],
                root_path=root_path,
                owner=None,
            )
            
            expected_path = root_path / "global" / "commands" / "general" / "test-cmd.md"
            assert expected_path in written_paths

    @pytest.mark.asyncio
    async def test_write_multiple_resources(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            root_path = Path(tmpdir)
            resources = [
                self._make_resource("skill1", "skill", "coding", "content1"),
                self._make_resource("skill2", "skill", "testing", "content2"),
            ]
            
            written_paths = await service._write_resource_files(
                resources=resources,
                root_path=root_path,
                owner="ws",
            )
            
            assert len(written_paths) == 2


class TestDeleteOrphanFiles:
    """Tests for _delete_orphan_files method."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    @pytest.mark.asyncio
    async def test_delete_orphans_keeps_valid_files(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            root_path = Path(tmpdir)
            skills_dir = root_path / "ws" / "skills"
            skills_dir.mkdir(parents=True)
            
            valid_file = skills_dir / "valid.md"
            valid_file.write_text("keep me")
            orphan_file = skills_dir / "orphan.md"
            orphan_file.write_text("delete me")
            
            deleted = await service._delete_orphan_files(
                root_path=root_path,
                owner="ws",
                valid_paths={valid_file},
            )
            
            assert deleted == 1
            assert valid_file.exists()
            assert not orphan_file.exists()

    @pytest.mark.asyncio
    async def test_delete_orphans_no_orphans(self, service):
        with tempfile.TemporaryDirectory() as tmpdir:
            root_path = Path(tmpdir)
            skills_dir = root_path / "ws" / "skills"
            skills_dir.mkdir(parents=True)
            
            valid_file = skills_dir / "valid.md"
            valid_file.write_text("keep me")
            
            deleted = await service._delete_orphan_files(
                root_path=root_path,
                owner="ws",
                valid_paths={valid_file},
            )
            
            assert deleted == 0


class TestReadSystemPrompts:
    """Tests for _read_system_prompts method."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    def _make_resource(self, type, content, disabled=False):
        resource = MagicMock(spec=AiResource)
        resource.type = type
        resource.content = content
        resource.disabled = disabled
        return resource

    @pytest.mark.asyncio
    async def test_read_prompts_merges_enabled(self, service):
        resources = [
            self._make_resource("system_prompt", "First prompt"),
            self._make_resource("system_prompt", "Second prompt"),
        ]
        
        result = await service._read_system_prompts(resources)
        
        assert "First prompt" in result
        assert "Second prompt" in result
        assert "---" in result

    @pytest.mark.asyncio
    async def test_read_prompts_skips_disabled(self, service):
        resources = [
            self._make_resource("system_prompt", "Active", disabled=False),
            self._make_resource("system_prompt", "Inactive", disabled=True),
        ]
        
        result = await service._read_system_prompts(resources)
        
        assert "Active" in result
        assert "Inactive" not in result

    @pytest.mark.asyncio
    async def test_read_prompts_empty_when_none(self, service):
        resources = []
        result = await service._read_system_prompts(resources)
        assert result == ""

    @pytest.mark.asyncio
    async def test_read_prompts_ignores_other_types(self, service):
        resources = [
            self._make_resource("skill", "Skill content"),
            self._make_resource("command", "Command content"),
        ]
        
        result = await service._read_system_prompts(resources)
        assert result == ""


class TestSyncLock:
    """Tests for sync lock mechanism."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return AiResourceService(mock_session)

    @pytest.mark.asyncio
    async def test_get_sync_lock_creates_new(self, service):
        from services.ai_resource_service import SYNC_LOCK
        SYNC_LOCK.clear()
        
        lock = await service._get_sync_lock("workspace-1")
        
        assert lock is not None
        assert "workspace-1" in SYNC_LOCK

    @pytest.mark.asyncio
    async def test_get_sync_lock_returns_existing(self, service):
        from services.ai_resource_service import SYNC_LOCK
        import asyncio
        SYNC_LOCK.clear()
        
        lock1 = await service._get_sync_lock("workspace-1")
        lock2 = await service._get_sync_lock("workspace-1")
        
        assert lock1 is lock2
