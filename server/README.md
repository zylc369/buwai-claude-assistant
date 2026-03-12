# Claude SDK Python Integration - Usage Guide

## Setup

### Install Dependencies
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Set API Key

You can set the API key in two ways:

**Option 1: Environment Variable**
```bash
export ANTHROPIC_API_KEY=your-key-here
```

**Option 2: Settings File**
```bash
~/.claude/settings.json
```

The SDK will automatically load this file on initialization.

**Supported Settings**:

- `api_key`: Override default API key (optional)
- `model`: Specify Claude model to use (optional)
- `max_tokens`: Set maximum token limit (optional)
- `permission_mode`: Set permission mode (default: acceptEdits)
- `system_prompt`: Override system prompt (optional)
- `base_url`: Custom API base URL (optional)
- `timeout`: Request timeout in seconds (optional)

**Example settings.json**:

```json
{
  "api_key": "your-api-key-here",
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 8192,
  "permission_mode": "acceptEdits",
  "system_prompt": "You are a helpful assistant for coding tasks."
}
```

## Run Application

### Basic Usage (required --cwd)
```bash
python main.py --cwd /path/to/project
```

### With custom settings file
```bash
python main.py --cwd /path/to/project --settings /path/to/settings.json
```

### Start REPL (streaming mode - default)
```bash
python main.py --cwd .
```

### Start REPL (non-streaming mode)
```bash
python main.py --cwd . --no-stream
```

### Start REPL (quiet mode - hide tool calls)
```bash
python main.py --cwd . --quiet
```

### Combined (non-streaming + quiet)
```bash
python main.py --cwd . --no-stream --quiet
```

### CLI Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--cwd` | Yes | - | Working directory for Claude |
| `--settings` | No | `~/.claude/settings.json` | Path to Claude settings.json file |
| `--stream` / `--no-stream` | No | `--stream` | Enable/disable streaming output |
| `--verbose` / `--quiet` | No | `--verbose` | Show/hide tool use details |
## Available Commands

In REPL, you can type:
- `exit` or `quit` - Exit application
- `Ctrl+D` - Exit application (EOF)
- `Ctrl+C` - Interrupt current operation

## Features

1. **Multi-turn conversations**: Context is maintained across messages
2. **Streaming output**: Text appears in real-time (default)
3. **Non-streaming output**: All text collected and displayed at once
4. **Verbose mode**: Shows tool use details (file operations, etc.)
5. **Quiet mode**: Hides tool use details
6. **Settings.json support**: SDK automatically loads Claude config from `~/.claude/settings.json`

## Testing

Run pytest test suite:
```bash
pytest tests/ -v
```

All 16 unit tests should pass.

## Notes

- The application requires a valid `ANTHROPIC_API_KEY` environment variable to function
- You can also provide configuration via `~/.claude/settings.json` file
- Without API key, application will fall back to demo mode (no API calls)
- Demo mode will echo back your input without processing
