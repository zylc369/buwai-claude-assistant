# API接口文档

> **对应目录**: `server/routers/`

---

## 基础信息

| 配置项 | 值 |
|--------|-----|
| 基础URL | `http://127.0.0.1:8000` |
| 内容类型 | `application/json` |
| CORS | 允许 `http://localhost:3000` |

---

## 1. Projects API

**路由文件**: `server/routers/projects.py`

### 1.1 获取项目列表

```
GET /projects/
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| offset | int | 否 | 分页偏移，默认0 |
| limit | int | 否 | 每页数量，默认100 |
| name | string | 否 | 项目名过滤(模糊匹配) |

**响应**: `List[ProjectResponse]`

```json
[
  {
    "id": 1,
    "project_unique_id": "uuid-xxx",
    "worktree": "/path/to/project",
    "branch": "main",
    "name": "My Project",
    "time_initialized": 1710123456,
    "time_created": 1710123456,
    "time_updated": 1710123456
  }
]
```

### 1.2 创建项目

```
POST /projects/
```

**请求体**:
```json
{
  "project_unique_id": "uuid-xxx",
  "worktree": "/path/to/project",
  "name": "My Project",
  "branch": "main"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_unique_id | string | 是 | 项目唯一ID |
| worktree | string | null允许 | 工作树路径 |
| name | string | 否 | 项目名称 |
| branch | string | 否 | Git分支 |

**响应**: `ProjectResponse`

### 1.3 获取单个项目

```
GET /projects/{project_unique_id}
```

**响应**: `ProjectResponse`

### 1.4 更新项目

```
PUT /projects/{project_unique_id}
```

**请求体**:
```json
{
  "name": "New Name",
  "branch": "develop"
}
```

### 1.5 删除项目

```
DELETE /projects/{project_unique_id}
```

**响应**: 204 No Content

---

## 2. Workspaces API

**路由文件**: `server/routers/workspaces.py`

### 2.1 获取工作空间列表

```
GET /workspaces/
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_unique_id | string | 是 | 项目唯一ID |
| offset | int | 否 | 分页偏移 |
| limit | int | 否 | 每页数量 |

**响应**: `List[WorkspaceResponse]`

```json
[
  {
    "id": 1,
    "workspace_unique_id": "uuid-xxx",
    "project_unique_id": "proj-uuid",
    "name": "main",
    "branch": "main",
    "directory": "/path",
    "extra": null
  }
]
```

### 2.2 创建工作空间

```
POST /workspaces/
```

**请求体**:
```json
{
  "workspace_unique_id": "uuid-xxx",
  "project_unique_id": "proj-uuid",
  "name": "main",
  "branch": "main",
  "directory": "/path"
}
```

### 2.3 获取单个工作空间

```
GET /workspaces/{workspace_unique_id}
```

### 2.4 更新工作空间

```
PUT /workspaces/{workspace_unique_id}
```

### 2.5 删除工作空间

```
DELETE /workspaces/{workspace_unique_id}
```

---

## 3. Sessions API

**路由文件**: `server/routers/sessions.py`

### 3.1 获取会话列表

```
GET /sessions/
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_unique_id | string | 是 | 项目唯一ID |
| workspace_unique_id | string | 是 | 工作空间唯一ID |
| external_session_id | string | 否 | 外部会话ID |
| include_archived | bool | 否 | 是否包含已归档 |
| offset | int | 否 | 分页偏移 |
| limit | int | 否 | 每页数量 |

**响应**: `List[SessionResponse]`

```json
[
  {
    "id": 1,
    "session_unique_id": "uuid-xxx",
    "external_session_id": "uuidv7-xxx",
    "sdk_session_id": "sdk-xxx",
    "project_unique_id": "proj-uuid",
    "workspace_unique_id": "ws-uuid",
    "directory": "/path",
    "title": "New Chat",
    "time_created": 1710123456,
    "time_updated": 1710123456,
    "time_compacting": null,
    "time_archived": null
  }
]
```

### 3.2 创建会话

```
POST /sessions/
```

**请求体**:
```json
{
  "session_unique_id": "uuid-xxx",
  "external_session_id": "uuidv7-xxx",
  "project_unique_id": "proj-uuid",
  "workspace_unique_id": "ws-uuid",
  "directory": "/path",
  "title": "New Chat"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_unique_id | string | 是 | 会话唯一ID |
| external_session_id | string | 是 | 外部会话ID(前端生成UUIDv7) |
| project_unique_id | string | 是 | 项目唯一ID |
| workspace_unique_id | string | 是 | 工作空间唯一ID |
| directory | string | 是 | 工作目录 |
| title | string | 是 | 会话标题 |

### 3.3 获取单个会话

```
GET /sessions/{session_unique_id}
```

### 3.4 更新会话

```
PUT /sessions/{session_unique_id}
```

**请求体**:
```json
{
  "title": "Updated Title",
  "directory": "/new/path"
}
```

### 3.5 删除会话

```
DELETE /sessions/{session_unique_id}
```

### 3.6 归档会话

```
POST /sessions/{session_unique_id}/archive
```

### 3.7 取消归档

```
POST /sessions/{session_unique_id}/unarchive
```

---

## 4. Messages API

**路由文件**: `server/routers/messages.py`

### 4.1 获取消息列表

```
GET /messages/
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_unique_id | string | 是 | 会话唯一ID |
| offset | int | 否 | 分页偏移 |
| limit | int | 否 | 每页数量 |
| last_message_id | int | 否 | 增量获取: 只返回id > last_message_id的消息 |

**响应**: `List[MessageResponse]`

```json
[
  {
    "id": 1,
    "message_unique_id": "uuid-xxx",
    "session_unique_id": "session-uuid",
    "time_created": 1710123456,
    "time_updated": 1710123456,
    "data": "{\"role\":\"user\",\"content\":\"Hello\"}"
  }
]
```

### 4.2 发送AI提示词 (流式)

```
POST /messages/send
```

**请求体**:
```json
{
  "prompt": "Hello, Claude!",
  "session_unique_id": "session-uuid",
  "cwd": "/path/to/project",
  "settings": "",
  "system_prompt": "You are a helpful assistant"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 用户提示词 |
| session_unique_id | string | 是 | 会话唯一ID |
| cwd | string | 是 | 工作目录 |
| settings | string | 否 | 设置文件路径 |
| system_prompt | string | 否 | 系统提示词 |

**响应**: Server-Sent Events (SSE)

```
data: {"type":"chunk","content":"Hello"}

data: {"type":"chunk","content":" there"}

data: {"type":"done","session_unique_id":"xxx","sdk_session_id":"sdk-xxx"}

data: {"type":"error","message":"Error message"}
```

**SSE事件类型**:
| type | 说明 | 附加字段 |
|------|------|----------|
| chunk | 流式内容块 | content |
| done | 完成 | session_unique_id, sdk_session_id |
| error | 错误 | message |

### 4.3 获取单个消息

```
GET /messages/{message_unique_id}
```

### 4.4 更新消息

```
PUT /messages/{message_unique_id}
```

### 4.5 删除消息

```
DELETE /messages/{message_unique_id}
```

---

## 5. Events API (SSE)

**路由文件**: `server/routers/events.py`

### 5.1 SSE事件流

```
GET /events/stream
```

**响应**: Server-Sent Events

- 每30秒发送心跳
- 实时推送会话更新事件

---

## Schema定义

**位置**: 各router文件中的Pydantic模型

### ProjectResponse
```python
class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_unique_id: str
    worktree: str
    branch: str | None
    name: str | None
    time_initialized: int | None
    time_created: int
    time_updated: int
```

### SessionResponse
```python
class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_unique_id: str
    external_session_id: str
    sdk_session_id: str | None
    project_unique_id: str
    workspace_unique_id: str
    directory: str
    title: str
    time_created: int
    time_updated: int
    time_compacting: int | None
    time_archived: int | None
```

### MessageResponse
```python
class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    message_unique_id: str
    session_unique_id: str
    time_created: int
    time_updated: int
    data: str  # JSON string
```
