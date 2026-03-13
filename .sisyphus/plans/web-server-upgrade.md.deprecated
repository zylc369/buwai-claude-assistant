# Web Server Upgrade - Implementation Plan

**Created**: 2026-03-12 (Reconstructed from session.md)
**Status**: Wave 1 Complete, Wave 2 In Progress
**Branch**: main

---

## Project Overview

Transform the Claude SDK Python REPL client into a full-stack web application with:
- **Backend**: FastAPI + SQLAlchemy 2.0 async + SSE
- **Frontend**: Next.js 16 + shadcn/ui + Tailwind v4
- **Architecture**: Session-level connection pooling, ULID identifiers, TDD

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115+
- **ORM**: SQLAlchemy 2.0 async with aiosqlite
- **Migrations**: Alembic
- **Connection Pool**: Custom ClaudeClientPool (session-level)
- **Real-time**: Server-Sent Events (SSE)
- **Session IDs**: ULID format

### Frontend
- **Framework**: Next.js 16.1.6 (App Router)
- **UI Library**: shadcn/ui with base-nova style
- **Styling**: Tailwind CSS v4
- **State Management**: Zustand
- **Data Fetching**: @tanstack/react-query
- **SSE Client**: eventsource

---

## Guardrails

- ⛔ MUST NOT modify `main.py` argument parsing
- ⛔ MUST NOT change ClaudeClient's public interface
- ⛔ MUST NOT add more than 3 error classes
- ⛔ MUST NOT add authentication in Phase 1

---

## Implementation Waves

### ✅ Wave 1: Foundation (COMPLETE)

**Duration**: Completed 2026-03-12
**Status**: All tasks done, tests passing

#### Backend Infrastructure
- [x] ClaudeClientPool implementation (`pool.py`)
  - Per-session locking with asyncio.Lock
  - Idle timeout cleanup (5 min default)
  - Context manager support
- [x] Database engine (`database/engine.py`)
  - Async SQLAlchemy engine with WAL mode
  - Session factory with FastAPI dependency
  - Connection pooling disabled (WAL handles concurrency)
- [x] Data models (`database/models.py`)
  - User, Session, Project, Task models
  - Relationships and cascade rules
- [x] Base repository (`repositories/base.py`)
  - Generic CRUD operations
  - Pagination and filtering
- [x] Directory structure
  - database/, routers/, services/, repositories/
  - All modules importable
- [x] Alembic configuration
  - Async migration support
  - Models referenced in env.py

#### Frontend Infrastructure
- [x] Next.js project initialization
  - TypeScript + Tailwind v4 + ESLint
  - App Router with `app/` directory
- [x] shadcn/ui setup
  - Button, Input, Card components
  - base-nova style, lucide icons
- [x] Layout components
  - AppLayout, TopBar, Sidebar
  - Dark mode with `.dark` class
- [x] Dependencies installed
  - @tanstack/react-query, zustand, eventsource

#### Test Coverage
- [x] test_pool.py (19 tests)
- [x] test_base_repository.py (comprehensive)
- [x] test_engine.py (7 tests)
- [x] test_structure.py (19 tests)
- [x] test_claude_client.py
- [x] test_main.py

---

### 🔄 Wave 2: Backend Business Logic (IN PROGRESS)

**Duration**: Est. 2-3 hours
**Dependencies**: Wave 1 complete

#### 2.1 Concrete Repositories
- [ ] Create `repositories/user_repository.py`
  - Inherit from BaseRepository[User]
  - Add user-specific queries (by_email, by_username)
  - TDD: Write tests first
  
- [ ] Create `repositories/session_repository.py`
  - Inherit from BaseRepository[Session]
  - Add session-specific queries (by_token, valid_sessions)
  - TDD: Write tests first

- [ ] Create `repositories/project_repository.py`
  - Inherit from BaseRepository[Project]
  - Add project-specific queries (by_owner)
  - TDD: Write tests first

- [ ] Create `repositories/task_repository.py`
  - Inherit from BaseRepository[Task]
  - Add task-specific queries (by_project, by_assignee)
  - TDD: Write tests first

#### 2.2 Service Layer
- [ ] Create `services/user_service.py`
  - Business logic for user operations
  - Dependency injection of UserRepository
  - Error handling
  
- [ ] Create `services/session_service.py`
  - Session creation, validation, cleanup
  - ULID generation
  - Token management

- [ ] Create `services/project_service.py`
  - Project CRUD with owner validation
  - Cascade delete logic

- [ ] Create `services/task_service.py`
  - Task CRUD with project/assignee validation
  - Status transitions

#### 2.3 API Routers
- [ ] Create `routers/users.py`
  - GET /users - List users
  - POST /users - Create user
  - GET /users/{id} - Get user
  - PUT /users/{id} - Update user
  - DELETE /users/{id} - Delete user

