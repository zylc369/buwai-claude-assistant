"""Tests for AiResourceRepository."""

import pytest
import time
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AiResource
from repositories.ai_resource_repository import AiResourceRepository


class TestAiResourceRepositoryCreate:
    """Tests for AiResourceRepository.create method."""

    @pytest.mark.asyncio
    async def test_create_resource_basic(self, db_session: AsyncSession):
        repo = AiResourceRepository(db_session)
        now = int(time.time() * 1000)

        resource = await repo.create(
            resource_unique_id="repo-test-001",
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

        assert resource.id is not None
        assert resource.resource_unique_id == "repo-test-001"
        assert resource.name == "test-skill"

    @pytest.mark.asyncio
    async def test_create_resource_with_owner(self, db_session: AsyncSession):
        repo = AiResourceRepository(db_session)
        now = int(time.time() * 1000)

        resource = await repo.create(
            resource_unique_id="repo-test-002",
            name="test-command",
            type="COMMAND",
            sub_type="git",
            owner="workspace-abc",
            disabled=False,
            content='{"type": "SHELL", "data": "echo hello"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )

        assert resource.owner == "workspace-abc"
        assert resource.sub_type == "git"


class TestAiResourceRepositoryGetByUniqueId:
    """Tests for AiResourceRepository.get_by_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_unique_id_exists(self, db_session: AsyncSession):
        repo = AiResourceRepository(db_session)
        now = int(time.time() * 1000)

        created = await repo.create(
            resource_unique_id="get-test-001",
            name="test",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "test"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )

        found = await repo.get_by_unique_id("get-test-001", test=True)
        assert found is not None
        assert found.resource_unique_id == "get-test-001"

    @pytest.mark.asyncio
    async def test_get_by_unique_id_not_found(self, db_session: AsyncSession):
        repo = AiResourceRepository(db_session)
        found = await repo.get_by_unique_id("nonexistent", test=True)
        assert found is None


class TestAiResourceRepositoryGetByOwnerQuery:
    """Tests for AiResourceRepository.get_by_owner_query method."""

    @pytest.mark.asyncio
    async def test_get_by_owner_found(self, db_session: AsyncSession):
        repo = AiResourceRepository(db_session)
        now = int(time.time() * 1000)

        await repo.create(
            resource_unique_id="owner-test-001",
            name="test-skill",
            type="SKILL",
            sub_type="",
            owner="workspace-xyz",
            disabled=False,
            content='{"type": "MD", "data": "test"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )

        resources = await repo.get_by_owner_query("workspace-xyz")
        assert len(resources) == 1
        assert resources[0].owner == "workspace-xyz"

    @pytest.mark.asyncio
    async def test_get_by_owner_not_found(self, db_session: AsyncSession):
        repo = AiResourceRepository(db_session)
        resources = await repo.get_by_owner_query("nonexistent-workspace")
        assert len(resources) == 0


class TestAiResourceRepositoryGetGlobalResources:
    """Tests for AiResourceRepository.get_global_resources method."""

    @pytest.mark.asyncio
    async def test_get_global_resources_found(self, db_session: AsyncSession):
        repo = AiResourceRepository(db_session)
        now = int(time.time() * 1000)

        await repo.create(
            resource_unique_id="global-001",
            name="global-skill",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "test"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )

        await repo.create(
            resource_unique_id="global-002",
            name="global-skill-2",
            type="SKILL",
            sub_type="",
            owner="",
            disabled=False,
            content='{"type": "MD", "data": "test"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )

        resources = await repo.get_global_resources()
        assert len(resources) >= 2


class TestAiResourceRepositoryUpdate:
    """Tests for AiResourceRepository.update method."""

    @pytest.mark.asyncio
    async def test_update_resource(self, db_session: AsyncSession):
        repo = AiResourceRepository(db_session)
        now = int(time.time() * 1000)

        resource = await repo.create(
            resource_unique_id="update-test-001",
            name="original-name",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "test"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )

        updated = await repo.update(resource, name="updated-name")
        assert updated.name == "updated-name"


class TestAiResourceRepositoryDelete:
    """Tests for AiResourceRepository.delete method."""

    @pytest.mark.asyncio
    async def test_delete_resource(self, db_session: AsyncSession):
        repo = AiResourceRepository(db_session)
        now = int(time.time() * 1000)

        resource = await repo.create(
            resource_unique_id="delete-test-001",
            name="to-delete",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "test"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )

        await repo.delete(resource)
        found = await repo.get_by_unique_id("delete-test-001", test=True)
        assert found is None
