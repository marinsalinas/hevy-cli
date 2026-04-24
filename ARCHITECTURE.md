# Architecture — hevy-cli

## Overview

`hevy-cli` is a Python CLI for the [Hevy](https://hevy.com) workout tracking API. It wraps the official Hevy v1 REST API into an ergonomic command-line interface for power users, automation, and data export.

This document captures the **why** behind the key technical choices. For the **what** (how to use each command, supported endpoints) see [docs/usage.md](docs/usage.md). For the project layout, browse [`src/`](src/) directly — the filesystem is authoritative.

New architectural decisions should be added to the list below as dated sections with a problem statement, options considered, and rationale.

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
| CLI | `click.testing.CliRunner` | Command invocation |

**Why respx over VCR.py:** respx is purpose-built for httpx, declarative, no cassette file management. VCR.py's cassette approach is fragile with API changes.

### 9. Logging → **structlog**

- Structured JSON logging for debugging
- Human-readable console output for `--verbose` mode
- Log levels: ERROR (default) → INFO (--verbose) → DEBUG (--debug)
