# Issues Found During Code Quality Review (F2)

## 2026-03-13: Backend Test Failures

### Critical: Missing Required Field in Test Fixtures

**Location:** `server/tests/test_message_repository.py` and related test files
**Issue:** Test fixtures don't provide `external_session_id` which is required (NOT NULL) in `Session` model.

**Root Cause:**
- `server/database/models.py:68` defines `external_session_id = Column(Text, nullable=False)`
- Test fixture at `server/tests/test_message_repository.py:40-48` creates Session without `external_session_id`

**Affected Tests (21 ERROR, 4 FAILED):**

ERROR tests:
- test_message_repository.py (13 tests)
- test_message_service.py (14 tests) 
- test_messages_router.py (3 tests)
- test_workspace_repository.py (11 tests)
- test_sse_service.py (2 tests)

FAILED tests:
- test_project_repository.py::TestProjectRepositoryDelete::test_delete_cascades_to_sessions
- test_project_repository.py::TestProjectRepositoryDelete::test_delete_cascades_to_messages
- test_project_service.py::TestProjectServiceDelete::test_delete_cascades_to_sessions
- test_project_service.py::TestProjectServiceDelete::test_delete_cascades_to_messages
- test_workspace_service.py::TestWorkspaceServiceDelete::test_delete_workspace_cascades_sessions

**Fix Required:**
Update test fixtures to include `external_session_id` when creating Session objects:
```python
session = Session(
    session_unique_id="sess_001",
    external_session_id="ext_sess_001",  # ADD THIS
    project_unique_id="proj_001",
    ...
)
```

---

## Minor: Console Statements in Frontend

**Location:** Frontend components
**Severity:** Low (acceptable for error handling)

Files with console statements:
- `web/components/InputArea.tsx` - 2x console.error (error handling)
- `web/components/Sidebar.tsx` - 2x console.error, 1x console.log (debug)
- `web/components/layout/TopBar.tsx` - 1x console.error (error handling)

**Recommendation:** Consider replacing console.log with proper logging or removing debug statements.

---

## Code Quality Summary

### PASSING:
- Frontend build: ✅ Compiled successfully (Next.js 16.1.6)
- LSP diagnostics: ✅ No errors in frontend components
- Anti-patterns: ✅ No `as any`, `@ts-ignore`, `eslint-disable`
- AI slop: ✅ No excessive comments, good code organization
- TODO/FIXME: ✅ None found

### FAILING:
- Backend tests: ❌ 277 passed, 4 failed, 21 errors (test fixtures broken)
