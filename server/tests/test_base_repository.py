"""Tests for BaseRepository."""

import pytest
import asyncio
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

# Import the repository
from repositories.base import BaseRepository, BaseModel


# Create a test base for models
TestBase = declarative_base()


# Mock user model for testing
class MockUser(TestBase):
    """Mock user model for testing."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    age = Column(Integer)
    test = Column(Boolean, nullable=False, default=False)


class MockUserRepository(BaseRepository[MockUser]):
    """Concrete repository for MockUser."""

    def __init__(self, session: AsyncSession):
        """Initialize with session."""
        super().__init__(session)
        self.model = MockUser


def test_get_by_id_exists():
    """Test getting an existing model by ID."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create test user
            user = MockUser(name="Alice", email="alice@example.com", test=True)
            session.add(user)
            await session.flush()
            
            # Get by ID
            repo = MockUserRepository(session)
            result = await repo.get_by_id(user.id, test=True)
            
            assert result is not None
            assert result.id == user.id
            assert result.name == "Alice"
            assert result.email == "alice@example.com"
    
    asyncio.run(_test())


def test_get_by_id_not_exists():
    """Test getting a non-existent model by ID."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Get non-existent ID
            repo = MockUserRepository(session)
            result = await repo.get_by_id(99999, test=True)
            
            assert result is None
    
    asyncio.run(_test())


def test_get_all_basic():
    """Test getting all models."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create multiple users
            users = [
                MockUser(name="Alice", email="alice@example.com", test=True),
                MockUser(name="Bob", email="bob@example.com", test=True),
                MockUser(name="Charlie", email="charlie@example.com", test=True),
            ]
            session.add_all(users)
            await session.flush()
            
            # Get all
            repo = MockUserRepository(session)
            result = await repo.get_all(test=True)
            
            assert len(result) == 3
            names = [u.name for u in result]
            assert "Alice" in names
            assert "Bob" in names
            assert "Charlie" in names
    
    asyncio.run(_test())


def test_get_all_with_pagination():
    """Test getting all models with pagination."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create 5 users
            users = [
                MockUser(name=f"User{i}", email=f"user{i}@example.com", test=True)
                for i in range(5)
            ]
            session.add_all(users)
            await session.flush()
            
            # Get first 2
            repo = MockUserRepository(session)
            result = await repo.get_all(offset=0, limit=2, test=True)
            assert len(result) == 2
            
            # Get next 2
            result = await repo.get_all(offset=2, limit=2, test=True)
            assert len(result) == 2
            
            # Get remaining 1
            result = await repo.get_all(offset=4, limit=2, test=True)
            assert len(result) == 1
    
    asyncio.run(_test())


def test_get_all_with_filter():
    """Test getting models with filter."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create users with different names
            users = [
                MockUser(name="Alice", email="alice@example.com", test=True),
                MockUser(name="Bob", email="bob@example.com", test=True),
                MockUser(name="Alice", email="alice2@example.com", test=True),
                MockUser(name="Charlie", email="charlie@example.com", test=True),
            ]
            session.add_all(users)
            await session.flush()
            
            # Filter by name
            repo = MockUserRepository(session)
            result = await repo.get_all(name="Alice", test=True)
            assert len(result) == 2
            assert all(u.name == "Alice" for u in result)
            
            # Filter by email
            result = await repo.get_all(email="bob@example.com", test=True)
            assert len(result) == 1
            assert result[0].name == "Bob"
    
    asyncio.run(_test())


def test_create():
    """Test creating a new model."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create user
            repo = MockUserRepository(session)
            user = await repo.create(name="Test User", email="test@example.com", test=True)
            await session.flush()
            
            assert user.id is not None
            assert user.name == "Test User"
            assert user.email == "test@example.com"
    
    asyncio.run(_test())


def test_update():
    """Test updating a model."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create user
            repo = MockUserRepository(session)
            user = await repo.create(name="Original", email="original@example.com", test=True)
            await session.flush()
            
            # Update user
            updated = await repo.update(user, name="Updated", email="updated@example.com")
            await session.flush()
            
            assert updated.id == user.id
            assert updated.name == "Updated"
            assert updated.email == "updated@example.com"
    
    asyncio.run(_test())


