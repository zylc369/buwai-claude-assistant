# AI Conversation Workspace System Rewrite

## TL;DR

> **Quick Summary**: 重写前端为类似Claude Code/OpenCode的AI对话工作空间系统。废弃当前CRUD代码，按需求.md实现：Project切换器 + Workspace列表 + Session对话 + SSE实时流式输出。
> 
> **Deliverables**: 
> - 新数据库schema（Project/Workspace/Session/Message）
> - 6类API端点（CRUD + AI对话 + SSE）
> - 4区域前端UI（TopBar/Sidebar/Chat/Input）
> - TDD测试套件
> 
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 5 waves, max 7 concurrent
> **Critical Path**: DB Models → Repositories → Services → Routers → Frontend Integration

---

## Context

### Original Request
用户反馈4个UI问题（项目切换位置、对话框黑屏、workspace列表、task概念），经调研发现当前代码是CRUD项目管理系统，与需求.md要求的AI对话工作空间系统完全不匹配。

### Interview Summary
**Key Discussions**:
- **概念澄清**: User → Project (1:1) → Workspace (1:N) → Session (1:N) → Message
- **功能定义**: 类似Claude Code的对话工作空间，不是任务管理系统
- **技术方案**: 废弃当前代码，按需求.md重写；TDD测试驱动
- **AI集成**: 复用现有`claude_client.py`，通过SSE流式输出
- **状态同步**: SSE和轮询API同时支持，前端可切换

**Research Findings**:
- 当前前端: Next.js 16 + React Query + Tailwind v4 + Zustand
- 当前后端: FastAPI + SQLAlchemy + SQLite + alembic
- AI客户端: `claude_client.py`支持流式输出（`receive_response()`异步迭代器）
- 需求.md: 完整定义了数据模型、API、前端UI（27-138行）

### Metis Review
**Identified Gaps** (addressed):
- ✅ AI集成方式: 使用`claude_client.py`，通过SSE流式输出
- ✅ 用户认证: 移除，单用户模式
- ✅ MessageV2.Info: 从SDK导入或定义mock类型
- ✅ 边缘case: 首次打开无数据、切换session中断流等

---

## Work Objectives

### Core Objective
重写为AI对话工作空间系统，实现：
1. 顶部Project切换器（下拉菜单 + 创建）
2. 侧边栏Workspace列表（显示执行状态）+ Session列表
3. 中间对话消息展示（支持流式）
4. 底部提示词输入（快捷键：Enter发送，Cmd/Shift+Enter换行）

### Concrete Deliverables
- 数据库: 4个新表（project/workspace/session/message）
- 后端: 6类API（Project/Workspace/Session/Message CRUD + AI对话 + SSE流式）
- 前端: 单页应用，4区域布局
- 测试: TDD全覆盖（repository/service/router/component）

### Definition of Done
- [ ] `pytest server/tests/ -v` 全部通过（新模型/服务/API测试）
- [ ] `cd web && npm run build` 成功（无TS错误）
- [ ] 前端能创建project、创建workspace、发送消息、接收AI流式回复
- [ ] SSE实时推送工作，localStorage状态恢复正常

### Must Have
- 按需求.md 27-138行精确实现
- TDD测试驱动（先写测试再实现）
- 复用`claude_client.py`（不重写AI集成）
- SSE流式输出 + 轮询API双模式
- 键盘快捷键支持

### Must NOT Have (Guardrails)
- ❌ 用户认证系统（单用户模式）
- ❌ 任务管理功能（Task模型删除）
- ❌ CRUD项目管理（Project只是容器，不是管理实体）
- ❌ 额外功能（搜索、编辑、设置等未在需求.md中的）
- ❌ 重写`claude_client.py`（只封装，不替换）

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: YES (pytest in server/, Jest/Vitest in web/)
- **Automated tests**: YES (TDD)
- **Framework**: pytest (backend), Jest (frontend)
- **TDD**: RED (failing test) → GREEN (minimal impl) → REFACTOR

### QA Policy
Every task includes agent-executed QA scenarios:
- **Backend**: `pytest tests/test_*.py -v` with specific test file
- **Frontend**: `cd web && npm run build` + component render checks
- **API**: `curl` commands with expected JSON responses
- **SSE**: Stream connection test with event validation

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation - 2 parallel):
├── Task 1: Database models + migration [deep]
└── Task 2: Remove old models/tests [quick]

