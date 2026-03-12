# Claude SDK Settings 参数完整指南

深入理解 ClaudeAgentOptions 的 settings 参数

## 概述

`settings` 参数是 `ClaudeAgentOptions` 中的关键配置项，用于控制 AI 代理的运行时行为、权限、沙箱环境等。它接受一个字典对象或文件路径字符串，指定代理在执行任务时的各种限制和配置。

### 快速参考

| 项目 | 说明 |
|------|------|
| **参数类型** | `Optional[Union[Dict[str, Any], str]]` |
| **接受值** | JSON 文件路径（字符串）或字典对象 |
| **参数位置** | `ClaudeAgentOptions` 构造函数 |
| **默认值** | `None`（使用 SDK 默认配置） |
| **必填性** | 非必填，但强烈推荐提供 |

---

## 如何传递 Settings

### 2.1 文件路径方式

通过传递 JSON 文件路径来加载设置配置。这种方式适合在生产环境中集中管理配置。

**适用场景：**
- 配置文件需要频繁修改但代码不需要重新部署
- 团队共享统一的配置模板
- 配置内容较长，不适合直接写在代码中

**示例代码：**

```python
from anthropic.agent import ClaudeAgentOptions

# 通过文件路径传递 settings
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings="path/to/settings.json"
)

# 使用配置创建代理
agent = ClaudeAgent(options)
```

**settings.json 文件示例：**

```json
{
  "permissions": {
    "allow": ["tool::read_file", "tool::write_file"]
  },
  "sandbox": {
    "enabled": true,
    "fs_access": "read_write"
  }
}
```

---

### 2.2 JSON 字符串方式

直接在代码中传递 JSON 字符串，适合需要动态生成配置的场景。

**适用场景：**
- 配置需要在运行时根据条件动态生成
- 测试代码需要快速验证不同配置
- 小型配置，直接嵌入代码更方便

**示例代码：**

```python
from anthropic.agent import ClaudeAgentOptions

# 通过 JSON 字符串传递 settings
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings='{"permissions": {"allow": ["tool::read_file"]}}'
)

# 使用配置创建代理
agent = ClaudeAgent(options)
```

**注意：** JSON 字符串中的双引号需要转义，或使用单引号包裹整个字符串。

---

### 2.3 决策流程图

```
┌─────────────────────────────────────┐
│   开始：需要传递 settings 参数？     │
└─────────────┬───────────────────────┘
              │
              ▼
        ┌───────────┐
        │   是     │
        └─────┬─────┘
              │
              ▼
        ┌─────────────────────┐
        │  配置内容需要修改？  │
        └─────┬───────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
   是                  否
    │                   │
    ▼                   ▼
┌──────────┐      ┌────────────┐
│使用文件   │      │使用 JSON   │
│路径方式   │      │字符串方式   │
└──────────┘      └────────────┘
    │                   │
    └─────────┬─────────┘
              │
              ▼
        ┌────────────┐
        │   创建代理  │
        │ClaudeAgent │
        └────────────┘
```

---

## Settings JSON 结构

### 3.1 完整字段参考

下表列出了 `settings` 参数支持的所有字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `permissions` | `Dict` | 否 | 权限配置，定义允许/禁止的工具调用 |
| `hooks` | `Dict` | 否 | 回调钩子函数，在特定事件触发时执行 |
| `sandbox` | `Dict` | 否 | 沙箱环境配置，控制代码执行的安全级别 |
| `mcpServers` | `Dict` | 否 | MCP 服务器配置，扩展工具集 |
| `api_key` | `str` | 否 | API 密钥（通常通过环境变量或单独参数传递） |
| `model` | `str` | 否 | 使用的模型名称 |
| `system_prompt` | `str` | 否 | 系统提示词，覆盖默认的系统指令 |

---

### 3.2 权限配置 (Permissions)

权限控制 AI 代理可以调用哪些工具。通过 `allow` 和 `deny` 列表指定白名单和黑名单。

**配置说明：**

- **`allow`**: 允许的工具列表，如果存在则只允许这些工具
- **`deny`**: 禁止的工具列表，即使白名单包含也不允许调用
- **工具名称格式**: `tool::<tool_name>`

**示例代码：**

