# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-12
**Commit:** c659d44
**Branch:** main

## OVERVIEW

Claude SDK Python REPL client. Async chat interface with streaming/verbose mode support. Wraps `claude-agent-sdk` for interactive coding assistant sessions.

## STRUCTURE

```
./
├── main.py           # CLI entry point, REPL loop, message processing
├── claude_client.py  # ClaudeClient wrapper with async context manager
├── tests/            # Pytest unit tests (16 tests)
├── requirements.txt  # Dependencies: claude-agent-sdk, pytest
└── README.md         # Usage documentation
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add CLI argument | `main.py:parse_args()` | Uses argparse, `--cwd` required |
| Process messages | `main.py:process_message()` | Handles TextBlock, ToolUseBlock, ThinkingBlock |
| Extend client | `claude_client.py:ClaudeClient` | Async context manager pattern |
| Configuration | `ClaudeClientConfig` dataclass | cwd, settings, system_prompt |
| Tests | `tests/test_main.py`, `tests/test_claude_client.py` | Mock classes for SDK types |

## CONVENTIONS

- **Entry point**: `main.py` - call `main()` via `if __name__ == "__main__"`
- **Client usage**: Always `async with ClaudeClient(config) as client:` - no manual connect/disconnect
- **Settings**: Load from `~/.claude/settings.json` or custom path via `--settings`
- **Message flow**: `client.query()` → `client.receive_response()` (async iterator)
- **Demo mode**: Fallback when ClaudeClient import fails - echoes input, no API calls

## ANTI-PATTERNS (THIS PROJECT)

- **Never** instantiate `ClaudeSDKClient` directly - use `ClaudeClient` wrapper
- **Never** skip `async with` context manager - will raise RuntimeError
- **Never** hardcode settings path - use `ClaudeClientConfig.settings` parameter

## UNIQUE STYLES

- **Graceful SDK fallback**: Try/except imports with `None` fallbacks for testing without SDK installed
- **Mock classes**: `MockTextBlock`, `MockToolUseBlock` in tests mirror SDK types
- **Dual mode**: `stream=True` prints incrementally, `stream=False` aggregates and returns string
- **Verbose control**: `--quiet` hides tool calls, `--verbose` (default) shows them

## COMMANDS

```bash
# Run REPL
python main.py --cwd .

# Non-streaming mode
python main.py --cwd . --no-stream

# Quiet mode (hide tool calls)
python main.py --cwd . --quiet

# Custom settings
python main.py --cwd . --settings /path/to/settings.json

# Run tests
pytest tests/ -v
```

## NOTES

- Requires `ANTHROPIC_API_KEY` env var or `api_key` in settings.json
- Settings file must exist (raises FileNotFoundError if missing)
- `--cwd` is required - no default working directory
- REPL commands: `exit`, `quit`, Ctrl+D to exit; Ctrl+C to interrupt
