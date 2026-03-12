"""Generic base repository with CRUD operations for SQLAlchemy models."""

from typing import Any, TypeVar, Generic, Type, List, Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get model by primary key.

        Args:
            id: Primary key value

        Returns:
            Model instance if found, None otherwise
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

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
        query = select(self.model).offset(offset).limit(limit)

        # Apply filters if provided
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new model instance.

        Args:
            **kwargs: Model field values

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

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
        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        await self.session.flush()
        return instance

    async def delete(self, instance: ModelType) -> None:
        """
        Delete a model instance.

        Args:
            instance: Model instance to delete
        """
        await self.session.delete(instance)
        await self.session.flush()

    async def count(self, **filters: Any) -> int:
        """
        Count model instances with optional filtering.

        Args:
            **filters: Additional filter conditions

        Returns:
            Count of matching instances
        """
        query = select(self.model)

        # Apply filters if provided
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def exists(self, id: int) -> bool:
        """
        Check if a model instance exists by ID.

        Args:
            id: Primary key value

        Returns:
            True if instance exists, False otherwise
        """
        return await self.get_by_id(id) is not None
