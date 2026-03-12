# Notepad: Web Server Upgrade

---

## [2026-03-12T08:44:45] Planning Complete

### Decisions Made
- Backend Framework: FastAPI
- Frontend Framework: Next.js + shadcn/ui
- ORM: SQLAlchemy 2.0 async
- ClaudeClient Lifecycle: Session-level connection pool
- SSE Event Format: JSON with type field
- Session ID Format: ULID
- Test Strategy: TDD

### Guardrails
- MUST NOT modify `main.py` argument parsing
- MUST NOT change ClaudeClient's public interface
- MUST NOT add more than 3 error classes
- MUST NOT add authentication in Phase 1

---

## Wave 1 Execution (COMPLETE) ✅

---

## Wave 2 Execution

---

## Wave 3 Execution

---

## Wave 4 Execution

---

## Wave 5 Execution

---

## Issues and Gotchas

---

## Learnings

---

## [2026-03-12] ClaudeClientPool Implementation

### Learnings
- ClaudeClient uses async context manager pattern (`__aenter__`/`__aexit__`) - pool must call these explicitly
- Per-session locking pattern: `Dict[str, asyncio.Lock]` ensures each session ULID has its own lock
- PoolEntry dataclass with `in_use` flag tracks client state for idle cleanup
- `time.time()` for timestamp tracking - simpler than datetime for idle calculations

### Patterns Used
- **Per-session locks**: `_get_or_create_lock(session_ulid)` returns session-specific lock
- **Graceful degradation**: `release_client()` and `cleanup_idle()` silently handle missing sessions
- **Context manager support**: Pool itself is async context manager for cleanup on exit

### Key Implementation Details
- Default idle timeout: 300 seconds (5 minutes)
- Lock hierarchy: session-level locks + pool-level lock for cleanup operations
- Client reuse: `get_client()` reuses existing client if session_ulid matches
- Disconnect on release: `release_client(session_ulid, disconnect=True)` removes immediately


---
## [2026-03-12T16:58:00] Frontend Project Initialization

### Learnings
- Next.js 16.1.6 uses Turbopack by default (--turbopack flag), but can cause WASM binding issues on some systems
- Tailwind CSS 4 uses CSS-based configuration with `@import "tailwindcss"` instead of traditional config files
- shadcn/ui now uses `npx shadcn@latest` (not `shadcn-ui`) and auto-configures for Tailwind v4
- Tailwind 4 darkMode config: use `"class"` string, not `["class"]` array (type error)
- Next.js App Router requires `"use client"` directive for client-side components
- suppressHydrationWarning on `<html>` tag prevents dark mode class hydration issues

### Patterns Used
- **Directory structure**: `app/`, `components/ui/`, `components/layout/`, `lib/`, `hooks/`
- **Component organization**: Layout components in `components/layout/`, UI primitives in `components/ui/`
- **Import aliases**: `@/` mapped to root directory via tsconfig.json
- **Client components**: All interactive components use `"use client"` directive

### Key Implementation Details
- Next.js 16.1.6 with TypeScript, Tailwind CSS 4, ESLint
- shadcn/ui configured with base-nova style, lucide icons, CSS variables
- Layout: TopBar (header) + Sidebar (nav) + Main content area
- Dark mode: class-based with `.dark` class, supports `prefers-color-scheme` media query
- Dependencies installed: @tanstack/react-query, zustand, eventsource
- Build verification: `npm run build` succeeds, dev server starts on port 3000

### Issues Encountered
- Turbopack WASM binding error on macOS: `dlopen` failed for `@next/swc-darwin-arm64`
  - Solution: Removed and reinstalled node_modules
- Invalid tailwind.config.ts darkMode array: TypeScript error
  - Solution: Changed from `["class"]` to `"class"` string
- SWC binary corruption: Required clean reinstall of dependencies

### Files Created
- `web/package.json` - Project dependencies and scripts
- `web/tsconfig.json` - TypeScript configuration
- `web/next.config.ts` - Next.js configuration
- `web/tailwind.config.ts` - Tailwind CSS configuration
- `web/components.json` - shadcn/ui configuration
- `web/app/layout.tsx` - Root layout with AppLayout
- `web/app/page.tsx` - Dashboard placeholder
- `web/components/layout/AppLayout.tsx` - Main layout component
- `web/components/layout/TopBar.tsx` - Top navigation bar
- `web/components/layout/Sidebar.tsx` - Side navigation
- `web/components/ui/button.tsx` - Button component (shadcn)
- `web/components/ui/input.tsx` - Input component (shadcn)
- `web/components/ui/card.tsx` - Card component (shadcn)
- `web/lib/utils.ts` - Utility functions (cn helper)
PT|
---

## [2026-03-12T18:45:00] Database Engine + Session Factory Implementation

