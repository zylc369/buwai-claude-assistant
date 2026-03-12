"""FastAPI application main entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import (
    users_router,
    sessions_router,
    projects_router,
    tasks_router
)
from routers.events import router as events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title="Claude Assistant Web Server",
    description="Web API for Claude Assistant with user management, projects, and tasks",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router)
app.include_router(sessions_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(events_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Claude Assistant Web Server",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
