"""FastAPI application main entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from config import get_config
from utils.id_generator import generate_uuidv7
from database import init_db
from logger import setup_logging, shutdown_logging, set_request_id, reset_request_id, get_logger
from routers.projects import router as projects_router
from routers.sessions import router as sessions_router
from routers.workspaces import router as workspaces_router
from routers.messages import router as messages_router
from routers.ai_resources import router as ai_resources_router
try:
    from routers.events import router as events_router
except ImportError:
    events_router = None

_logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or generate_uuidv7()[:8]
        token = set_request_id(request_id)
        try:
            _logger.info(f"Request started: {request.method} {request.url.path}")
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            _logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code}")
            return response
        except Exception as e:
            _logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)}")
            raise
        finally:
            reset_request_id(token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _logger.info("Application starting up")
    setup_logging(get_config().logging)
    await init_db()
    _logger.info("Database initialized")
    yield
    _logger.info("Application shutting down")
    shutdown_logging()


# Load configuration
config = get_config()

# Create FastAPI application
app = FastAPI(
    title="Claude Assistant Web Server",
    description="Web API for Claude Assistant with user management, projects, and tasks",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS from application.yml
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors.origins,
    allow_credentials=config.server.cors.allow_credentials,
    allow_methods=config.server.cors.allow_methods,
    allow_headers=config.server.cors.allow_headers,
)

app.add_middleware(RequestIDMiddleware)

# Include routers
app.include_router(projects_router)
app.include_router(sessions_router)
app.include_router(workspaces_router)
app.include_router(messages_router)
app.include_router(ai_resources_router)
if events_router:
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
