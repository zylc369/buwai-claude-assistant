"""Database engine and session factory for SQLAlchemy 2.0 async."""

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Default database path - can be overridden via environment variable or config
DEFAULT_DATABASE_PATH = Path(__file__).parent.parent / "app.db"
DATABASE_PATH = Path(__name__).parent.parent / "app.db"
#VP|
#HX|# Add code to enable SQLite WAL mode for concurrency support
async def _enable_wal_mode() -> None:
    """Enable SQLite WAL mode for better concurrency support."""
    async with engine.begin() as conn:
        result = await conn.exec_driver_sql("PRAGMA journal_mode")
        mode = result.scalar()
        if mode != "wal":
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL")


async def init_db() -> None:
    """Initialize database with default configuration."""
    await _enable_wal_mode()

# Create async engine with SQLite configuration
# NO connection pooling for SQLite (handled by WAL mode for concurrency)
engine: AsyncEngine = create_async_engine(
    "sqlite+aiosqlite:///" + str(DATABASE_PATH),
    echo=False,  # Set to True for SQL logging during development
    future=True,  # Use SQLAlchemy 2.0 style
    connect_args={"check_same_thread": False},  # Allow multiple threads
)

# Create async session factory
# expire_on_commit=False to avoid lazy loading issues
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting async database sessions.

    This function:
    - Creates a new session
    - Yields it to the caller
    - Rolls back any changes on error
    - Closes and cleans up the session on completion

    Usage in FastAPI:
        @app.get("/items/")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            return await db.execute(select(Item))
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