Wave 2 (Data Layer - 4 parallel):
├── Task 3: Project repository + tests [deep]
├── Task 4: Workspace repository + tests [deep]
├── Task 5: Session repository + tests [deep]
└── Task 6: Message repository + tests [deep]

Wave 3 (Business Logic - 4 parallel):
├── Task 7: Project service + tests [deep]
├── Task 8: Workspace service + tests [deep]
├── Task 9: Session service + tests [deep]
└── Task 10: Message service + tests [deep]

Wave 4 (API Layer - 6 parallel):
├── Task 11: Project router + tests [deep]
├── Task 12: Workspace router + tests [deep]
├── Task 13: Session router + tests [deep]
├── Task 14: Message router + tests [deep]
├── Task 15: SSE service + tests [deep]
└── Task 16: SSE router + tests [deep]

Wave 5 (Frontend - 7 parallel):
├── Task 17: Delete old pages + setup store [quick]
├── Task 18: API client extension [deep]
├── Task 19: TopBar component [visual-engineering]
├── Task 20: Sidebar component [visual-engineering]
├── Task 21: Chat area component [visual-engineering]
├── Task 22: Input area component [visual-engineering]
└── Task 23: SSE client + localStorage [deep]

Wave FINAL (Integration - 4 parallel):
├── Task F1: E2E project creation [deep]
├── Task F2: E2E AI conversation [deep]
├── Task F3: E2E session switching [deep]
└── Task F4: Code quality + compliance [oracle]

Critical Path: T1 → T3-T6 → T7-T10 → T11-T16 → T17-T23 → F1-F4
Parallel Speedup: ~75% faster than sequential
Max Concurrent: 7 (Wave 5)
```

### Dependency Matrix

```
Wave 1:
  1 → 3,4,5,6
  2 → (none)

Wave 2:
  3,4,5,6 → 7,8,9,10

Wave 3:
  7 → 11
  8 → 12
  9 → 13,15
  10 → 14,15

Wave 4:
  11-16 → 17-23

Wave 5:
  17-23 → F1-F4
