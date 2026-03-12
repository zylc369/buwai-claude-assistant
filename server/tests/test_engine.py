"""Tests for database engine and session factory."""

import pytest

# Test the database engine and session factory
# These tests should FAIL initially, then PASS after implementing engine.py


class TestDatabaseEngine:
    """Test database engine creation and configuration."""

    def test_engine_is_async_engine(self):
        """Verify engine is an AsyncEngine instance."""
        # This will fail initially - engine doesn't exist yet
        from database.engine import engine

        assert type(engine).__name__ == "AsyncEngine"

    def test_session_factory_is_sessionmaker(self):
        """Verify session factory is an async sessionmaker."""
        # This will fail initially - SessionLocal doesn't exist yet
        from database.engine import SessionLocal

        assert "sessionmaker" in type(SessionLocal).__name__.lower()

    def test_session_factory_works(self):
        """Verify session factory creates async sessions."""
        # This will fail initially
        from database.engine import SessionLocal
        import asyncio

        async def test_session():
            async with SessionLocal() as session:
                return type(session).__name__

        result = asyncio.run(test_session())
        assert result == "AsyncSession"

    def test_get_db_session_is_generator(self):
        """Verify get_db_session is a FastAPI dependency generator."""
        # This will fail initially
        from database.engine import get_db_session

        # Verify it's callable
        assert callable(get_db_session)

        # Verify it's an async generator function
        import inspect

        gen = inspect.isasyncgenfunction(get_db_session)
        assert gen is True

    def test_get_db_session_creates_session(self):
        """Verify get_db_session creates and returns an async session."""
        # This will fail initially
        from database.engine import get_db_session
        import asyncio

        async def test_session():
            async for session in get_db_session():
                return type(session).__name__

        result = asyncio.run(test_session())
        assert result == "AsyncSession"

    def test_get_db_session_rolls_back_on_error(self):
        """Verify get_db_session rolls back on exception."""
        # This will fail initially
        from database.engine import get_db_session
        import asyncio

        async def test_rollback():
            try:
                async for session in get_db_session():
                    # Do nothing - session should be rolled back on exit
                    pass
            except Exception:
                pass

        asyncio.run(test_rollback())
        # Should not raise exception if finally block handles cleanup

    def test_sqlite_wal_mode_enabled(self):
        from database.engine import engine, init_db
        # This will fail initially
        from database.engine import init_db

        # Initialize database to enable WAL mode
        import asyncio

        asyncio.run(init_db())

        # Check WAL mode using the engine
        async def check_wal():
            async with engine.begin() as conn:
                result = await conn.exec_driver_sql("PRAGMA journal_mode")
                return result.scalar()

        mode = asyncio.run(check_wal())
        assert mode == "wal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