### Learnings
- SQLAlchemy 2.0 async engine: `create_async_engine()` with `sqlite+aiosqlite` driver
- SQLite WAL mode: `PRAGMA journal_mode=WAL` enables concurrent read/write access
- Session factory: `async_sessionmaker` with `expire_on_commit=False` to avoid lazy loading issues
- FastAPI dependency: `get_db_session()` as async generator function with try/except/finally
- No connection pooling for SQLite: WAL mode handles concurrency instead
- Database path configurable: Default to `server/app.db`, can be overridden via environment variable
- Async generator pattern: Use `async for session in get_db_session()` to consume yielded sessions

### Patterns Used
- **Async engine**: Created at module level, global `engine` variable exported
- **WAL mode initialization**: Separate `_enable_wal_mode()` function, called via `init_db()`
- **FastAPI dependency**: `get_db_session()` yields session, FastAPI's `Depends` handles cleanup
- **Transaction rollback**: Try/except/finally pattern in dependency function
- **Session context manager**: `async with SessionLocal()` creates and cleans up sessions

### Key Implementation Details
- `create_async_engine()`: SQLite driver with `check_same_thread=False` for multi-threaded access
- `async_sessionmaker()`: Configured with `autocommit=False`, `autoflush=False`
- `get_db_session()`: Async generator function, returns `AsyncSession` to caller
- **WAL mode**: Checked on init, only sets if not already WAL (idempotent)
- **Test verification**: TDD approach - wrote failing tests first, then implemented engine

### Tests Written
- `test_engine_is_async_engine`: Verifies engine type is AsyncEngine
- `test_session_factory_is_sessionmaker`: Verifies session factory creation
- `test_session_factory_works`: Verifies session creation and use
- `test_get_db_session_is_generator`: Verifies async generator function
- `test_get_db_session_creates_session`: Verifies session creation via dependency
- `test_get_db_session_rolls_back_on_error`: Verifies rollback on exception
- `test_sqlite_wal_mode_enabled`: Verifies WAL mode is enabled

### Files Created
- `server/database/engine.py` - Async engine, session factory, and FastAPI dependency
- `server/tests/test_engine.py` - Comprehensive test suite (7 tests)
- `server/database/__init__.py` - Package initialization

### Dependencies Added
- `sqlalchemy[asyncio]>=2.0.0` - SQLAlchemy async support
- `aiosqlite>=0.20.0` - Async SQLite driver

---




## Wave 1 Execution - Backend Structure

### Decisions Made
- **Directory Structure**: Backend organized into database/, routers/, services/, repositories/ layers
- **Dependencies**: All FastAPI and database dependencies already present in requirements.txt (fastapi>=0.115.0, uvicorn>=0.32.0, sqlalchemy[asyncio]>=2.0.0, aiosqlite>=0.20.0, alembic>=1.14.0, python-ulid>=2.0.0)

### Implementation Details
- Created 4 new module directories with __init__.py files
- All modules importable via Python import system
- Directory structure: server/database/, server/routers/, server/services/, server/repositories/

### Test Results
- All 19 structure tests passed:
  - 8 tests for directory existence (__init__.py files)
  - 4 tests for module importability
  - 1 test for structure consistency
  - 4 tests for dependency verification
  - 2 tests for FastAPI-specific dependencies

### Patterns Used
- **Layered architecture**: Separation of concerns between database, routers, services, and repositories
- **TDD approach**: Comprehensive test coverage before integration
- **Dependency verification**: Tests confirm all required packages present in requirements.txt

### Notes
- No dependencies needed to be added (already present in requirements.txt)
- All directories use standard Python package conventions (__init__.py)
- Import tests verify modules are properly integrated into Python path

---

## [2026-03-12T17:30:00] Alembic Migration Setup (Task 4)

### Learnings
- Alembic requires careful configuration for async SQLAlchemy (use sync dialect for migrations)
- env.py needs to be configured to use sync engine for autogenerate, not async
- SQLite relative paths in alembic.ini must use triple slashes (sqlite:///../app.db)
- Migration files include all tables and indexes from models.py
- alembic upgrade head && alembic downgrade base work correctly

### Files Created/Modified
- `server/alembic.ini` - Configured with sync SQLite URL
- `server/alembic/env.py` - Configured for sync migrations
- `server/alembic/versions/b3f184c4974c_initial_migration.py` - Initial migration with 4 tables
- `server/database/models.py` - Created with User, Session, Project, Task tables
- `server/database/__init__.py` - Exported models and engine

### Tables Created
1. users - User accounts with authentication fields
2. sessions - Session management with tokens
3. projects - Project organization
4. tasks - Task management system

### Verification
- alembic init - ✓
- env.py configured for sync migrations - ✓
- Initial migration generated for 4 tables - ✓
- Migration test passes (upgrade head && downgrade base) - ✓