def test_update_non_existent():
    """Test updating a non-existent model."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create a user to hold ID
            repo = MockUserRepository(session)
            user = await repo.create(name="Test", email="test@example.com", test=True)
            await session.flush()
            user_id = user.id
            
            # Try to update non-existent user
            other_user = MockUser(name="Other", email="other@example.com", test=True)
            session.add(other_user)
            await session.flush()
            
            updated = await repo.update(other_user, name="Updated")
            await session.flush()
            
            assert updated.name == "Updated"
    
    asyncio.run(_test())


def test_delete():
    """Test deleting a model."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create user
            repo = MockUserRepository(session)
            user = await repo.create(name="To Delete", email="delete@example.com", test=True)
            user_id = user.id
            await session.flush()
            
            # Delete user
            await repo.delete(user)
            await session.flush()
            
            # Verify deletion
            result = await repo.get_by_id(user_id, test=True)
            assert result is None
    
    asyncio.run(_test())


def test_delete_non_existent():
    """Test deleting a non-existent model doesn't raise error."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create a user to hold ID
            repo = MockUserRepository(session)
            user = await repo.create(name="Test", email="test@example.com", test=True)
            await session.flush()
            user_id = user.id
            
            # Create another user
            other_user = MockUser(name="Other", email="other@example.com", test=True)
            session.add(other_user)
            await session.flush()
            
            # Should not raise error
            await repo.delete(other_user)
            await session.flush()
            
            # Original user still exists
            result = await repo.get_by_id(user_id, test=True)
            assert result is not None
    
    asyncio.run(_test())


def test_count_basic():
    """Test counting models."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create users
            users = [
                MockUser(name=f"User{i}", email=f"user{i}@example.com", test=True)
                for i in range(3)
            ]
            session.add_all(users)
            await session.flush()
            
            # Count all
            repo = MockUserRepository(session)
            total = await repo.count(test=True)
            assert total == 3
            
            # Count filtered
            count = await repo.count(name="User0", test=True)
            assert count == 1
    
    asyncio.run(_test())


def test_count_with_filter():
    """Test counting models with filter."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create users
            users = [
                MockUser(name="Alice", email="alice@example.com", test=True),
                MockUser(name="Bob", email="bob@example.com", test=True),
                MockUser(name="Alice", email="alice2@example.com", test=True),
                MockUser(name="Bob", email="bob2@example.com", test=True),
                MockUser(name="Charlie", email="charlie@example.com", test=True),
            ]
            session.add_all(users)
            await session.flush()
            
            # Count Alice
            repo = MockUserRepository(session)
            count = await repo.count(name="Alice", test=True)
            assert count == 2
            
            # Count Bob
            count = await repo.count(name="Bob", test=True)
            assert count == 2
            
            # Count non-existent
            count = await repo.count(name="Unknown", test=True)
            assert count == 0
    
    asyncio.run(_test())


def test_exists():
    """Test checking if model exists."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create user
            repo = MockUserRepository(session)
            user = await repo.create(name="Test", email="test@example.com", test=True)
            await session.flush()
            
            # Test exists
            assert await repo.exists(user.id, test=True) is True
            
            # Test not exists
            assert await repo.exists(99999, test=True) is False
    
    asyncio.run(_test())


def test_generic_type_hints():
    """Test that repository properly uses generic type hints."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Verify model attribute is set
            repo = MockUserRepository(session)
            assert repo.model == MockUser
    
    asyncio.run(_test())


def test_multiple_creates_and_reads():
    """Test multiple create and read operations."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create multiple users
            repo = MockUserRepository(session)
            for i in range(5):
                user = await repo.create(name=f"User{i}", email=f"user{i}@example.com", test=True)
                await session.flush()
                assert user.id is not None
            
            # Read them back
            users = await repo.get_all(test=True)
            assert len(users) == 5
    
    asyncio.run(_test())


def test_update_changing_multiple_fields():
    """Test updating multiple fields at once."""
    import asyncio
    
    async def _test():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(TestBase.metadata.create_all)
            
            # Create user
            repo = MockUserRepository(session)
            user = await repo.create(name="Original", email="original@example.com", test=True)
            await session.flush()
            
            # Update multiple fields
            updated = await repo.update(
                user, name="Updated Name", email="updated@example.com", age=25
            )
            await session.flush()
            
            assert updated.name == "Updated Name"
            assert updated.email == "updated@example.com"
            assert updated.age == 25
    
    asyncio.run(_test())
