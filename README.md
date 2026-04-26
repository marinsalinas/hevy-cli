# hevy-cli

> A typed, testable CLI for the [Hevy](https://hevy.com) workout tracking API.

[![CI](https://github.com/marinsalinas/hevy-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/marinsalinas/hevy-cli/actions/workflows/ci.yml)
[![CodeQL](https://github.com/marinsalinas/hevy-cli/actions/workflows/codeql.yml/badge.svg)](https://github.com/marinsalinas/hevy-cli/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/marinsalinas/hevy-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/marinsalinas/hevy-cli)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/marinsalinas/hevy-cli/main.svg)](https://results.pre-commit.ci/latest/github/marinsalinas/hevy-cli/main)
[![PyPI](https://img.shields.io/pypi/v/hevy-cli)](https://pypi.org/project/hevy-cli/)
[![Python](https://img.shields.io/pypi/pyversions/hevy-cli)](https://pypi.org/project/hevy-cli/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Full Hevy API coverage — workouts, routines, folders, exercises, history
- Multiple output formats — table (rich), JSON, YAML (auto-selected by TTY)
- Auto-pagination — fetch all results with `--all`
- Flexible auth — env var, flag, or config file (XDG-compliant)
- Typed end-to-end — pydantic v2 models, mypy `--strict`, pyright-friendly
- Retry logic — exponential backoff on rate limits and server errors (tenacity)
- Structured logging — `structlog` with JSON output in `--debug`
- Tested — pytest + respx against the real API shapes

## Installation

### With uv (recommended)

```bash
uv tool install hevy-cli
```

### With pip

```bash
pip install hevy-cli
```

### From source

```bash
git clone https://github.com/marinsalinas/hevy-cli.git
cd hevy-cli
uv sync
```

## Quick Start

### 1. Get your API key

Go to [hevy.com/settings?developer](https://hevy.com/settings?developer) (requires Hevy Pro).

### 2. Configure

```bash
# Option A: Environment variable
export HEVY_API_KEY="your-api-key"

# Option B: Config file
hevy config set auth.api_key "your-api-key"

# Option C: Per-command flag
hevy --api-key "your-api-key" workouts list
```

### 3. Use

```bash
# List recent workouts
hevy workouts list

# Get a specific workout
hevy workouts get abc123

# List all workouts (auto-paginate)
hevy workouts list --all

# Count total workouts
hevy workouts count

# JSON output for scripting
hevy workouts list --format json | jq '.[] | .title'

# Create a workout from file
hevy workouts create --file workout.json

# List exercise templates
hevy exercises list --page-size 50

# Get exercise history with date range
hevy exercises history D04AC939 --start 2024-01-01 --end 2024-12-31

# List routines
hevy routines list

# List routine folders
hevy folders list

# Create a routine folder
hevy folders create "Push Pull Legs"

# Show current config
hevy config show
```

## Output Formats

```bash
# Rich table (default in terminal)
hevy workouts list

# JSON (default when piped)
hevy workouts list --format json

# YAML
hevy workouts list --format yaml
```

## Configuration

Config is stored at `~/.config/hevy/config.toml` (XDG compliant):

```toml
[auth]
api_key = "your-api-key"

[output]
format = "table"    # json | table | yaml
color = true

[api]
base_url = "https://api.hevy.com"
timeout = 30
max_retries = 3
```

## Development

```bash
# Clone and setup
git clone https://github.com/marinsalinas/hevy-cli.git
cd hevy-cli
uv sync --dev

# Run tests
uv run pytest

# Run linter
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Type checking
uv run mypy src/

# Run CLI in dev mode
uv run hevy --help
```

## API Coverage

| Resource | list | get | create | update | count | events | history |
|----------|------|-----|--------|--------|-------|--------|---------|
| Workouts | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Routines | ✅ | ✅ | ✅ | ✅ | — | — | — |
| Folders | ✅ | ✅ | ✅ | — | — | — | — |
| Exercises | ✅ | ✅ | ✅ | — | — | — | ✅ |

## Use with Claude Code

This package ships a [Claude Code skill](https://docs.claude.com/en/docs/claude-code) so Claude can query your Hevy data directly through `hevy` instead of writing one-off HTTP scripts. Roughly 2–3× fewer tokens per Hevy-related prompt and no auth/pagination/error-handling drift.

```bash
# One-time install (from a clone of this repo)
mkdir -p ~/.claude/skills
cp -r skills/hevy ~/.claude/skills/
```

Then ask Claude things like *"summarise my workouts from this week"* or *"what's my bench press PR?"* — the skill activates automatically based on its description.

See [docs/claude-skill.md](docs/claude-skill.md) for the install guide, customisation, and troubleshooting. An MCP server (cross-platform — Claude Desktop, Cursor, opencode, Continue) is planned for a future release.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the dev setup, commit conventions, and pull-request flow. Start with issues labelled [`good first issue`](https://github.com/marinsalinas/hevy-cli/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

Architecture decisions and rationale are captured in [ARCHITECTURE.md](ARCHITECTURE.md). Security issues should follow the private disclosure path in [SECURITY.md](SECURITY.md) — please do not file them as public issues.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html); pre-1.0 minor releases may include breaking changes.

## License

MIT — see [LICENSE](LICENSE).
