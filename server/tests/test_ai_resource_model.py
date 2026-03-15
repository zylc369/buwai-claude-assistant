"""Tests for AiResource model."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AiResource


class TestAiResourceModel:
    """Tests for AiResource model."""

    @pytest.mark.asyncio
    async def test_create_ai_resource_minimal(self, db_session: AsyncSession):
        """Test creating AI resource with minimal fields."""
        import time
        now = int(time.time() * 1000)
        
        resource = AiResource(
            resource_unique_id="res-001",
            name="test-skill",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "test content"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)
        
        assert resource.id is not None
        assert resource.resource_unique_id == "res-001"
        assert resource.name == "test-skill"
        assert resource.type == "SKILL"
        assert resource.sub_type == ""
        assert resource.owner is None
        assert resource.disabled is False
        assert resource.test is True

    @pytest.mark.asyncio
    async def test_create_ai_resource_with_owner(self, db_session: AsyncSession):
        """Test creating AI resource with owner."""
        import time
        now = int(time.time() * 1000)
        
        resource = AiResource(
            resource_unique_id="res-002",
            name="test-command",
            type="COMMAND",
            sub_type="git",
            owner="workspace-123",
            disabled=False,
            content='{"type": "SHELL", "data": "#!/bin/bash\\necho hello"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)
        
        assert resource.owner == "workspace-123"
        assert resource.type == "COMMAND"
        assert resource.sub_type == "git"

    @pytest.mark.asyncio
    async def test_create_ai_resource_all_types(self, db_session: AsyncSession):
        """Test creating AI resources of all types."""
        import time
        now = int(time.time() * 1000)
        
        types = ["SKILL", "COMMAND", "SYSTEM_PROMPT"]
        
        for i, res_type in enumerate(types):
            resource = AiResource(
                resource_unique_id=f"res-type-{i}",
                name=f"test-{res_type.lower()}",
                type=res_type,
                sub_type="",
                owner=None,
                disabled=False,
                content='{"type": "MD", "data": "content"}',
                gmt_create=now,
                gmt_modified=now,
                test=True
            )
            db_session.add(resource)
        
        await db_session.commit()
        
        # Verify all types saved
        from sqlalchemy import select
        result = await db_session.execute(
            select(AiResource).where(AiResource.test == True)
        )
        resources = result.scalars().all()
        
        saved_types = {r.type for r in resources}
        assert "SKILL" in saved_types
        assert "COMMAND" in saved_types
        assert "SYSTEM_PROMPT" in saved_types

    @pytest.mark.asyncio
    async def test_ai_resource_unique_constraint(self, db_session: AsyncSession):
        """Test that resource_unique_id must be unique."""
        import time
        from sqlalchemy.exc import IntegrityError
        
        now = int(time.time() * 1000)
        
        resource1 = AiResource(
            resource_unique_id="unique-res-001",
            name="resource1",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "content"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        db_session.add(resource1)
        await db_session.commit()
        
        # Try to create another with same unique_id
        resource2 = AiResource(
            resource_unique_id="unique-res-001",  # Same ID
            name="resource2",
            type="COMMAND",
            sub_type="",
            owner=None,
            disabled=False,
            content='{"type": "MD", "data": "content2"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        db_session.add(resource2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_ai_resource_disabled_default(self, db_session: AsyncSession):
        """Test that disabled defaults to False."""
        import time
        now = int(time.time() * 1000)
        
        resource = AiResource(
            resource_unique_id="res-default",
            name="default-disabled",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,  # Explicitly set
            content='{"type": "MD", "data": "content"}',
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)
        
        assert resource.disabled is False

    @pytest.mark.asyncio
    async def test_ai_resource_content_json(self, db_session: AsyncSession):
        """Test that content is stored as JSON string."""
        import time
        import json
        now = int(time.time() * 1000)
        
        content = {"type": "MD", "data": "# Heading\n\nContent with **markdown**"}
        
        resource = AiResource(
            resource_unique_id="res-json",
            name="json-content",
            type="SKILL",
            sub_type="",
            owner=None,
            disabled=False,
            content=json.dumps(content),
            gmt_create=now,
            gmt_modified=now,
            test=True
        )
        
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)
        
        # Parse and verify
        parsed = json.loads(resource.content)
        assert parsed["type"] == "MD"
        assert "Heading" in parsed["data"]