```python
from anthropic.agent import ClaudeAgentOptions

# 严格模式：只允许读取文件和写入文件
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings={
        "permissions": {
            "allow": [
                "tool::read_file",
                "tool::write_file",
                "tool::list_directory"
            ]
        }
    }
)

# 限制模式：禁止执行命令和访问网络
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings={
        "permissions": {
            "deny": [
                "tool::execute_command",
                "tool::http_request"
            ]
        }
    }
)

# 组合使用：允许基础工具，禁止危险操作
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings={
        "permissions": {
            "allow": [
                "tool::read_file",
                "tool::write_file",
                "tool::list_directory"
            ],
            "deny": [
                "tool::execute_command",
                "tool::http_request"
            ]
        }
    }
)
```

**使用场景：**
- 限制 AI 在只读模式下工作
- 防止 AI 执行危险的 shell 命令
- 控制网络访问权限

---

### 3.3 Hooks 配置

钩子函数允许在特定事件发生时插入自定义逻辑，用于日志记录、监控或审计。

**钩子类型：**

| 钩子名称 | 触发时机 | 返回值 |
|---------|---------|--------|
| `PostToolUse` | 工具使用后 | None 或覆盖结果 |
| `PostMessage` | 消息发送后 | None |
| `PreToolUse` | 工具使用前 | 是否允许执行 |

**示例代码：**

```python
from anthropic.agent import ClaudeAgentOptions
import json

# PostToolUse 钩子：记录工具使用日志
def log_tool_use_hook(tool_use: Dict[str, Any], result: Any) -> Any:
    """记录工具使用到日志文件"""
    log_entry = {
        "timestamp": str(datetime.now()),
        "tool": tool_use.get("name"),
        "input": tool_use.get("input"),
        "result": str(result)
    }

    # 写入日志文件
    with open("tool_usage.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return result  # 返回原始结果

# 配置钩子
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings={
        "hooks": {
            "PostToolUse": log_tool_use_hook
        }
    }
)
```

**高级钩子示例（监控敏感操作）：**

```python
# 监控并阻止文件写入操作
def sensitive_operation_hook(tool_use: Dict[str, Any]) -> bool:
    """检查是否执行敏感操作"""
    if tool_use.get("name") == "tool::write_file":
        path = tool_use.get("input", {}).get("path")
        if path and "/system/" in path:
            print(f"⚠️ 拒绝写入系统目录: {path}")
            return False
    return True

options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings={
        "hooks": {
            "PreToolUse": sensitive_operation_hook
        }
    }
)
```

---

### 3.4 Sandbox 配置

沙箱控制 AI 代理运行代码或命令时的安全级别。

**配置说明：**

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | `bool` | `true` | 是否启用沙箱 |
| `fs_access` | `str` | `"read_write"` | 文件系统访问级别 |
| `timeout` | `int` | `30000` | 超时时间（毫秒） |
| `max_exec_time` | `int` | `10000` | 最大执行时间（毫秒） |

**fs_access 可选值：**
- `"read_write"`: 读写访问
- `"read_only"`: 只读访问
- `"none"`: 无访问权限

**示例代码：**

```python
from anthropic.agent import ClaudeAgentOptions

# 只读沙箱：允许读取文件，禁止修改
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings={
        "sandbox": {
            "enabled": True,
            "fs_access": "read_only"
        }
    }
)

# 严格沙箱：限制执行时间和文件访问
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings={
        "sandbox": {
            "enabled": True,
            "fs_access": "read_write",
            "timeout": 60000,
            "max_exec_time": 15000
        }
    }
)

# 禁用沙箱：完全开放（仅限受信任环境）
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings={
        "sandbox": {
            "enabled": False
        }
    }
)
```

**使用建议：**
- **开发环境**: 可以设置为 `read_write` 以便调试
- **生产环境**: 建议使用 `read_only` 或严格的超时配置
- **敏感操作**: 必须启用沙箱并限制超时时间

---

## settings 与 setting_sources 的区别

### 关键区别对照表

| 对比项 | `settings` | `setting_sources` |
|--------|-----------|-------------------|
| **用途** | 最终生效的配置集合 | 配置来源的描述性信息 |
| **类型** | `Dict[str, Any]` 或 `str` | `List[Dict[str, Any]]` |
| **接受值** | 文件路径或字典 | 配置源对象列表 |
| **默认值** | `None` | `[]` |
| **合并顺序** | 最后应用 | 按顺序加载 |
| **使用场景** | 直接提供配置值 | 描述配置来源 |
| **优先级** | 高于 setting_sources | 被settings覆盖 |

