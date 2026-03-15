# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-15
**Commit:** a02750b
**Branch:** main

## OVERVIEW

Full-stack Claude Assistant application with FastAPI backend and Next.js frontend. Python backend provides REST API + SSE streaming with Claude SDK integration. TypeScript frontend offers React-based UI with TanStack Query.

## STRUCTURE

```
./
├── server/           # Python backend (FastAPI + Claude SDK)
├── web/              # Next.js frontend (React 19 + TanStack Query)
└── docs/             # Requirements docs (Chinese) + SDK guide
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Start backend API | `server/run.py` | Config-driven: `python run.py` |
| Start backend CLI | `server/main.py` | REPL mode: `--cwd .` required |
| Start frontend | `web/` | `npm run dev` (port 3000) |
| Backend endpoints | `server/routers/` | REST + SSE endpoints |
| Backend services | `server/services/` | Business logic layer |
| Backend repos | `server/repositories/` | Data access layer |
| Frontend API | `web/lib/api/` | API client + types |
| Frontend hooks | `web/hooks/` | React Query hooks |
| Database models | `server/database/models.py` | SQLAlchemy ORM |
| Run tests | `server/tests/` | pytest (195 tests) |

## CONVENTIONS

- **Backend entry**: `server/run.py` (config-driven) or `uvicorn app:app` (direct)
- **Frontend entry**: `web/app/` (Next.js App Router)
- **API base URL**: Backend at :8000, Frontend at :3000
- **Config format**: YAML with `${VAR:default}` interpolation (Spring Boot style)
- **Async pattern**: `async with ClaudeClient(config)` required for SDK
- **Path alias**: `@/*` maps to `web/` root in TypeScript

## ANTI-PATTERNS (THIS PROJECT)

- **Never** run `main.py` without `--cwd` argument
- **Never** instantiate `ClaudeSDKClient` directly - use `ClaudeClient` wrapper
- **Never** skip `async with` context manager for ClaudeClient
- **Never** commit `server/.venv/` or `web/node_modules/`
- **Never** hardcode settings path - use config system

## UNIQUE STYLES

- **Layered backend**: routers → services → repositories pattern
- **Spring Boot config**: `application.yml` with profiles (dev/prod)
- **Connection pooling**: `ClaudeClientPool` with per-session locks
- **SSE streaming**: AsyncGenerator + StreamingResponse for real-time
- **Test isolation**: `test=True` flag on all DB models
- **Mock SDK classes**: Test suite mirrors SDK types for isolation

## COMMANDS

```bash
# Backend (from server/)
cd server && source .venv/bin/activate
python run.py                          # Start API (config-driven)
uvicorn app:app --reload --port 8000  # Start API (direct)
python main.py --cwd .                 # CLI REPL mode
pytest tests/ -v                       # Run tests

# Frontend (from web/)
cd web && npm install
npm run dev                            # Dev server (port 3000)
npm run build                          # Production build
npm test                               # Vitest
```

## NOTES

- Requires `ANTHROPIC_API_KEY` env var or in `~/.claude/settings.json`
- Backend uses SQLite with WAL mode (`server/app.db`)
- Frontend uses bun (bun.lock present)
- Config profiles: `APP_PROFILE=dev` or `APP_PROFILE=prod`
- Env overrides: `SERVER__PORT=9000` (double underscore syntax)
- No CI/CD configured yet
- See `server/AGENTS.md` for backend details, `web/AGENTS.md` for frontend