```

### Agent Dispatch Summary

- **Wave 1**: 2 agents - T1→deep, T2→quick(+git-master)
- **Wave 2**: 4 agents - All deep
- **Wave 3**: 4 agents - All deep
- **Wave 4**: 6 agents - All deep
- **Wave 5**: 7 agents - T17→quick, T18→deep, T19-T22→visual-engineering, T23→deep
- **Wave FINAL**: 4 agents - F1-F3→deep, F4→oracle

---

## TODOs

### Wave 1: Database Foundation

- [ ] 1. **Database Models + Migration**
  
  **What to do**:
  - 创建4个新SQLAlchemy模型：Project, Workspace, Session, Message
  - 字段严格按需求.md 27-104行定义
  - 创建alembic迁移（包含DROP旧表）
  
  **Must NOT do**:
  - 不要修改现有User/Task模型（直接删除）
  - 不要添加需求.md中未定义的字段
  
  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: 数据库建模需要深入理解需求，无特殊skill需求
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: Wave 2 (Tasks 3-6)
  - **Blocked By**: None
  
  **References**:
  - `docs/需求.md:27-104` - 完整表结构定义
  - `server/database/models.py` - 参考现有模型写法
  - `server/database/engine.py` - SQLAlchemy引擎配置
  
  **Acceptance Criteria**:
  - [ ] 4个模型类定义完成（Project, Workspace, Session, Message）
  - [ ] alembic迁移文件创建
  - [ ] `alembic upgrade head` 成功
  - [ ] `sqlite3 app.db .schema` 显示新表结构
  
  **QA Scenarios**:
  ```
  Scenario: Database migration succeeds
    Tool: Bash
    Steps:
      1. cd server && alembic upgrade head
      2. sqlite3 app.db ".tables"
    Expected Result: "message\nproject\nsession\nworkspace" (4 tables)
    Evidence: .sisyphus/evidence/task-01-db-migration.txt
  ```
  
  **Commit**: YES
  - Message: `feat(db): add Project/Workspace/Session/Message models`
  - Files: `server/database/models.py`, `server/alembic/versions/*.py`

- [ ] 2. **Remove Old Models and Tests**
  
  **What to do**:
  - 删除User, Task, auth Session模型
  - 删除所有相关测试文件
  - 清理相关imports和references
  
  **Must NOT do**:
  - 不要保留任何User/Task相关代码
  - 不要删除数据库引擎配置
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  - **Reason**: 清理任务需要git操作，git-master确保安全删除
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: None
  - **Blocked By**: None
  
  **References**:
  - `server/database/models.py` - 定位User/Task模型
  - `server/tests/test_*.py` - 定位相关测试
  
  **Acceptance Criteria**:
  - [ ] User/Task模型已删除
  - [ ] 相关测试文件已删除
  - [ ] `grep -r "class User" server/` 返回空
  - [ ] `grep -r "class Task" server/` 返回空
  
  **QA Scenarios**:
  ```
  Scenario: Old models completely removed
    Tool: Bash
    Steps:
      1. grep -r "class User" server/ --include="*.py"
      2. grep -r "class Task" server/ --include="*.py"
    Expected Result: Both return no output
    Evidence: .sisyphus/evidence/task-02-cleanup.txt
  ```
  
  **Commit**: YES
  - Message: `refactor(db): remove User/Task models and tests`
  - Files: `server/database/models.py`, `server/tests/`

### Wave 2: Repository Layer

- [ ] 3. **Project Repository + Tests**
  
  **What to do**:
  - 实现ProjectRepository类（CRUD + 查询）
  - 支持分页查询、按ID/name搜索
  - 编写TDD测试（先写测试再实现）
  
  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4,5,6)
  - **Blocks**: Task 7 (Project service)
  - **Blocked By**: Task 1 (Database models)
  
  **References**:
  - `docs/需求.md:109-111` - Project API需求
  - `server/repositories/` - 参考现有repository实现
  
  **Acceptance Criteria**:
  - [ ] `pytest tests/test_project_repository.py -v` 全部通过
  - [ ] 支持create/read/update/delete/paginate/search
  
  **QA Scenarios**:
  ```
  Scenario: Project CRUD operations work
    Tool: Bash
    Steps:
      1. pytest server/tests/test_project_repository.py -v
    Expected Result: All tests pass
    Evidence: .sisyphus/evidence/task-03-project-repo.txt
  ```
  
  **Commit**: YES
  - Message: `feat(repo): add Project repository with tests`

- [ ] 4. **Workspace Repository + Tests**
  
  **What to do**: 同Task 3，但针对Workspace模型
  - 支持按project_unique_id过滤
  
  **Category**: `deep`
  **Parallelization**: Wave 2 parallel
  **Blocked By**: Task 1
  **Blocks**: Task 8
  
  **References**: `docs/需求.md:118-120`
  
  **Acceptance Criteria**:
  - [ ] `pytest tests/test_workspace_repository.py -v` 全部通过
  
  **Commit**: `feat(repo): add Workspace repository with tests`

- [ ] 5. **Session Repository + Tests**
  
  **What to do**: 同Task 3，但针对Session模型
  - 支持按project_unique_id和workspace_unique_id过滤
  - 支持过滤已归档session
  
  **Category**: `deep`
  **Parallelization**: Wave 2 parallel
  **Blocked By**: Task 1
  **Blocks**: Task 9
  
  **References**: `docs/需求.md:112-115`
  
  **Acceptance Criteria**:
  - [ ] `pytest tests/test_conversation_session_repository.py -v` 全部通过
  
  **Commit**: `feat(repo): add Session repository with tests`

- [ ] 6. **Message Repository + Tests**
  
  **What to do**: 同Task 3，但针对Message模型
  - 支持按session_unique_id过滤
  - Message.data字段存储JSON
  
  **Category**: `deep`
  **Parallelization**: Wave 2 parallel
  **Blocked By**: Task 1
  **Blocks**: Task 10
  
  **References**: `docs/需求.md:116-117`, `docs/需求.md:79` (MessageV2.Info类型)
  
  **Acceptance Criteria**:
  - [ ] `pytest tests/test_message_repository.py -v` 全部通过
  
  **Commit**: `feat(repo): add Message repository with tests`

### Wave 3: Service Layer

- [ ] 7. **Project Service + Tests**
  - **What**: Project业务逻辑层
  - **Category**: `deep`
  - **Parallel**: Wave 3 (with 8,9,10)
  - **Blocked By**: Task 3
  - **QA**: `pytest tests/test_project_service.py -v`
  - **Commit**: `feat(svc): add Project service with tests`

- [ ] 8. **Workspace Service + Tests**
  - **What**: Workspace业务逻辑层
  - **Category**: `deep`
  - **Parallel**: Wave 3
  - **Blocked By**: Task 4
  - **QA**: `pytest tests/test_workspace_service.py -v`
  - **Commit**: `feat(svc): add Workspace service with tests`

- [ ] 9. **Session Service + Tests**
  - **What**: Session业务逻辑层（包含归档逻辑）
  - **Category**: `deep`
  - **Parallel**: Wave 3
  - **Blocked By**: Task 5
  - **Blocks**: Task 13, Task 15
  - **QA**: `pytest tests/test_conversation_session_service.py -v`
  - **Commit**: `feat(svc): add Session service with tests`

- [ ] 10. **Message Service + Tests**
  - **What**: Message业务逻辑层（集成AI调用）
  - **Category**: `deep`
  - **Parallel**: Wave 3
  - **Blocked By**: Task 6
  - **Blocks**: Task 14, Task 15
  - **References**: `server/claude_client.py` - AI客户端集成
  - **QA**: `pytest tests/test_message_service.py -v`
  - **Commit**: `feat(svc): add Message service with tests`

### Wave 4: API Layer

- [ ] 11. **Project Router + Tests**
  - **What**: Project API端点（GET/POST/PUT/DELETE）
  - **Category**: `deep`
  - **Parallel**: Wave 4 (with 12,13,14,15,16)
  - **Blocked By**: Task 7
  - **QA**: `curl http://localhost:8000/projects/` 返回JSON
  - **Commit**: `feat(api): add Project router endpoints`

- [ ] 12. **Workspace Router + Tests**
  - **What**: Workspace API端点
  - **Category**: `deep`
  - **Parallel**: Wave 4
  - **Blocked By**: Task 8
  - **QA**: `curl http://localhost:8000/workspaces/?project_unique_id=xxx`
  - **Commit**: `feat(api): add Workspace router endpoints`

- [ ] 13. **Session Router + Tests**
  - **What**: Session API端点（包含归档过滤）
  - **Category**: `deep`
  - **Parallel**: Wave 4
  - **Blocked By**: Task 9
  - **QA**: `curl http://localhost:8000/sessions/?workspace_unique_id=xxx`
  - **Commit**: `feat(api): add Session router endpoints`

- [ ] 14. **Message Router + Tests**
  - **What**: Message API端点 + AI发送接口
  - **Category**: `deep`
  - **Parallel**: Wave 4
  - **Blocked By**: Task 10
  - **QA**: `curl -X POST http://localhost:8000/messages/send -d '{...}'`
  - **Commit**: `feat(api): add Message router endpoints`

- [ ] 15. **SSE Service + Tests**
  - **What**: SSE流式服务（封装claude_client.py）
  - **Category**: `deep`
  - **Parallel**: Wave 4
  - **Blocked By**: Task 9, Task 10
  - **References**: `server/claude_client.py:82-90` - receive_response()异步迭代器
  - **QA**: SSE连接能接收AI流式响应
  - **Commit**: `feat(sse): add AI streaming service`

- [ ] 16. **SSE Router + Tests**
  - **What**: SSE endpoint（/events/stream/{session_id}）
  - **Category**: `deep`
  - **Parallel**: Wave 4
  - **Blocked By**: Task 15
  - **QA**: `curl -N http://localhost:8000/events/stream/test-id` 流式输出
  - **Commit**: `feat(sse): add session-specific SSE endpoint`

### Wave 5: Frontend

- [x] 17. **Delete Old Pages + Setup Store**
  - **What**: 删除/users,/tasks,/projects页面；创建Zustand store
  - **Category**: `quick`
  - **Parallel**: Wave 5 (with 18,19,20,21,22,23)
  - **QA**: `ls web/app/` 仅显示page.tsx,layout.tsx；store编译通过
  - **Commit**: `refactor(web): remove old CRUD pages and add stores`

- [x] 18. **API Client Extension**
  - **What**: 扩展web/lib/api/client.ts，添加新API方法
  - **Category**: `deep`
  - **Parallel**: Wave 5
  - **References**: `web/lib/api/client.ts` - 现有API客户端模式
  - **QA**: TypeScript编译通过，types匹配backend schemas
  - **Commit**: `feat(web): add API client methods`

- [ ] 19. **TopBar Component (Project Switcher)**
  - **What**: 顶部栏 + Project下拉切换 + 创建按钮
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]
  - **Parallel**: Wave 5
  - **QA**: 组件渲染，下拉工作，创建按钮可用
  - **Commit**: `feat(ui): add TopBar component`

- [x] 20. **Sidebar Component (Workspace + Session)**
  - **What**: Workspace列表（带执行状态）+ Session列表 + 新建按钮
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]
  - **Parallel**: Wave 5
  - **References**: `docs/需求.md:129` - 侧边栏需求
  - **QA**: Workspace/Session加载正常，新建功能工作
  - **Commit**: `feat(ui): add Sidebar component`

- [ ] 21. **Chat Area Component (Message Display)**
  - **What**: 消息展示区域，支持流式消息
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]
  - **Parallel**: Wave 5
  - **QA**: 消息渲染正常，流式消息增量显示
  - **Commit**: `feat(ui): add Chat area component`

- [ ] 22. **Input Area Component (Prompt Input)**
  - **What**: 输入框 + 发送按钮 + 键盘快捷键
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]
  - **Parallel**: Wave 5
  - **References**: `docs/需求.md:134` - Enter发送，Cmd/Shift+Enter换行
  - **QA**: Enter发送，Cmd+Enter换行，Shift+Enter换行
  - **Commit**: `feat(ui): add Input area component`

- [ ] 23. **SSE Client + localStorage Restoration**
  - **What**: 更新SSE客户端支持session流式 + localStorage状态恢复
  - **Category**: `deep`
  - **Parallel**: Wave 5
  - **References**: `docs/需求.md:135-138` - localStorage恢复逻辑
  - **QA**: SSE连接session URL，刷新页面恢复上次状态
  - **Commit**: `feat(sse): add session streaming and localStorage restoration`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE.

- [ ] F1. **E2E: Project Creation** — `deep`
  Create project via API → verify in database → check frontend displays it
  Output: `API [PASS] | DB [PASS] | UI [PASS] | VERDICT: APPROVE/REJECT`

- [ ] F2. **E2E: AI Conversation** — `deep`
  Send message → SSE stream receives tokens → message stored in DB → UI displays
  Output: `Send [PASS] | Stream [PASS] | Store [PASS] | Display [PASS] | VERDICT`

- [ ] F3. **E2E: Session Switching** — `deep`
  Switch session → previous stream cancelled → new session loads → localStorage updated
  Output: `Cancel [PASS] | Load [PASS] | Storage [PASS] | VERDICT`

- [ ] F4. **Code Quality + Compliance** — `oracle`
  Verify all tests pass, no TypeScript errors, requirements.md compliance check
  Output: `Tests [N/N] | TS [CLEAN] | Compliance [N/N] | VERDICT`

---

## Commit Strategy

- **Commit 1**: `feat(db): add Project/Workspace/Session/Message models`
- **Commit 2**: `feat(db): add alembic migration for new schema`
- **Commit 3**: `refactor(db): remove User/Task models and tests`
- **Commit 4-7**: `feat(repo): add [Entity] repository with tests` (4 commits)
- **Commit 8-11**: `feat(svc): add [Entity] service with tests` (4 commits)
- **Commit 12-17**: `feat(api): add [Entity] router endpoints` (6 commits)
- **Commit 18-24**: `feat(ui): add [Component] component` (7 commits)
- **Commit 25**: `feat(sse): add AI streaming service and endpoint`
- **Commit 26**: `feat(state): add localStorage restoration`
- **Commit 27-29**: `test(e2e): add E2E tests for [scenario]` (3 commits)

---

## Success Criteria

### Verification Commands
```bash
# Backend tests
cd server && pytest tests/ -v
# Expected: X passed, 0 failed

# Frontend build
cd web && npm run build
# Expected: Build succeeds, no TS errors

# API health
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# SSE stream test
curl -N http://localhost:8000/events/stream/test-session
# Expected: data: {"type": "heartbeat", ...}
```

### Final Checklist
- [ ] All "Must Have" present (4 new models, 6 APIs, 4 UI regions, TDD tests)
- [ ] All "Must NOT Have" absent (no User/Task/auth, no extra features)
- [ ] All tests pass (pytest + npm build)
- [ ] AI conversation works end-to-end
- [ ] SSE streaming functional
- [ ] LocalStorage restoration working