### 代码对比

**使用 `settings` (直接配置):**

```python
from anthropic.agent import ClaudeAgentOptions

options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings={
        "permissions": {
            "allow": ["tool::read_file"]
        },
        "sandbox": {
            "enabled": True
        }
    }
)
```

**使用 `setting_sources` (来源描述):**

```python
from anthropic.agent import ClaudeAgentOptions

options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    setting_sources=[
        {
            "name": "production_config",
            "type": "file",
            "path": "/etc/anthropic/agent.json"
        },
        {
            "name": "runtime_override",
            "type": "environment",
            "value": "READ_ONLY_MODE=true"
        }
    ]
)
```

### 设置源位置

| 来源 | 位置 | 说明 |
|------|------|------|
| **文件** | `path/to/settings.json` | 本地配置文件 |
| **环境变量** | `.env` 文件或系统环境 | 动态配置 |
| **默认配置** | SDK 内部默认值 | 不指定时的默认行为 |
| **合并源** | SDK 内部逻辑 | settings 会覆盖 setting_sources |

---

## 合并行为

当同时提供 `settings` 和 `setting_sources` 时，SDK 会按照以下顺序合并配置：

1. 加载 `setting_sources` 中的所有配置
2. 合并 `settings` 中的配置（覆盖同名字段）

**合并示例：**

```python
from anthropic.agent import ClaudeAgentOptions

# setting_sources 定义配置来源
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    setting_sources=[
        {
            "name": "base_config",
            "type": "file",
            "path": "config/base.json"
        }
    ],
    # settings 覆盖和补充 base_config
    settings={
        "permissions": {
            "allow": ["tool::execute_command"]  # 覆盖 base_config 中的 allow
        },
        "sandbox": {
            "timeout": 30000  # 覆盖 base_config 中的 timeout
        },
        "model": "claude-3-opus-20240229"  # 新增配置
    }
)
```

**合并优先级（从低到高）：**

```
1. setting_sources 中的配置
2. SDK 默认配置
3. settings 中的配置（最高优先级）
```

**注意事项：**
- `settings` 会完全覆盖 `setting_sources` 中的同名字段
- 建议在 `settings` 中只修改需要变更的配置
- 保持 `setting_sources` 用于描述配置来源，便于追踪

---

## 完整示例

### 示例 6.1: 基础文件路径

最简单的使用方式，通过文件路径加载配置。

```python
# options.py
from anthropic.agent import ClaudeAgentOptions

# 从文件加载配置
options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    settings="path/to/settings.json"
)

# 创建并使用代理
from anthropic import ClaudeAgent
agent = ClaudeAgent(options)

# 执行任务
response = agent.query("读取当前目录下的所有文件")
print(response)
```

**settings.json 内容：**

```json
{
  "permissions": {
    "allow": ["tool::read_file", "tool::list_directory"]
  },
  "sandbox": {
    "enabled": true,
    "fs_access": "read_only"
  }
}
```

---

### 示例 6.2: 动态配置

根据运行时条件动态生成配置。

```python
# dynamic_config.py
import json
from anthropic.agent import ClaudeAgentOptions

def create_agent_config(is_read_only: bool = True, enable_logging: bool = False) -> ClaudeAgentOptions:
    """根据条件动态创建配置"""

    # 基础配置
    base_config = {
        "permissions": {
            "allow": ["tool::read_file", "tool::write_file", "tool::list_directory"]
        },
        "sandbox": {
            "enabled": True,
            "fs_access": "read_write"
        }
    }

    # 根据参数修改配置
    if is_read_only:
        base_config["sandbox"]["fs_access"] = "read_only"

    if enable_logging:
        def log_hook(tool_use, result):
            print(f"🔧 Tool: {tool_use['name']}")
            print(f"📝 Input: {tool_use['input']}")
            return result

        base_config["hooks"] = {
            "PostToolUse": log_hook
        }

    return ClaudeAgentOptions(
        api_key="your-api-key-here",
        settings=base_config
    )

# 使用示例
options_readonly = create_agent_config(is_read_only=True)
agent_readonly = ClaudeAgent(options_readonly)

options_with_logging = create_agent_config(is_read_only=False, enable_logging=True)
agent_logging = ClaudeAgent(options_with_logging)
```

