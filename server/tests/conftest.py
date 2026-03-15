"""Pytest configuration and fixtures for repository tests."""

import os
import shutil
import pytest
import pytest_asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database.models import Base
from config import get_config


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
PROJECTS_ROOT = get_config().projects.root


@pytest.fixture(scope="session", autouse=True)
def cleanup_projects_root():
    if os.path.exists(PROJECTS_ROOT):
        shutil.rmtree(PROJECTS_ROOT)
    yield
    if os.path.exists(PROJECTS_ROOT):
        shutil.rmtree(PROJECTS_ROOT)


@pytest_asyncio.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create a test database session."""
    SessionLocal = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with SessionLocal() as session:
        yield session
