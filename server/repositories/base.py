"""Generic base repository with CRUD operations for SQLAlchemy models."""

from typing import Any, TypeVar, Generic, Type, List, Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from logger import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound="BaseModel")


class BaseModel:
    """Base class for all database models."""

    id: int

    @classmethod
    def __table__(cls) -> Any:
        """Return the table associated with this model."""
        raise NotImplementedError("Subclasses must implement __table__")


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for CRUD operations.

    This is an abstract base class that provides common CRUD operations
    for SQLAlchemy models. Concrete repositories can inherit from this
    and specialize for specific models if needed.

    Example:
        class ProjectRepository(BaseRepository[Project]):
            def __init__(self, session: AsyncSession):
                super().__init__(session)
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        logger.debug(f"BaseRepository initialized with session")

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get model by primary key.

        Args:
            id: Primary key value

        Returns:
            Model instance if found, None otherwise
        """
        try:
            logger.debug(f"get_by_id called with id={id}")
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            instance = result.scalar_one_or_none()
            logger.debug(f"get_by_id returned {type(instance).__name__ if instance else 'None'}")
            return instance
        except Exception as e:
            logger.error(f"get_by_id failed: {str(e)}")
            raise

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
        **filters: Any
    ) -> List[ModelType]:
        """
        Get all models with optional pagination and filtering.

        Args:
            offset: Offset for pagination (default: 0)
            limit: Maximum number of results (default: 100)
            **filters: Additional filter conditions

        Returns:
            List of model instances
        """
        try:
            logger.debug(f"get_all called with offset={offset}, limit={limit}, filters={list(filters.keys())}")
            query = select(self.model).offset(offset).limit(limit)

            # Apply filters if provided
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

            result = await self.session.execute(query)
            instances = list(result.scalars().all())
            logger.debug(f"get_all returned {len(instances)} results")
            return instances
        except Exception as e:
            logger.error(f"get_all failed: {str(e)}")
            raise

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new model instance.

        Args:
            **kwargs: Model field values

        Returns:
            Created model instance
        """
        try:
            logger.debug(f"create called with kwargs={list(kwargs.keys())}")
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            logger.debug(f"create returned instance with id={instance.id}")
            return instance
        except Exception as e:
            logger.error(f"create failed: {str(e)}")
            raise

    async def update(
        self,
        instance: ModelType,
        **kwargs: Any
    ) -> ModelType:
        """
        Update an existing model instance.

        Args:
            instance: Model instance to update
            **kwargs: Fields to update with new values

        Returns:
            Updated model instance
        """
        try:
            logger.debug(f"update called with instance.id={instance.id}, kwargs={list(kwargs.keys())}")
            for field, value in kwargs.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)

            await self.session.flush()
            logger.debug(f"update returned instance with id={instance.id}")
            return instance
        except Exception as e:
            logger.error(f"update failed: {str(e)}")
            raise

    async def delete(self, instance: ModelType) -> None:
        """
        Delete a model instance.

        Args:
            instance: Model instance to delete
        """
        try:
            logger.debug(f"delete called with instance.id={instance.id}")
            await self.session.delete(instance)
            await self.session.flush()
            logger.debug(f"delete succeeded for instance with id={instance.id}")
        except Exception as e:
            logger.error(f"delete failed: {str(e)}")
            raise

    async def count(self, **filters: Any) -> int:
        """
        Count model instances with optional filtering.

        Args:
            **filters: Additional filter conditions

        Returns:
            Count of matching instances
        """
        try:
            logger.debug(f"count called with filters={list(filters.keys())}")
            query = select(self.model)

            # Apply filters if provided
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

            result = await self.session.execute(query)
            count = len(result.scalars().all())
            logger.debug(f"count returned {count}")
            return count
        except Exception as e:
            logger.error(f"count failed: {str(e)}")
            raise

    async def exists(self, id: int) -> bool:
        """
        Check if a model instance exists by ID.

        Args:
            id: Primary key value

        Returns:
            True if instance exists, False otherwise
        """
        try:
            logger.debug(f"exists called with id={id}")
            exists = await self.get_by_id(id) is not None
            logger.debug(f"exists returned {exists}")
            return exists
        except Exception as e:
            logger.error(f"exists failed: {str(e)}")
            raise
