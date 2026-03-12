# Claude SDK Python Integration - Work Plan

## TL;DR

> **Quick Summary**: 创建一个交互式Python CLI程序，使用Claude Agent SDK实现多轮AI对话，支持流式/非流式输出和工具调用详细度控制。
> 
> **Deliverables**:
> - `main.py` - 主程序入口
> - `requirements.txt` - 依赖清单
> - `tests/` - pytest单元测试
> - `.env.example` - 环境变量示例
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 → Task 3 → Task 5 → Task 6

---

## Context

### Original Request
用户希望在现有的Python虚拟环境中集成Claude Agent SDK，创建一个交互式AI助手CLI程序。

### Interview Summary
**Key Discussions**:
- 虚拟环境: 使用现有`.venv` (Python 3.13)
- 对话模式: 多轮对话 (ClaudeSDKClient)
- 交互方式: REPL循环（持续对话）
- 权限模式: acceptEdits (自动接受文件操作)
- 流式控制: `--stream` / `--no-stream` 参数，默认流式
- 工具调用详细度: 参数控制，默认显示详细过程
- 测试策略: pytest单元测试

**Research Findings**:
- Claude SDK默认是流式的，非流式需要收集所有消息后再处理
- `ClaudeSDKClient` 支持 `permission_mode="acceptEdits"` 自动接受文件操作
- 需要处理 `AssistantMessage`, `TextBlock`, `ToolUseBlock` 等消息类型
- 需要 `ANTHROPIC_API_KEY` 环境变量

### Self Gap Analysis
**Identified Gaps** (addressed):
- **退出机制**: 用户如何退出REPL循环？ → 使用 `exit`/`quit`/`Ctrl+D` 命令
- **错误处理**: API调用失败如何处理？ → 捕获异常，显示友好错误信息，继续循环
- **环境变量检查**: API key不存在怎么办？ → 启动时检查，缺失则提示并退出
- **消息类型处理**: SDK返回多种消息类型，需要区分处理 → TextBlock显示文本，ToolUseBlock显示工具调用

---

## Work Objectives

### Core Objective
创建一个功能完整的Claude AI交互式CLI程序，支持：
1. 多轮对话（REPL循环）
2. 流式/非流式输出切换
3. 工具调用详细度控制
4. 自动文件操作权限
5. pytest单元测试覆盖

### Concrete Deliverables
- `main.py` - 主程序（参数解析、REPL循环、消息处理）
- `requirements.txt` - claude-agent-sdk, pytest, pytest-asyncio
- `tests/test_main.py` - 单元测试
- `.env.example` - 环境变量示例文件

### Definition of Done
- [ ] `python main.py` 能正常启动REPL循环
- [ ] `python main.py --no-stream` 使用非流式输出
- [ ] `python main.py --quiet` 隐藏工具调用详细过程
- [ ] `pytest tests/` 全部通过
- [ ] AI能在当前目录创建/修改文件

### Must Have
- 使用现有`.venv`虚拟环境
- ClaudeSDKClient多轮对话
- REPL循环交互
- 流式/非流式参数控制
- 工具调用详细度参数控制
- acceptEdits权限模式
- pytest单元测试

### Must NOT Have (Guardrails)
- 不要使用 `query()` 函数（用户选择了ClaudeSDKClient）
- 不要添加Web服务/REST API
- 不要添加复杂UI界面（保持纯命令行）
- 不要持久化会话存储
- 不要使用 `as any` 或 `# type: ignore`

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (需要设置)
- **Automated tests**: YES (pytest)
- **Framework**: pytest + pytest-asyncio
- **Test approach**: Tests-after (先实现功能，后添加测试)

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI/TUI**: Use interactive_bash (tmux) — Run command, send keystrokes, validate output
- **Unit Tests**: Use Bash (pytest) — Run tests, assert pass/fail

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — 环境设置 + 骨架):
├── Task 1: 安装依赖包 [quick]
├── Task 2: 创建项目骨架文件 [quick]
└── Task 3: 实现参数解析模块 [quick]

Wave 2 (After Wave 1 — 核心功能):
├── Task 4: 实现Claude SDK客户端封装 [deep]
├── Task 5: 实现REPL循环主逻辑 [deep]
└── Task 6: 实现消息处理和输出格式化 [unspecified-high]

Wave 3 (After Wave 2 — 测试 + 验证):
├── Task 7: 编写pytest单元测试 [unspecified-high]
└── Task 8: 集成测试和最终验证 [unspecified-high]

