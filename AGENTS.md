# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-12
**Commit:** c659d44
**Branch:** main

## OVERVIEW

Claude SDK Python integration toolkit. Provides async REPL client wrapping `claude-agent-sdk` with streaming support, configuration management, and comprehensive testing.

## STRUCTURE

```
./
├── server/           # Core Python application (REPL client + SDK wrapper)
├── docs/             # Documentation (Claude SDK settings guide)
└── web/              # Placeholder for future frontend
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Run application | `server/main.py` | CLI entry point, `--cwd` required |
| Extend client | `server/claude_client.py` | ClaudeClient wrapper class |
| Add configuration | `server/requirements.txt` | Dependencies |
| Read docs | `docs/claude-sdk-settings-guide.md` | SDK configuration reference |
| Write tests | `server/tests/` | pytest suite (16 tests) |

## CONVENTIONS

- **Python-first**: Pure Python 3.x project, no Node.js/TypeScript
- **Virtual environment**: Use `server/.venv/` for isolation
- **Entry point**: `server/main.py` - not at project root
- **Async patterns**: All Claude API calls use `async with` context manager
- **Settings**: Load from `~/.claude/settings.json` or custom path via `--settings`

## ANTI-PATTERNS (THIS PROJECT)

- **Never** run from project root - always `cd server/` or use `python server/main.py`
- **Never** instantiate `ClaudeSDKClient` directly - use `ClaudeClient` wrapper
- **Never** skip `--cwd` argument - required for REPL operation
- **Never** commit `.venv/` directory - already in `.gitignore`

## UNIQUE STYLES

- **Nested structure**: Main code in `server/` subdirectory, not at root
- **Demo mode fallback**: Graceful degradation when SDK import fails (echoes input)
- **Mock classes**: Test suite uses mirror classes of SDK types for isolation
- **Dual output modes**: Streaming (incremental) vs non-streaming (aggregated)
- **Verbose control**: `--quiet` hides tool calls, `--verbose` (default) shows them

## COMMANDS

```bash
# Setup
cd server
source .venv/bin/activate
pip install -r requirements.txt

# Run REPL
python main.py --cwd .

# Run with options
python main.py --cwd . --no-stream --quiet
python main.py --cwd . --settings /path/to/settings.json

# Run tests
pytest tests/ -v
```

## NOTES

- Requires `ANTHROPIC_API_KEY` env var or `api_key` in `~/.claude/settings.json`
- `web/` directory is empty placeholder for potential frontend
- No CI/CD configured (no .github/workflows, no Makefile)
- No Python package metadata (no setup.py, pyproject.toml at root)
- See `server/AGENTS.md` for detailed server module documentation
