# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-15
**Commit:** a02750b
**Branch:** main

## OVERVIEW

FastAPI backend with Claude SDK integration. Provides REST API + SSE streaming for AI conversations. Layered architecture: routers → services → repositories.

## STRUCTURE

```
./
├── app.py               # FastAPI app + lifespan + middleware
├── run.py               # Config-driven server startup
├── main.py              # CLI REPL client (legacy)
├── config.py            # Spring Boot-style YAML config loader
├── claude_client.py     # ClaudeClient SDK wrapper
├── pool.py              # ClaudeClientPool with per-session locks
├── database/            # SQLAlchemy async engine + models
├── repositories/        # Data access layer (base.py + 4 repos)
├── services/            # Business logic (6 services)
├── routers/             # API endpoints (6 routers)
├── utils/               # Helpers (id_generator, timestamp)
├── tests/               # pytest suite (29 files, 195 tests)
├── application.yml      # Default config
├── application-dev.yml  # Dev profile
└── application-prod.yml # Prod profile
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `routers/*.py` | FastAPI routers, include in app.py |
| Add business logic | `services/*.py` | Service layer, inject repos |
| Add data access | `repositories/*.py` | Extend BaseRepository |
| Add DB model | `database/models.py` | Inherit Base + TestMixin |
| Modify config | `config.py` + `application*.yml` | Pydantic models + YAML |
| SSE streaming | `services/sse_service.py` | AsyncGenerator pattern |
| Client pooling | `pool.py` | ClaudeClientPool with locks |

## CONVENTIONS

- **Entry point**: `run.py` (config-driven) or `uvicorn app:app` (direct)
- **Config**: YAML with `${VAR:default}` interpolation, `APP_PROFILE` for profiles
- **Env overrides**: `SECTION__KEY=value` (e.g., `SERVER__PORT=9000`)
- **Async DB**: SQLAlchemy 2.0 with `AsyncSession`, WAL mode SQLite
- **Async SDK**: `async with ClaudeClient(config)` required
- **Streaming**: `async for chunk in await client.receive_response()`
- **Test data**: Set `test=True` on model instances for isolation

## ANTI-PATTERNS (THIS PROJECT)

- **Never** instantiate `ClaudeSDKClient` directly - use `ClaudeClient` wrapper
- **Never** skip `async with` context manager - raises RuntimeError
- **Never** run `main.py` without `--cwd` argument
- **Never** hardcode settings path - use `ClaudeClientConfig.settings`
- **Never** commit `app.db` or `*.log` files

## UNIQUE STYLES

- **Spring Boot config**: YAML profiles + env interpolation + Pydantic validation
- **Layered architecture**: Router → Service → Repository pattern
- **Connection pooling**: Per-session locks, idle timeout cleanup
- **Test isolation**: `test=True` column on all models
- **Mock SDK classes**: Test files mirror SDK types for isolation
- **Request ID middleware**: UUID v7 per request, logged with context

## COMMANDS

```bash
# Setup
source .venv/bin/activate
pip install -r requirements.txt

# Run API server
python run.py                          # Config-driven (port from application.yml)
APP_PROFILE=dev python run.py          # Dev profile
SERVER__PORT=9000 python run.py        # Env override
uvicorn app:app --reload --port 8000  # Direct uvicorn

# Run CLI REPL (legacy)
python main.py --cwd .

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Run tests
pytest tests/ -v                       # All tests
pytest tests/test_app.py -v            # Specific file
```

## NOTES

- Requires `ANTHROPIC_API_KEY` env var or in `~/.claude/settings.json`
- SQLite database at `server/app.db` (WAL mode)
- Log files: `server/app-*.log`
- No linter/formatter configured (ruff/black hooks commented in alembic.ini)
- Type checker: basedpyright==1.26.0
- 195 tests across 29 test files