- [ ] Create `routers/sessions.py`
  - POST /sessions - Create session
  - GET /sessions/{id} - Get session
  - DELETE /sessions/{id} - End session

- [ ] Create `routers/projects.py`
  - Full CRUD endpoints
  - Owner validation

- [ ] Create `routers/tasks.py`
  - Full CRUD endpoints
  - Project/assignee validation

#### 2.4 FastAPI Application
- [ ] Create `server/app.py` (FastAPI main)
  - Initialize FastAPI app
  - Include all routers
  - CORS configuration
  - Exception handlers
  - Lifespan events (init_db)

- [ ] Create SSE endpoint
  - GET /events - SSE stream
  - Event types: task_update, project_update
  - Connection management

#### 2.5 Database Migration
- [ ] Generate initial migration
  ```bash
  cd server
  alembic revision --autogenerate -m "Initial tables"
  ```
- [ ] Apply migration
  ```bash
  alembic upgrade head
  ```

---

### ⏳ Wave 3: Frontend Business Logic (PENDING)

**Duration**: Est. 3-4 hours
**Dependencies**: Wave 2 complete

#### 3.1 API Client Layer
- [ ] Create `web/lib/api/client.ts`
  - Base fetch wrapper with error handling
  - TypeScript types for API responses

- [ ] Create `web/lib/api/users.ts`
  - User CRUD operations

- [ ] Create `web/lib/api/projects.ts`
  - Project CRUD operations

- [ ] Create `web/lib/api/tasks.ts`
  - Task CRUD operations

- [ ] Create `web/lib/api/sse.ts`
  - SSE connection management
  - Event parsing

#### 3.2 State Management
- [ ] Create `web/stores/userStore.ts`
  - Current user state
  - User list cache

- [ ] Create `web/stores/projectStore.ts`
  - Projects state
  - Selected project

- [ ] Create `web/stores/taskStore.ts`
  - Tasks state
  - Filters

#### 3.3 React Query Setup
- [ ] Configure QueryClient
- [ ] Create query hooks
  - useUsers, useProjects, useTasks
- [ ] Create mutation hooks
  - useCreateProject, useUpdateTask, etc.

#### 3.4 Page Components
- [ ] `web/app/users/page.tsx`
  - User list with CRUD
  
- [ ] `web/app/projects/page.tsx`
  - Project list with CRUD
  - Project detail view

- [ ] `web/app/tasks/page.tsx`
  - Task list with filters
  - Task CRUD
  - Real-time updates via SSE

---

### ⏳ Wave 4: Integration & Testing (PENDING)

**Duration**: Est. 2 hours
**Dependencies**: Wave 3 complete

#### 4.1 CORS Configuration
- [ ] Configure FastAPI CORS for localhost:3000
- [ ] Test cross-origin requests

#### 4.2 End-to-End Testing
- [ ] Test user creation → session creation
- [ ] Test project CRUD
- [ ] Test task CRUD with SSE updates
- [ ] Test error scenarios

#### 4.3 Error Handling
- [ ] Backend error responses (JSON format)
- [ ] Frontend error boundaries
- [ ] Loading states

---

### ⏳ Wave 5: Documentation & Cleanup (PENDING)

**Duration**: Est. 1 hour
**Dependencies**: Wave 4 complete

#### 5.1 Documentation
- [ ] Update README.md with setup instructions
- [ ] Document API endpoints
- [ ] Document environment variables

#### 5.2 Code Quality
- [ ] Run linters (basedpyright, ESLint)
- [ ] Format code (Black, Prettier)
- [ ] Remove unused dependencies

#### 5.3 Final Verification
- [ ] All tests passing
- [ ] Build succeeds (backend + frontend)
- [ ] Manual testing complete

---

## Key Patterns & Learnings

### Backend
- **Per-session locks**: `Dict[str, asyncio.Lock]` for session isolation
- **WAL mode**: SQLite concurrent access without connection pooling
- **Generic repositories**: `BaseRepository[ModelType]` pattern
- **TDD**: Write tests before implementation

### Frontend
- **Tailwind v4**: Use `"class"` string for darkMode, not array
- **Client components**: All interactive components need `"use client"`
- **Import aliases**: `@/` mapped via tsconfig.json
- **suppressHydrationWarning**: Prevent dark mode hydration issues

---

## Running the Application

### Backend
```bash
cd server
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app:app --reload
```

### Frontend
```bash
cd web
npm install
npm run dev
```

---

## Notes

- No authentication in Phase 1 (per guardrails)
- Demo mode fallback if Claude SDK import fails
- SQLite WAL mode for concurrency support
- SSE for real-time updates (not WebSockets)
