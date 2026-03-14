# Claude Assistant Server

FastAPI web service with Claude SDK integration for building AI-powered assistant applications.

## Project Structure

```
server/
├── app.py               # FastAPI application entry point
├── main.py              # CLI REPL client
├── claude_client.py     # Claude SDK wrapper
├── pool.py              # Client connection pool
├── database/            # Database models and engine
├── repositories/        # Data access layer
├── services/            # Business logic layer
├── routers/             # API endpoints
├── tests/               # Test suite
└── requirements.txt     # Dependencies
```

## Quick Start

### 1. Create Virtual Environment

```bash
cd server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

**Option A: Environment Variable**
```bash
export ANTHROPIC_API_KEY=your-key-here
```

**Option B: Settings File**

Create `~/.claude/settings.json`:
```json
{
  "api_key": "your-api-key-here",
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 8192
}
```

---

## Development Usage

### Start Web API Server

```bash
# Activate virtual environment first
source .venv/bin/activate

# Start server using application.yml config (recommended)
python run.py

# Or use a specific profile
APP_PROFILE=dev python run.py

# Or override via environment variables
SERVER__PORT=9000 python run.py
```

Alternative (hardcoded, bypasses application.yml):
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Access points:
- **API Root**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

### Start CLI REPL Client

```bash
# Activate virtual environment first
source .venv/bin/activate

# Start REPL with streaming output (default)
python main.py --cwd .

# Non-streaming mode
python main.py --cwd . --no-stream

# Quiet mode (hide tool calls)
python main.py --cwd . --quiet

# Combined options
python main.py --cwd . --no-stream --quiet
```

### Run Tests

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_app.py -v

# Run with coverage (if pytest-cov is installed)
pytest tests/ -v --cov=. --cov-report=html
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

---

## Production Usage

### Option 1: Uvicorn (Single Worker)

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Option 2: Gunicorn + Uvicorn (Multiple Workers)

```bash
# Install gunicorn first
pip install gunicorn

# Run with 4 workers
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Option 3: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t claude-assistant .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your-key claude-assistant
```

### Option 4: Systemd Service

Create `/etc/systemd/system/claude-assistant.service`:
```ini
[Unit]
Description=Claude Assistant API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/server
Environment="ANTHROPIC_API_KEY=your-key"
ExecStart=/path/to/server/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable claude-assistant
sudo systemctl start claude-assistant
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger documentation |
| `/users/` | GET, POST | List/create users |
| `/users/{id}` | GET, PUT, DELETE | User CRUD |
| `/projects/` | GET, POST | List/create projects |
| `/projects/{id}` | GET, PUT, DELETE | Project CRUD |
| `/tasks/` | GET, POST | List/create tasks |
| `/tasks/{id}` | GET, PUT, DELETE | Task CRUD |
| `/sessions/` | GET, POST | Auth sessions |
| `/events/` | GET | SSE event stream |

### Example API Calls

```bash
# Create user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"secret"}'

# List users
curl http://localhost:8000/users/

# Create project
curl -X POST http://localhost:8000/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"My Project","owner_id":1}'

# List projects by owner
curl "http://localhost:8000/projects/?owner_id=1"

# Create task
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Do something","project_id":1}'

# List tasks by project
curl "http://localhost:8000/tasks/?project_id=1"
```

---

## CLI Arguments (main.py)

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--cwd` | Yes | - | Working directory |
| `--settings` | No | `~/.claude/settings.json` | Settings file path |
| `--stream` / `--no-stream` | No | `--stream` | Streaming mode |
| `--verbose` / `--quiet` | No | `--verbose` | Verbosity |

---

## REPL Commands

| Command | Description |
|---------|-------------|
| `exit`, `quit` | Exit application |
| `Ctrl+D` | Exit (EOF) |
| `Ctrl+C` | Interrupt current operation |

---

## Testing

### Run All Tests
```bash
source .venv/bin/activate
pytest tests/ -v
```

### Test Categories
```bash
# Repository tests
pytest tests/test_*_repository.py -v

# Service tests
pytest tests/test_*_service.py -v

# API endpoint tests
pytest tests/test_app.py -v
```

### Expected Output
```
====================== 195 passed, 410 warnings in 1.58s =======================
```

---

## PyCharm Setup

### Run Configuration
1. `Run` → `Edit Configurations...` → `+` → `Python`
2. Configure:
   - **Name**: `FastAPI Server`
   - **Module name**: `uvicorn`
   - **Parameters**: `app:app --reload --host 0.0.0.0 --port 8000`
   - **Working directory**: `/path/to/server`
   - **Python interpreter**: Select `.venv`

### Debug
- Set breakpoints in code
- Click Debug (🐛) button
- Requests will pause at breakpoints

---

## Configuration

### Settings File (~/.claude/settings.json)

| Setting | Type | Description |
|---------|------|-------------|
| `api_key` | string | Anthropic API key |
| `model` | string | Claude model (default: claude-3-5-sonnet-20241022) |
| `max_tokens` | int | Max response tokens |
| `permission_mode` | string | Permission mode (default: acceptEdits) |
| `system_prompt` | string | Custom system prompt |
| `base_url` | string | Custom API URL |
| `timeout` | int | Request timeout (seconds) |

---

## Troubleshooting

### ModuleNotFoundError
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Address Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn app:app --port 8001
```

### Database Errors
```bash
# Recreate database
rm app.db
python create_tables.py
```

---

## License

MIT