---

### 示例 6.3: 结合 setting_sources

使用 `setting_sources` 描述配置来源，方便追踪和管理。

```python
# multi_source_config.py
from anthropic.agent import ClaudeAgentOptions

# 定义配置源
config_sources = [
    {
        "name": "default_production",
        "type": "file",
        "path": "/etc/anthropic/agent/default.json",
        "version": "1.0"
    },
    {
        "name": "environment_specific",
        "type": "environment",
        "variables": ["READ_ONLY_MODE", "MAX_TIMEOUT"],
        "description": "从环境变量加载特定配置"
    }
]

# 设置覆盖
settings_override = {
    "model": "claude-3-opus-20240229",
    "permissions": {
        "allow": ["tool::execute_command"]  # 临时开放命令执行
    }
}

options = ClaudeAgentOptions(
    api_key="your-api-key-here",
    setting_sources=config_sources,
    settings=settings_override
)

agent = ClaudeAgent(options)
```

**环境变量配置 (.env 文件):**

```bash
READ_ONLY_MODE=false
MAX_TIMEOUT=60000
```

---

### 示例 6.4: 开发与生产环境

根据环境使用不同的配置。

```python
# env_config.py
import os
from anthropic.agent import ClaudeAgentOptions

def get_agent_options(env: str = "development") -> ClaudeAgentOptions:
    """根据环境返回相应的配置"""

    if env == "development":
        # 开发环境：宽松配置，详细日志
        return ClaudeAgentOptions(
            api_key=os.getenv("CLAUDE_API_KEY"),
            settings={
                "permissions": {
                    "allow": [
                        "tool::read_file",
                        "tool::write_file",
                        "tool::execute_command",
                        "tool::list_directory",
                        "tool::http_request"
                    ]
                },
                "sandbox": {
                    "enabled": True,
                    "fs_access": "read_write",
                    "timeout": 120000
                },
                "hooks": {
                    "PostToolUse": lambda tool_use, result: print(f"[DEV] Tool: {tool_use['name']}")
                }
            }
        )

    elif env == "production":
        # 生产环境：严格配置，只读访问
        return ClaudeAgentOptions(
            api_key=os.getenv("CLAUDE_API_KEY"),
            settings={
                "permissions": {
                    "allow": ["tool::read_file", "tool::list_directory"]
                },
                "sandbox": {
                    "enabled": True,
                    "fs_access": "read_only",
                    "timeout": 60000
                }
            }
        )

    else:
        # 测试环境：最小配置
        return ClaudeAgentOptions(
            api_key=os.getenv("CLAUDE_API_KEY"),
            settings={
                "permissions": {
                    "allow": ["tool::read_file"]
                }
            }
        )

# 使用示例
agent_dev = ClaudeAgent(get_agent_options("development"))
agent_prod = ClaudeAgent(get_agent_options("production"))
agent_test = ClaudeAgent(get_agent_options("test"))
```

---

## 故障排查

### 常见错误及解决方案

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `FileNotFoundError: [Errno 2] No such file or directory: 'settings.json'` | 配置文件路径不存在 | 检查文件路径是否正确，使用绝对路径或相对路径 |
| `JSONDecodeError: Expecting property name enclosed in double quotes` | JSON 格式错误 | 确保所有键和字符串值使用双引号 |
| `AttributeError: 'NoneType' object has no attribute 'get'` | settings 值为 None | 确保 `settings` 参数不为 None，提供有效的字典或路径 |
| `Permission denied` | 文件访问权限不足 | 检查配置文件的读写权限 |
| `Tool 'tool::execute_command' not allowed` | 权限配置错误 | 检查 `permissions.allow` 列表中是否包含该工具 |

---

### 常见陷阱

❌ **错误示例 1: JSON 字符串中未转义双引号**

```python
# 错误：JSON 字符串中包含双引号
settings = '{"permissions": {"allow": ["tool::read_file"]}}'

# 正确：使用单引号包裹或转义双引号
settings = '{"permissions": {"allow": ["tool::read_file"]}}'  # 单引号
settings = '{"permissions": {"allow": ["tool::read_file"]}}'  # 转义引号
```

