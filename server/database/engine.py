"""Database engine and session factory for SQLAlchemy 2.0 async."""

from typing import AsyncGenerator

from config import get_config
from logger import get_logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = get_logger(__name__)


def _get_database_url() -> str:
    """Get database URL from configuration."""
    config = get_config()
    url = config.database.url
    redacted_url = url.split('//')[-1].split('?')[0] if '//' in url else url
    logger.info(f"Database URL: {redacted_url}")
    return url


async def _enable_wal_mode() -> None:
    """Enable SQLite WAL mode for better concurrency support."""
    async with engine.begin() as conn:
        result = await conn.exec_driver_sql("PRAGMA journal_mode")
        mode = result.scalar()
        if mode != "wal":
            logger.info(f"Enabling WAL mode (current: {mode})")
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            logger.info("WAL mode enabled successfully")
        else:
            logger.debug("WAL mode already enabled")


async def init_db() -> None:
    """Initialize database with default configuration."""
    logger.info("Initializing database...")
    await _enable_wal_mode()
    logger.info("Database initialized successfully")

# Create async engine with SQLite configuration
# NO connection pooling for SQLite (handled by WAL mode for concurrency)
engine: AsyncEngine = create_async_engine(
    _get_database_url(),
    echo=get_config().database.echo,
    future=True,
    connect_args={"check_same_thread": False},
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
        logger.debug("Database session created")
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error, rolling back: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()
