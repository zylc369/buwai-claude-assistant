"""AiResource repository for database operations."""

from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AiResource
from repositories.base import BaseRepository
from logger import get_logger

logger = get_logger(__name__)


class AiResourceRepository(BaseRepository[AiResource]):
    """Repository for AiResource model operations.
    
    Provides AI resource-specific database operations on top of base CRUD.
    
    Attributes:
        model: The AiResource model class.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize AiResourceRepository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session)
        self.model = AiResource
        logger.debug("AiResourceRepository initialized")
    
    async def get_by_owner_query(self, owner: str | None) -> List[AiResource]:
        """Get resources by owner (workspace directory).

        Args:
            owner: Workspace directory string to match against owner field.

        Returns:
            List of AiResource objects matching the owner.
        """
        try:
            logger.debug(f"get_by_owner_query called with owner={owner}")
            result = await self.session.execute(
                select(AiResource).where(
                    AiResource.owner == owner
                )
            )
            resources = list(result.scalars().all())
            logger.debug(f"get_by_owner_query returned {len(resources)} resources")
            return resources
        except Exception as e:
            logger.error(f"get_by_owner_query failed: {str(e)}")
            raise
    
    async def get_global_resources(self) -> List[AiResource]:
        """Get global resources (owner is null or empty string).

        Returns:
            List of global AiResource objects.
        """
        try:
            logger.debug("get_global_resources called")
            result = await self.session.execute(
                select(AiResource).where(
                    or_(
                        AiResource.owner.is_(None),
                        AiResource.owner == ''
                    )
                )
            )
            resources = list(result.scalars().all())
            logger.debug(f"get_global_resources returned {len(resources)} resources")
            return resources
        except Exception as e:
            logger.error(f"get_global_resources failed: {str(e)}")
            raise

    async def get_resources_for_sync(
        self,
        owner: Optional[str] = None,
        test: bool = False
    ) -> List[AiResource]:
        """Get resources eligible for sync to workspace.

        Returns resources where:
        - owner is NULL or empty string (global) OR owner matches the given owner
        - test = False
        - disabled = False

        Args:
            owner: Workspace directory to match against owner field.
            test: Whether to include test resources (default: False).

        Returns:
            List of AiResource objects eligible for sync.
        """
        try:
            logger.debug(f"get_resources_for_sync called with owner={owner}, test={test}")

            owner_conditions = or_(
                AiResource.owner.is_(None),
                AiResource.owner == '',
            )
            if owner:
                owner_conditions = or_(owner_conditions, AiResource.owner == owner)

            result = await self.session.execute(
                select(AiResource).where(
                    owner_conditions,
                    AiResource.test == test,
                    AiResource.disabled == False  # noqa: E712
                )
            )
            resources = list(result.scalars().all())
            logger.debug(f"get_resources_for_sync returned {len(resources)} resources")
            return resources
        except Exception as e:
            logger.error(f"get_resources_for_sync failed: {str(e)}")
            raise

    async def get_by_unique_id(
        self,
        resource_unique_id: str,
        test: bool = False
    ) -> Optional[AiResource]:
        """Get resource by unique identifier.

        Args:
            resource_unique_id: Unique identifier of the resource.
            test: Whether to query test resources (default: False).

        Returns:
            AiResource if found, None otherwise.
        """
        try:
            logger.debug(f"get_by_unique_id called with resource_unique_id={resource_unique_id}")
            result = await self.session.execute(
                select(AiResource).where(
                    AiResource.resource_unique_id == resource_unique_id,
                    AiResource.test == test
                )
            )
            resource = result.scalar_one_or_none()
            logger.debug(f"get_by_unique_id completed, found={resource is not None}")
            return resource
        except Exception as e:
            logger.error(f"get_by_unique_id failed: {str(e)}")
            raise
