# Architecture — hevy-cli

## Overview

`hevy-cli` is a production-ready Python CLI for the [Hevy](https://hevy.com) workout tracking API. It wraps the official Hevy v1 REST API into an ergonomic command-line interface for power users, automation, and data export.

## Design Decisions

### 1. CLI Framework → **Click**

| Option | Pros | Cons |
|--------|------|------|
| Click | Mature, composable groups, lazy loading, explicit | More boilerplate than Typer |
| Typer | Less boilerplate, type hints | Thin wrapper over Click, adds dependency, less control over help text |

**Decision:** Click. It's the standard for production CLIs (pip, black, Flask). No extra abstraction layer. Lazy-loaded command groups keep startup fast.

### 2. HTTP Client → **httpx (sync)**

| Option | Pros | Cons |
|--------|------|------|
| httpx sync | Modern, timeout defaults, retry-friendly, same API as async | Slightly newer |
| requests | Battle-tested | No HTTP/2, stale maintenance |
| httpx async | Non-blocking | CLI doesn't benefit from async; adds complexity |

**Decision:** httpx in synchronous mode. Modern defaults (timeouts, connection pooling), easy upgrade path to async if needed later. The Hevy API is simple request-response with pagination — async adds no value for a CLI.

### 3. Authentication

```
Priority order:
1. --api-key flag (highest)
2. HEVY_API_KEY environment variable
3. config.toml → api_key field
```

The API key is sent as `api-key` header on every request. Never logged or printed in output.

### 4. Configuration → **XDG + TOML**

- Config dir: `~/.config/hevy/` (XDG_CONFIG_HOME)
- Data dir: `~/.local/share/hevy/` (XDG_DATA_HOME) — for sync cache
- Config file: `config.toml`

```toml
[auth]
api_key = "your-api-key-here"

[output]
format = "table"  # json | table | yaml
color = true

[api]
base_url = "https://api.hevy.com"
timeout = 30
max_retries = 3
```

### 5. Output Formats

| Format | Library | Use case |
|--------|---------|----------|
| JSON | stdlib json | Piping, scripting, jq |
| Table | rich | Human-readable terminal |
| YAML | pyyaml | Config files, readable structured |

Default: `table` for TTY, `json` for pipes (detected via `sys.stdout.isatty()`).

### 6. Pagination Strategy

The Hevy API uses page/pageSize pagination (max 10 per page for most endpoints, max 100 for exercises). The client implements:

- **Auto-pagination:** `--all` flag fetches all pages transparently
- **Manual pagination:** `--page N --page-size M` for explicit control
- **Iterator pattern:** Internal `paginate()` generator yields items across pages

### 7. Error Handling

```
HevyError (base)
├── AuthenticationError    (401/403)
├── NotFoundError          (404)
├── ValidationError        (400)
├── RateLimitError         (429)
└── ServerError            (500+)
```

- HTTP errors → mapped to typed exceptions with status code + API message
- Retry logic: exponential backoff on 429/5xx (max 3 retries via `tenacity`)
- User-facing: clean error messages, no tracebacks unless `--verbose`

### 8. Testing Strategy

| Layer | Tool | What |
|-------|------|------|
| Unit | pytest | Models, config, utils |
| Integration | respx | HTTP client with mocked responses |
| CLI | click.testing.CliRunner | Command invocation |
| Fixtures | JSON files in tests/fixtures/ | Real API response shapes |

**Why respx over VCR.py:** respx is purpose-built for httpx, declarative, no cassette file management. VCR.py's cassette approach is fragile with API changes.

### 9. Logging → **structlog**

- Structured JSON logging for debugging
- Human-readable console output for `--verbose` mode
- Log levels: ERROR (default) → INFO (--verbose) → DEBUG (--debug)

### 10. Project Layout (src layout)

```
hevy-cli/
├── ARCHITECTURE.md
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── hevy_cli/
│       ├── __init__.py          # Version
│       ├── cli.py               # Click entry point + global options
│       ├── client.py            # HevyClient — HTTP wrapper
│       ├── config.py            # Config loading (XDG + TOML)
│       ├── models.py            # Pydantic models (Workout, Routine, etc.)
│       ├── exceptions.py        # Error hierarchy
│       ├── output.py            # Output formatting (JSON/table/YAML)
│       ├── pagination.py        # Auto-pagination iterator
│       └── commands/
│           ├── __init__.py
│           ├── workouts.py      # workouts list/get/create/update
│           ├── routines.py      # routines list/get/create/update
│           ├── folders.py       # folders list/get/create/update/delete
│           ├── exercises.py     # exercises list/get/create + history
│           └── config_cmd.py    # config set/get/show
├── tests/
│   ├── conftest.py
│   ├── fixtures/                # JSON response fixtures
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_models.py
│   └── test_commands/
│       ├── test_workouts.py
│       ├── test_routines.py
│       └── test_exercises.py
├── .github/workflows/
│   ├── ci.yml
│   └── release.yml
├── docs/
│   └── usage.md
└── examples/
    ├── workout.json
    └── routine.json
```

## API Coverage

Based on the Hevy OpenAPI v0.0.1 spec:

| Endpoint | Method | CLI Command | Notes |
|----------|--------|-------------|-------|
| `/v1/workouts` | GET | `workouts list` | Paginated, page/pageSize |
| `/v1/workouts` | POST | `workouts create` | From JSON file |
| `/v1/workouts/{id}` | GET | `workouts get` | By workout ID |
| `/v1/workouts/{id}` | PUT | `workouts update` | From JSON file |
| `/v1/workouts/count` | GET | `workouts count` | Total count |
| `/v1/workouts/events` | GET | `workouts events` | Sync events since date |
| `/v1/routines` | GET | `routines list` | Paginated |
| `/v1/routines` | POST | `routines create` | From JSON file |
| `/v1/routines/{id}` | GET | `routines get` | By routine ID |
| `/v1/routines/{id}` | PUT | `routines update` | From JSON file |
| `/v1/routine_folders` | GET | `folders list` | Paginated |
| `/v1/routine_folders` | POST | `folders create` | By title |
| `/v1/routine_folders/{id}` | GET | `folders get` | By folder ID |
| `/v1/exercise_templates` | GET | `exercises list` | Paginated (max 100/page) |
| `/v1/exercise_templates` | POST | `exercises create` | Custom exercise |
| `/v1/exercise_templates/{id}` | GET | `exercises get` | By template ID |
| `/v1/exercise_history/{id}` | GET | `exercises history` | By template ID + date range |

### Not in API (CLI won't support)
- Workout delete (no DELETE endpoint)
- Routine delete (no DELETE endpoint)
- Routine folder update/delete (no PUT/DELETE endpoints)
- User profile (no endpoint in spec)

## Phased Implementation

### Phase 1 — Foundation
- Project scaffold (pyproject.toml, src layout)
- HevyClient with auth, pagination, retry
- Config management (XDG, TOML)
- Output formatting (JSON, table, YAML)
- Error hierarchy

### Phase 2 — Core Commands
- `workouts` (list, get, create, update, count, events)
- `routines` (list, get, create, update)
- `folders` (list, get, create)
- `exercises` (list, get, create, history)
- `config` (set, get, show)

### Phase 3 — Polish
- `--all` auto-pagination
- Shell completions (bash, zsh, fish)
- `hevy init` — interactive setup wizard
- Progress bars for bulk operations

### Phase 4 — Release
- CI/CD (lint, test, build, publish)
- PyPI packaging
- Documentation
- GitHub release automation
