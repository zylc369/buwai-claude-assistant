# AI Resource Management System - Work Plan

**Generated:** 2026-03-15
**Status:** Ready for Implementation

---

## 1. User Confirmed Requirements

### Database
- **New table**: `ai_resource`
- **Fields**: id, resource_unique_id (UUIDv7), name, type, sub_type, owner, disabled, content (JSON), gmt_create, gmt_modified, test
- **No changes** to workspace table (inited field removed)

### Configuration
- Config section: `ai_resources` in application*.yml
- Settings: root_dir, refresh_interval_ms
- Dev: 30s, Prod: 10min

### AI Resource Sync Logic
- **Trigger**: Before ClaudeClient call, once per request
- **Condition**: workspace.latest_active_time expired OR never synced
- **Query**: owner IS NULL OR owner='' OR owner=workspace.directory, test=false
- **Write**: Atomic (temp file + rename)
- **Paths**: owner=null → ~/.claude/, owner=X → [ai_resource_root]/X/
- **Symlinks**: Create after sync if not exists

### Backend API
- CRUD: /ai-resources/
- No permission validation

### Frontend
- Route: /ai-resources
- Stack: Next.js 16 + React 19 + React Query + Zustand

---

## 2. Critical Gaps (Metis)

| Gap | Resolution |
|-----|------------|
| Deleted resources not removed from disk | Add sync logic to delete orphan files |
| Concurrent sync requests | Add sync-in-progress lock per workspace |
| Malformed content JSON | Validate at API layer with Pydantic |
| Symlink exists as directory | Check and skip if not symlink |
| Empty string vs null owner | Both treated as global |
| Invalid content type | Default to MD if unknown |
| Special chars in name | Sanitize filename before write |

---

## 3. Work Breakdown

### Phase 1: Database Layer
**Files**: database/models.py, alembic/versions/xxx.py

Tasks:
- [x] Add AiResource model (inherit TestMixin)
- [x] Generate Alembic migration
- [x] Run migration

**QA**: ✅ Model import OK, table created in DB

---

### Phase 2: Repository Layer
**Files**: repositories/ai_resource_repository.py, repositories/__init__.py

Tasks:
- [x] Create AiResourceRepository (inherit BaseRepository)
- [x] Add get_by_owner_query method
- [x] Add get_global_resources method

**QA**: ✅ Repository created with query methods

---

### Phase 3: Service Layer
**Files**: services/ai_resource_service.py, services/__init__.py

Tasks:
- [x] Create AiResourceService with CRUD methods
- [x] Add sync_ai_resources method (core sync logic)
- [x] Add _should_sync helper
- [x] Add _write_resource_files helper
- [x] Add _create_symlinks helper
- [x] Add _read_system_prompts helper

**QA**: ✅ Service layer created with sync logic

---

### Phase 4: Router Layer
**Files**: routers/ai_resources.py, app.py

Tasks:
- [x] Create router with CRUD endpoints
- [x] Add Pydantic models (Create/Update/Response)
- [x] Register router in app.py

**QA**: ✅ Router layer created with CRUD endpoints

---

### Phase 5: Sync Integration
**Files**: services/message_service.py, config.py, application*.yml

Tasks:
- [x] Add AIResourcesConfig to config.py
- [x] Update application.yml, application-dev.yml, application-prod.yml
- [x] Add sync call in message_service before ClaudeClient
- [x] Add sync lock mechanism

**QA**: ✅ Sync integrated with lock mechanism

---

### Phase 6: Frontend
**Files**: lib/api/types.ts, lib/api/client.ts, hooks/useAIResources.ts, app/ai-resources/page.tsx