---

❌ **错误示例 2: 使用了不存在的字段名**

```python
# 错误：字段名拼写错误
settings = {
    "permission": {  # 应该是 permissions (复数)
        "allow": ["tool::read_file"]
    }
}

# 正确
settings = {
    "permissions": {
        "allow": ["tool::read_file"]
    }
}
```

---

❌ **错误示例 3: 在 setting_sources 中传递了无效的配置对象**

```python
# 错误：setting_sources 应该是配置源描述，不是实际配置
setting_sources = [
    {
        "permissions": {
            "allow": ["tool::read_file"]
        }
    }
]

# 正确：setting_sources 只描述来源，实际配置由 settings 提供
setting_sources = [
    {
        "name": "production_config",
        "type": "file",
        "path": "config/production.json"
    }
]
```

---

✅ **正确示例 1: 完整的权限配置**

```python
settings = {
    "permissions": {
        "allow": ["tool::read_file", "tool::write_file"],
        "deny": ["tool::execute_command", "tool::http_request"]
    },
    "sandbox": {
        "enabled": True,
        "fs_access": "read_only"
    }
}
```

---

✅ **正确示例 2: 带钩子的完整配置**

```python
import logging

def audit_hook(tool_use, result):
    """审计钩子：记录所有工具调用"""
    logging.info(f"Audit: {tool_use['name']} - Input: {tool_use['input']}")

settings = {
    "permissions": {
        "allow": ["tool::read_file", "tool::write_file"]
    },
    "hooks": {
        "PostToolUse": audit_hook
    },
    "sandbox": {
        "enabled": True,
        "fs_access": "read_write",
        "timeout": 60000
    }
}
```

---

✅ **正确示例 3: 环境变量结合配置文件**

```bash
# .env 文件
CLAUDE_API_KEY=sk-ant-xxx
ENVIRONMENT=production
```

```python
import os
from anthropic.agent import ClaudeAgentOptions

settings = {
    "sandbox": {
        "fs_access": "read_only" if os.getenv("ENVIRONMENT") == "production" else "read_write"
    }
}

options = ClaudeAgentOptions(
    api_key=os.getenv("CLAUDE_API_KEY"),
    settings=settings
)
```

---

## API 参考摘要

### ClaudeAgentOptions 类

```python
class ClaudeAgentOptions:
    """
    Claude Agent 选项配置类

    参数:
        api_key: Anthropic API 密钥
        settings: 配置设置（文件路径或字典）
        setting_sources: 配置源列表
        model: 使用的模型名称
        system_prompt: 系统提示词
    """

    def __init__(
        self,
        api_key: str,
        settings: Optional[Union[Dict[str, Any], str]] = None,
        setting_sources: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> None:
        ...
```

### 相关参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `api_key` | `str` | API 密钥，必需 |
| `settings` | `Optional[Union[Dict, str]]` | 配置设置 |
| `setting_sources` | `Optional[List[Dict]]` | 配置源描述 |
| `model` | `Optional[str]` | 模型名称 |
| `system_prompt` | `Optional[str]` | 系统提示词 |

### 相关工具类型

| 工具类型 | 格式 | 示例 |
|---------|------|------|
| **文件工具** | `tool::<action>` | `tool::read_file`, `tool::write_file` |
| **命令工具** | `tool::<action>` | `tool::execute_command` |
| **网络工具** | `tool::<action>` | `tool::http_request` |

---

## 总结

`settings` 参数是控制 Claude Agent 行为的核心配置项。掌握其使用方法可以帮助你：

1. **限制权限**：通过 `permissions` 控制可用的工具
2. **增强安全**：通过 `sandbox` 限制代码执行环境
3. **添加审计**：通过 `hooks` 记录和监控操作
4. **灵活配置**：支持文件路径和 JSON 字符串两种方式
5. **环境适配**：结合 `setting_sources` 管理多环境配置

**最佳实践：**
- 生产环境使用只读沙箱 (`fs_access: "read_only"`)
- 限制超时时间 (`timeout`, `max_exec_time`)
- 使用钩子记录敏感操作
- 根据环境动态调整配置
- 保持配置文件的可读性和可维护性

---

**文档版本**: 1.0
**最后更新**: 2026-03-12
**相关 SDK**: Claude Agent SDK
