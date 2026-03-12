"""API router module."""

from .users import router as users_router
from .sessions import router as sessions_router
from .projects import router as projects_router
from .tasks import router as tasks_router

__all__ = [
    "users_router",
    "sessions_router",
    "projects_router",
    "tasks_router"
]