Tasks:
- [x] Add TypeScript types
- [x] Add API client methods
- [x] Create React Query hooks (完整实现已验证）
- [x] Create AI resources page
- [x] Add navigation link

**QA**: ✅ 前端全部完成

---

## 4. Sync Logic Details

```
sync_ai_resources(workspace):
  1. Check should_sync(workspace)
     - Never synced: query ai_resource where owner=workspace.directory
     - Time expired: latest_active_time + refresh_interval < now

  2. Get resources from DB
     WHERE (owner IS NULL OR owner='' OR owner=workspace.directory)
       AND test=false
       AND disabled=false

  3. For each resource:
     - Build path: [root]/[owner or "global"]/[type_dir]/[sub_type]/[name].[ext]
     - Write content atomically (temp + rename)

  4. Delete orphan files (on disk but not in DB)

  5. Create symlinks:
     - [root]/[owner]/skills → [workspace]/.claude/skills
     - [root]/[owner]/commands → [workspace]/.claude/commands

  6. Read system prompts and merge

  7. Return merged system_prompt
```

---

## 5. Acceptance Criteria

| # | Criteria | How to Verify |
|---|----------|---------------|
| 1 | Model exists with all fields | `pytest tests/test_ai_resource_model.py` |
| 2 | Repository CRUD works | `pytest tests/test_ai_resource_repository.py` |
| 3 | Sync creates files correctly | `pytest tests/test_ai_resource_sync.py -k "creates_files"` |
| 4 | Sync respects interval | `pytest tests/test_ai_resource_sync.py -k "respects_interval"` |
| 5 | Atomic write works | `pytest tests/test_ai_resource_sync.py -k "atomic"` |
| 6 | Symlinks created | `pytest tests/test_ai_resource_sync.py -k "symlink"` |
| 7 | API CRUD works | `curl -X POST http://localhost:8000/ai-resources/ ...` |
| 8 | Frontend loads | Visit /ai-resources |
| 9 | Full integration works | Create resource → Sync → ClaudeClient uses it |

---

## 6. Task Dependency Graph

```
Phase 1: Database Layer
    │
    ├── T1.1: Add AiResource model ──────────────┐
    ├── T1.2: Generate Alembic migration ────────┤
    └── T1.3: Run migration ─────────────────────┘
                                                │
                                                ▼
Phase 2: Repository Layer                       │
    │                                           │
    ├── T2.1: Create AiResourceRepository ◄─────┤ (depends on T1)
    ├── T2.2: Add get_by_owner_query            │
    └── T2.3: Add get_global_resources          │
                                                │
            ┌───────────────────────────────────┤
            ▼                                   ▼
Phase 3: Service Layer              Phase 4: Router Layer
    │                                   │
    ├── T3.1: Create AiResourceService  ├── T4.1: Create router
    ├── T3.2: Add sync_ai_resources     ├── T4.2: Add Pydantic models
    ├── T3.3: Add _should_sync          └── T4.3: Register in app.py
    ├── T3.4: Add _write_resource_files
    ├── T3.5: Add _create_symlinks      (parallel with Phase 3)
    └── T3.6: Add _read_system_prompts
                                                │
            ┌───────────────────────────────────┘
            ▼
Phase 5: Sync Integration
    │
    ├── T5.1: Add AIResourcesConfig ◄─── (depends on T3 + T4)
    ├── T5.2: Update application*.yml
    ├── T5.3: Add sync call in message_service
    └── T5.4: Add sync lock mechanism
                                                │
                                                ▼
Phase 6: Frontend                               │
    │                                           │
    ├── T6.1: Add TypeScript types ◄────────────┤ (depends on T4 API)
    ├── T6.2: Add API client methods            │
    ├── T6.3: Create React Query hooks          │
    ├── T6.4: Create AI resources page          │
    └── T6.5: Add navigation link               │
```

---

## 7. Parallel Execution Graph

### Wave 1 (Sequential)
| Task ID | Description | Dependencies |
|---------|-------------|--------------|
| T1.1 | Add AiResource model | - |
| T1.2 | Generate Alembic migration | T1.1 |
| T1.3 | Run migration | T1.2 |
| T2.1 | Create AiResourceRepository | T1.3 |
| T2.2 | Add get_by_owner_query | T2.1 |
| T2.3 | Add get_global_resources | T2.1 |

### Wave 2 (Parallel: Phase 3 + Phase 4)
| Task ID | Description | Dependencies |
|---------|-------------|--------------|
| T3.1 | Create AiResourceService | T2.3 |
| T3.2 | Add sync_ai_resources | T3.1 |
| T3.3-T3.6 | Helper methods | T3.1 |
| **T4.1** | **Create router (parallel)** | **T2.3** |
| T4.2 | Add Pydantic models | T4.1 |
| T4.3 | Register in app.py | T4.1 |

### Wave 3 (Sequential)
| Task ID | Description | Dependencies |
|---------|-------------|--------------|
| T5.1 | Add AIResourcesConfig | T3.6, T4.3 |
| T5.2 | Update application*.yml | T5.1 |
| T5.3 | Add sync call | T5.2 |
| T5.4 | Add sync lock | T5.3 |

### Wave 4 (Parallel with late Wave 3)
| Task ID | Description | Dependencies |
|---------|-------------|--------------|
| T6.1 | Add TypeScript types | T4.3 (API exists) |
| T6.2 | Add API client methods | T6.1 |
| T6.3 | Create React Query hooks | T6.2 |
| T6.4 | Create AI resources page | T6.3 |
| T6.5 | Add navigation link | T6.4 |

---

## 8. Category + Skills Recommendations

| Phase | Category | Skills | Rationale |
|-------|----------|--------|-----------|
| Phase 1 | `quick` | - | Single model file, standard pattern |
| Phase 2 | `quick` | - | Repository pattern, copy existing |
| Phase 3 | `deep` | - | Complex sync logic, needs thorough implementation |
| Phase 4 | `quick` | - | Standard CRUD router pattern |
| Phase 5 | `deep` | - | Integration with message_service, async patterns |
| Phase 6 | `visual-engineering` | `frontend-ui-ux` | Frontend UI work |

---

## 9. Technical Implementation Details

### Content JSON Validation (Pydantic)
```python
# schemas/ai_resource.py
from pydantic import BaseModel
from typing import Literal

class ContentSchema(BaseModel):
    type: Literal["MD", "SHELL"]
    data: str

class AIResourceCreate(BaseModel):
    name: str
    type: Literal["SKILL", "COMMAND", "SYSTEM_PROMPT"]
    sub_type: str = ""
    owner: str | None = None
    disabled: bool = False
    content: ContentSchema
    test: bool = False
```

### Atomic Write Pattern
```python
import tempfile
import os

async def _write_atomically(filepath: Path, content: str):
    # Write to temp file first
    fd, temp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix='.tmp_',
        suffix=filepath.suffix
    )
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        # Atomic rename
        os.rename(temp_path, str(filepath))
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
```

### Filename Sanitization
```python
import re

def sanitize_filename(name: str) -> str:
    # Remove path traversal and special chars
    name = re.sub(r'[^\w\-_.]', '_', name)
    name = re.sub(r'\.{2,}', '_', name)  # No ..
    name = name.strip('._')[:255]  # Max filename length
    return name or 'unnamed'
```

### Symlink Creation with Safety
```python
import os
from pathlib import Path

def _create_symlink_safe(target: Path, link: Path):
    link = link.resolve()
    if link.exists():
        if link.is_symlink():
            return  # Already exists as symlink
        # Exists as file/dir, don't overwrite
        logger.warning(f"Symlink target exists as non-symlink: {link}")
        return
    
    target = target.resolve()
    if not target.exists():
        logger.warning(f"Symlink target directory missing: {target}")
        return
    
    link.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(str(target), str(link))
```

---

## 10. Test Plan

### Backend Tests
```
server/tests/
├── test_ai_resource_model.py
├── test_ai_resource_repository.py
├── test_ai_resource_service.py
├── test_ai_resource_api.py
└── test_ai_resource_sync.py
```

### Frontend Tests
```
web/tests/
├── useAIResources.test.ts
└── AIResourceList.test.tsx
```

---

## 11. Actionable TODO List (Wave-Grouped)

### Wave 1: Database + Repository
```bash
# T1.1: Add AiResource model
# File: server/database/models.py
# Category: quick, Skills: []
# QA: python -c "from database.models import AiResource; print('OK')"

# T1.2: Generate Alembic migration
# Command: cd server && alembic revision --autogenerate -m "add_ai_resource_table"
# QA: Check alembic/versions/ for new file

# T1.3: Run migration
# Command: cd server && alembic upgrade head
# QA: sqlite3 app.db ".schema ai_resource"

# T2.1-T2.3: Repository layer
# File: server/repositories/ai_resource_repository.py
# Category: quick, Skills: []
# QA: pytest tests/test_ai_resource_repository.py -v
```

### Wave 2: Service + Router (Parallel)
```bash
# T3.1-T3.6: Service layer (agent 1)
# File: server/services/ai_resource_service.py
# Category: deep, Skills: []
# QA: pytest tests/test_ai_resource_service.py -v

# T4.1-T4.3: Router layer (agent 2)
# File: server/routers/ai_resources.py
# Category: quick, Skills: []
# QA: pytest tests/test_ai_resource_api.py -v
```

### Wave 3: Sync Integration
```bash
# T5.1-T5.4: Sync integration
# Files: server/config.py, server/services/message_service.py, server/application*.yml
# Category: deep, Skills: []
# QA: pytest tests/test_ai_resource_sync.py -v
```

### Wave 4: Frontend (Parallel)
```bash
# T6.1-T6.5: Frontend
# Files: web/lib/api/types.ts, web/lib/api/client.ts, web/hooks/useAIResources.ts, web/app/ai-resources/page.tsx
# Category: visual-engineering, Skills: [frontend-ui-ux]
# QA: npm run test -- --grep "useAiResources"
```

---

## 12. Scope Guardrails

**MUST NOT:**
- Add authentication/authorization
- Create bidirectional sync
- Add versioning or history
- Add import/export
- Modify workspace table

**MUST:**
- Graceful degradation on sync failure
- Test all layers
- Follow existing patterns