Critical Path: Task 1 → Task 3 → Task 4 → Task 5 → Task 7
Parallel Speedup: ~40% faster than sequential
Max Concurrent: 3 (Wave 1)
```

### Dependency Matrix

- **1**: — — 4, 7, 1
- **2**: — — 4, 5, 6, 1
- **3**: — — 5, 1
- **4**: 1, 2 — 5, 6, 2
- **5**: 3, 4 — 7, 8, 2
- **6**: 4 — 7, 1
- **7**: 1, 5, 6 — 8, 1
- **8**: 5, 7 — —

### Agent Dispatch Summary

- **Wave 1**: **3** — T1 → `quick`, T2 → `quick`, T3 → `quick`
- **Wave 2**: **3** — T4 → `deep`, T5 → `deep`, T6 → `unspecified-high`
- **Wave 3**: **2** — T7 → `unspecified-high`, T8 → `unspecified-high`

---

## TODOs

- [x] 1. 安装依赖包

  **What to do**:
  - 激活`.venv`虚拟环境
  - 安装 `claude-agent-sdk` 包
  - 安装 `pytest` 和 `pytest-asyncio` 测试框架
  - 创建 `requirements.txt` 文件记录依赖

  **Must NOT do**:
  - 不要安装额外的Web框架或UI库
  - 不要修改`.venv`外的任何文件

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 简单的pip安装命令，执行快速
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无UI测试需求
    - `git-master`: 无git操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Task 4, Task 7
  - **Blocked By**: None

  **References**:
  **External References**:
  - Claude SDK PyPI: `pip install claude-agent-sdk`
  - pytest: `pip install pytest pytest-asyncio`

  **Acceptance Criteria**:
  - [ ] `requirements.txt` 存在且包含 claude-agent-sdk, pytest, pytest-asyncio
  - [ ] `source .venv/bin/activate && pip list | grep claude-agent-sdk` 返回包信息
  - [ ] `source .venv/bin/activate && pip list | grep pytest` 返回包信息

  **QA Scenarios**:
  ```
  Scenario: 依赖安装成功
    Tool: Bash
    Preconditions: 虚拟环境存在
    Steps:
      1. source .venv/bin/activate
      2. pip list | grep claude-agent-sdk
      3. pip list | grep pytest
    Expected Result: 两个命令都返回对应的包信息
    Failure Indicators: "Package not found" 或空输出
    Evidence: .sisyphus/evidence/task-1-install-success.txt
  ```

  **Evidence to Capture**:
  - [ ] pip list 输出保存到 evidence 文件

  **Commit**: YES (groups with Task 2)
  - Message: `chore: add project dependencies`
  - Files: requirements.txt
  - Pre-commit: None

- [x] 2. 创建项目骨架文件

  **What to do**:
  - 创建 `main.py` 骨架文件（空文件或基本结构）
  - 创建 `.env.example` 文件，包含 `ANTHROPIC_API_KEY=your-key-here`
  - 创建 `tests/` 目录
  - 创建 `tests/__init__.py` 空文件

  **Must NOT do**:
  - 不要在 `.env.example` 中填写真实的API key
  - 不要创建 `.env` 文件（用户自己创建）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 简单的文件创建操作
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3)
  - **Blocks**: Task 4, Task 5, Task 6
  - **Blocked By**: None

  **References**:
  **Pattern References**:
  - 无（新项目）

  **Acceptance Criteria**:
  - [ ] `main.py` 文件存在
  - [ ] `.env.example` 文件存在且包含 `ANTHROPIC_API_KEY=`
  - [ ] `tests/` 目录存在
  - [ ] `tests/__init__.py` 文件存在

  **QA Scenarios**:
  ```
  Scenario: 骨架文件创建成功
    Tool: Bash
    Preconditions: 无
    Steps:
      1. ls -la main.py .env.example tests/__init__.py
    Expected Result: 所有文件都存在，无报错
    Failure Indicators: "No such file or directory"
    Evidence: .sisyphus/evidence/task-2-skeleton-created.txt
  ```

  **Commit**: YES (groups with Task 1)
  - Message: `chore: add project dependencies`
  - Files: main.py, .env.example, tests/__init__.py
  - Pre-commit: None

- [x] 3. 实现参数解析模块

  **What to do**:
  - 在 `main.py` 中实现 `parse_args()` 函数
  - 使用 `argparse` 解析命令行参数
  - 支持参数：
    - `--stream` / `--no-stream`: 流式/非流式输出（默认流式）
    - `--quiet` / `--verbose`: 隐藏/显示工具调用详细过程（默认显示）
  - 返回 `argparse.Namespace` 对象

  **Must NOT do**:
  - 不要添加其他不必要的参数
  - 不要在参数解析中执行任何AI操作

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 标准的argparse实现，逻辑简单
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2)
  - **Blocks**: Task 5
  - **Blocked By**: None

  **References**:
  **External References**:
  - Python argparse docs: https://docs.python.org/3/library/argparse.html

  **Acceptance Criteria**:
  - [ ] `python main.py --help` 显示帮助信息
  - [ ] `python main.py --no-stream` 设置 stream=False
  - [ ] `python main.py --quiet` 设置 verbose=False
  - [ ] `python main.py` 默认 stream=True, verbose=True

  **QA Scenarios**:
  ```
  Scenario: 参数解析 - 默认值
    Tool: Bash
    Preconditions: main.py 包含 parse_args()
    Steps:
      1. python -c "from main import parse_args; args = parse_args([]); print(f'stream={args.stream}, verbose={args.verbose}')"
    Expected Result: 输出 "stream=True, verbose=True"
    Failure Indicators: AttributeError 或错误的值
    Evidence: .sisyphus/evidence/task-3-args-default.txt

  Scenario: 参数解析 - 自定义值
    Tool: Bash
    Preconditions: main.py 包含 parse_args()
    Steps:
      1. python -c "from main import parse_args; args = parse_args(['--no-stream', '--quiet']); print(f'stream={args.stream}, verbose={args.verbose}')"
    Expected Result: 输出 "stream=False, verbose=False"
    Failure Indicators: 错误的值
    Evidence: .sisyphus/evidence/task-3-args-custom.txt
  ```

  **Evidence to Capture**:
  - [ ] 参数解析输出

  **Commit**: NO (等待Wave 1完成)
  - Message: N/A
  - Files: N/A
  - Pre-commit: N/A

---

- [x] 4. 实现Claude SDK客户端封装

  **What to do**:
  - 创建 `ClaudeClient` 类封装 `ClaudeSDKClient`
  - 在 `__init__` 中配置 `ClaudeAgentOptions`：
    - `system_prompt`: 友好的AI助手
    - `cwd`: 当前工作目录
    - `permission_mode`: "acceptEdits"
  - 实现 `async with` 上下文管理器支持
  - 实现 `query()` 方法发送消息
  - 实现 `receive_response()` 方法获取响应流

  **Must NOT do**:
  - 不要使用 `query()` 函数（使用 ClaudeSDKClient）
  - 不要硬编码 API key

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 需要理解Claude SDK的异步模式和上下文管理
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6)
  - **Blocks**: Task 5, Task 6
  - **Blocked By**: Task 1, Task 2

  **References**:
  **API References**:
  - `claude_agent_sdk.ClaudeSDKClient` - 主客户端类
  - `claude_agent_sdk.ClaudeAgentOptions` - 配置选项
  - `claude_agent_sdk.AssistantMessage` - AI响应消息
  - `claude_agent_sdk.TextBlock` - 文本内容块
  - `claude_agent_sdk.ToolUseBlock` - 工具调用块

  **Acceptance Criteria**:
  - [ ] `ClaudeClient` 类存在且可导入
  - [ ] 支持 `async with ClaudeClient() as client:` 语法
  - [ ] `client.query("test")` 不抛出异常（需要有效API key）

  **QA Scenarios**:
  ```
  Scenario: 客户端创建成功
    Tool: Bash
    Preconditions: ANTHROPIC_API_KEY 环境变量已设置
    Steps:
      1. python -c "from main import ClaudeClient; print('ClaudeClient imported successfully')"
    Expected Result: 输出 "ClaudeClient imported successfully"
    Failure Indicators: ImportError 或其他错误
    Evidence: .sisyphus/evidence/task-4-client-import.txt
  ```

  **Commit**: NO (等待Wave 2完成)
  - Message: N/A
  - Files: N/A

- [x] 5. 实现REPL循环主逻辑

  **What to do**:
  - 实现 `repl_loop()` 异步函数
  - 循环读取用户输入（使用 `input()` 或 `asyncio` 等效方法）
  - 支持 `exit`/`quit`/`Ctrl+D` 退出循环
  - 调用 `ClaudeClient.query()` 发送消息
  - 根据参数决定流式或非流式输出
  - 错误处理：捕获异常，显示友好信息，继续循环

  **Must NOT do**:
  - 不要在错误时直接退出程序（应继续循环）
  - 不要忽略 KeyboardInterrupt

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 需要处理异步IO和用户交互的复杂性
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 6)
  - **Blocks**: Task 7, Task 8
  - **Blocked By**: Task 3, Task 4

  **References**:
  **Pattern References**:
  - Python REPL pattern: `while True: line = input("> "); if line in ("exit", "quit"): break`

  **Acceptance Criteria**:
  - [ ] 输入 "exit" 或 "quit" 能退出循环
  - [ ] Ctrl+D (EOFError) 能正常退出
  - [ ] API错误不会导致程序崩溃

  **QA Scenarios**:
  ```
  Scenario: REPL退出 - exit命令
    Tool: interactive_bash (tmux)
    Preconditions: main.py 可运行
    Steps:
      1. python main.py
      2. 等待提示符出现
      3. 输入 "exit"
    Expected Result: 程序正常退出
    Failure Indicators: 程序挂起或报错
    Evidence: .sisyphus/evidence/task-5-repl-exit.txt

  Scenario: REPL退出 - quit命令
    Tool: interactive_bash (tmux)
    Preconditions: main.py 可运行
    Steps:
      1. python main.py
      2. 等待提示符出现
      3. 输入 "quit"
    Expected Result: 程序正常退出
    Failure Indicators: 程序挂起或报错
    Evidence: .sisyphus/evidence/task-5-repl-quit.txt
  ```

  **Commit**: NO (等待Wave 2完成)
  - Message: N/A
  - Files: N/A

- [x] 6. 实现消息处理和输出格式化

  **What to do**:
  - 实现 `process_message()` 函数处理不同消息类型
  - 处理 `TextBlock`: 打印文本内容
  - 处理 `ToolUseBlock`: 根据 verbose 参数决定是否显示
  - 流式模式：实时打印每个消息块
  - 非流式模式：收集所有消息后一次性打印
  - 添加适当的颜色或格式化（可选）

  **Must NOT do**:
  - 不要忽略未知消息类型（应记录或跳过）
  - 不要在非流式模式中丢失消息

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 需要细致的消息类型处理和格式化逻辑
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 5)
  - **Blocks**: Task 7
  - **Blocked By**: Task 2, Task 4

  **References**:
  **API References**:
  - `claude_agent_sdk.AssistantMessage` - 消息基类
  - `claude_agent_sdk.TextBlock` - 文本块，属性 `.text`
  - `claude_agent_sdk.ToolUseBlock` - 工具调用块，属性 `.name`, `.input`

  **Acceptance Criteria**:
  - [ ] 流式模式：文本实时显示
  - [ ] 非流式模式：所有文本收集后显示
  - [ ] `--quiet` 模式：不显示工具调用详情
  - [ ] `--verbose` 模式：显示工具调用详情

  - [x] 8. 集成测试和最终验证
  ```
  Scenario: 流式输出 - 文本实时显示
    Tool: interactive_bash (tmux)
    Preconditions: ANTHROPIC_API_KEY 已设置
    Steps:
      1. python main.py
      2. 输入 "Hello, what is 2+2?"
      3. 观察输出是否逐字/逐块显示
    Expected Result: AI响应逐块显示，不是一次性全部出现
    Failure Indicators: 等待很久后一次性显示所有内容
    Evidence: .sisyphus/evidence/task-6-streaming.txt

  Scenario: 非流式输出 - 收集后显示
    Tool: interactive_bash (tmux)
    Preconditions: ANTHROPIC_API_KEY 已设置
    Steps:
      1. python main.py --no-stream
      2. 输入 "Hello, what is 2+2?"
      3. 观察输出是否一次性显示
    Expected Result: AI响应一次性完整显示
    Failure Indicators: 逐块显示（与预期相反）
    Evidence: .sisyphus/evidence/task-6-non-streaming.txt
  ```

  **Commit**: YES (Wave 2 完成)
  - Message: `feat: implement Claude SDK REPL client`
  - Files: main.py
  - Pre-commit: None

---

- [x] 7. 编写pytest单元测试

  **What to do**:
  - 创建 `tests/test_main.py`
  - 测试 `parse_args()` 函数：
    - 测试默认参数值
    - 测试 `--no-stream` 参数
    - 测试 `--quiet` 参数
  - 测试 `process_message()` 函数（如果可单独测试）：
    - 测试 TextBlock 处理
    - 测试 ToolUseBlock 处理（verbose/quiet）
  - 使用 `pytest-asyncio` 标记异步测试

  **Must NOT do**:
  - 不要测试需要真实API key的功能（使用mock）
  - 不要在测试中创建真实文件

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 需要编写规范的测试代码
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Task 8)
  - **Blocks**: Task 8
  - **Blocked By**: Task 1, Task 5, Task 6

  **References**:
  **Pattern References**:
  - pytest 文档: https://docs.pytest.org/
  - pytest-asyncio: https://pytest-asyncio.readthedocs.io/

  **Acceptance Criteria**:
  - [ ] `pytest tests/ -v` 返回全部通过
  - [ ] 至少5个测试用例
  - [ ] 覆盖 parse_args 的所有参数组合

  **QA Scenarios**:
  ```
  Scenario: 测试全部通过
    Tool: Bash
    Preconditions: tests/ 目录存在
    Steps:
      1. source .venv/bin/activate
      2. pytest tests/ -v
    Expected Result: 所有测试通过，显示 "X passed"
    Failure Indicators: "X failed" 或 "ERROR"
    Evidence: .sisyphus/evidence/task-7-tests-pass.txt
  ```

  **Commit**: YES (Wave 3 完成)
  - Message: `test: add pytest unit tests`
  - Files: tests/test_main.py
  - Pre-commit: pytest tests/

- [ ] 8. 集成测试和最终验证

  **What to do**:
  - 手动运行完整的集成测试
  - 测试流式模式：`python main.py`
  - 测试非流式模式：`python main.py --no-stream`
  - 测试quiet模式：`python main.py --quiet`
  - 测试AI创建文件功能：让AI写一个简单的脚本
  - 验证所有命令行参数组合

  **Must NOT do**:
  - 不要跳过任何测试场景
  - 不要忽略警告或错误

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 需要全面的验证和测试
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Task 7)
  - **Blocks**: None
  - **Blocked By**: Task 5, Task 7

  **References**:
  None

  **Acceptance Criteria**:
  - [ ] 流式模式正常工作
  - [ ] 非流式模式正常工作
  - [ ] quiet模式隐藏工具调用
  - [ ] AI能创建/修改文件
  - [ ] 所有pytest测试通过

  **QA Scenarios**:
  ```
  Scenario: 完整集成测试 - AI创建文件
    Tool: interactive_bash (tmux)
    Preconditions: ANTHROPIC_API_KEY 已设置
    Steps:
      1. python main.py
      2. 输入 "Create a file named test_hello.py with a hello world function"
      3. 等待AI完成
      4. 输入 "exit"
      5. ls test_hello.py
    Expected Result: test_hello.py 文件存在
    Failure Indicators: 文件不存在
    Evidence: .sisyphus/evidence/task-8-integration-file.txt

  Scenario: 参数组合测试
    Tool: Bash
    Preconditions: 无
    Steps:
      1. python main.py --help
      2. python main.py --no-stream --quiet --help
    Expected Result: 帮助信息正确显示参数
    Failure Indicators: 参数未识别
    Evidence: .sisyphus/evidence/task-8-args-combo.txt
  ```

  **Commit**: YES (Final)
  - Message: `feat: complete Claude SDK integration`
  - Files: 所有修改的文件
  - Pre-commit: pytest tests/

---

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter + `pytest`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports.
  Output: `Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration.
  Output: `Scenarios [N/N pass] | Integration [N/N] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built, nothing beyond spec was built.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | VERDICT`

---

## Commit Strategy

- **Wave 1 Complete**: `feat: setup project dependencies and structure` — requirements.txt, .env.example
- **Wave 2 Complete**: `feat: implement Claude SDK REPL client` — main.py
- **Wave 3 Complete**: `test: add pytest unit tests` — tests/
- **Final**: `feat: complete Claude SDK integration` — all files

---

## Success Criteria

### Verification Commands
```bash
# 1. 激活虚拟环境并安装依赖
source .venv/bin/activate
pip install -r requirements.txt

# 2. 设置环境变量
export ANTHROPIC_API_KEY=your-key-here

# 3. 运行程序（流式模式）
python main.py

# 4. 运行程序（非流式模式）
python main.py --no-stream

# 5. 运行程序（隐藏工具调用）
python main.py --quiet

# 6. 运行测试
pytest tests/ -v
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] REPL循环正常工作
- [ ] 流式/非流式切换正常
- [ ] 工具调用详细度切换正常
- [ ] AI能创建/修改文件
