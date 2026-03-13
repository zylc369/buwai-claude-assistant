"""API router module."""

# Import actual routers (using file extensions to match actual files)
from . import projects as projects_router
from . import workspaces as workspaces_router
from . import sessions as sessions_router
from . import messages as messages_router

# Check if events router exists
import os
_events_router_exists = os.path.exists("server/routers/events.py")

__all__ = [
    "projects_router",
    "workspaces_router",
    "sessions_router",
    "messages_router",
    *(["events_router"] if _events_router_exists else [])
]
