"""Tests for FastAPI app endpoints."""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database.models import Base
from database import get_db_session


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
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
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def app(test_session: AsyncSession):
    """Create FastAPI app with test database override."""
    from app import app as fastapi_app
    from database import get_db_session
    
    # Override the database dependency to use test session
    async def override_get_db():
        yield test_session
    
    fastapi_app.dependency_overrides[get_db_session] = override_get_db
    
    yield fastapi_app
    
    # Clean up override
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root_returns_info(self, client: AsyncClient):
        """Test root endpoint returns server info."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Claude Assistant Web Server"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check returns healthy status."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestDocsEndpoint:
    """Tests for API documentation endpoint."""

    @pytest.mark.asyncio
    async def test_docs_accessible(self, client: AsyncClient):
        """Test that API docs are accessible."""
        response = await client.get("/docs")
        
        assert response.status_code == 200
