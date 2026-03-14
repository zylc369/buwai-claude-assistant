# Claude SDK 集成文档

> **对应文件**: `server/claude_client.py`, `server/pool.py`

---

## 1. ClaudeClient 封装

**文件**: `server/claude_client.py`

### 1.1 ClaudeClientConfig

```python
@dataclass
class ClaudeClientConfig:
    cwd: str                          # 工作目录
    settings: str                     # 设置文件路径
    system_prompt: str = "You are a helpful coding assistant"
```

### 1.2 ClaudeClient

**异步上下文管理器模式**:

```python
async with ClaudeClient(config) as client:
    await client.query(prompt, session_id)
    async for response in await client.receive_response():
        process(response)
```

**方法**:

| 方法 | 参数 | 说明 |
|------|------|------|
| `__aenter__` | - | 连接到Claude SDK |
| `__aexit__` | - | 断开连接 |
| `query` | prompt, session_id | 发送提示词 |
| `receive_response` | - | 异步迭代器，返回响应流 |

**验证代码**:
```python
# server/claude_client.py:32-90
class ClaudeClient:
    def __init__(self, config: ClaudeClientConfig) -> None:
        options = ClaudeAgentOptions(
            system_prompt=config.system_prompt,
            cwd=config.cwd,
            permission_mode="acceptEdits",
            settings=config.settings
        )
        self._options = options
    
    async def __aenter__(self) -> "ClaudeClient":
        self._client = ClaudeSDKClient(self._options)
        await self._client.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.disconnect()
```

---

## 2. 连接池管理

**文件**: `server/pool.py`

### 2.1 ClaudeClientPool

**用途**: 管理Claude客户端连接池，支持会话级别的连接复用

| 方法 | 说明 |
|------|------|
| `get_client(session_id, config)` | 获取或创建客户端 |
| `release_client(session_id)` | 释放客户端回池 |
| `cleanup_idle()` | 清理空闲超时的客户端 |
| `pool_size` | 当前池大小 |
| `active_count` | 活跃连接数 |

**配置**:
- 默认空闲超时: 5分钟
- 按session_id管理连接

**验证代码**:
```python
# server/pool.py
class ClaudeClientPool:
    def __init__(self, idle_timeout_seconds: int = 300):
        self._clients: Dict[str, ClaudeClient] = {}
        self._last_used: Dict[str, float] = {}
        self._idle_timeout = idle_timeout_seconds
    
    async def get_client(self, session_id: str, config: ClaudeClientConfig) -> ClaudeClient:
        if session_id in self._clients:
            self._last_used[session_id] = time.time()
            return self._clients[session_id]
        # ... create new client
```

---

## 3. 配置要求

### 3.1 环境变量

```bash
ANTHROPIC_API_KEY=your-api-key
```

### 3.2 设置文件

**路径**: `~/.claude/settings.json`

```json
{
  "api_key": "your-api-key",
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 8192,
  "permission_mode": "acceptEdits",
  "system_prompt": "You are a helpful coding assistant",
  "base_url": "optional-custom-url",
  "timeout": 120
}
```

### 3.3 工作目录验证

**路由层处理** (`server/routers/messages.py`):

```python
def get_valid_cwd(cwd: Optional[str]) -> str:
    if cwd and os.path.isdir(cwd):
        return cwd
    fallback = os.getcwd()
    if os.path.isdir(fallback):
        return fallback
    return "/tmp"
```

**目的**: 确保传入的工作目录存在，否则使用服务器当前目录或/tmp

---

## 4. 流式响应处理

### 4.1 SSE事件格式

**位置**: `server/routers/messages.py`

| 事件类型 | 字段 | 说明 |
|----------|------|------|
| `chunk` | content | 流式内容块 |
| `done` | session_unique_id, sdk_session_id | 完成 |
| `error` | message | 错误信息 |

**示例**:
```
data: {"type":"chunk","content":"Hello"}

data: {"type":"done","session_unique_id":"xxx","sdk_session_id":"sdk-xxx"}

data: {"type":"error","message":"Working directory does not exist"}
```

### 4.2 响应处理流程

1. 用户发送提示词
2. 创建用户消息存入数据库
3. 调用Claude SDK，流式获取响应
4. 每个响应块:
   - yield SSE chunk事件
   - 累积到完整响应
5. 完成后:
   - 创建AI消息存入数据库
   - yield SSE done事件(含sdk_session_id)

---

## 5. 依赖要求

**requirements.txt**:
```
claude-agent-sdk>=0.1.48
```

---

## 6. 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| 工作目录不存在 | 自动fallback到有效目录 |
| API密钥无效 | SSE error事件 |
| 网络超时 | SSE error事件 |
| SDK异常 | SSE error事件 |
