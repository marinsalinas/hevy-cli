# hevy-cli

> Production-ready CLI for the [Hevy](https://hevy.com) workout tracking API.

[![CI](https://github.com/marinsalinas/hevy-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/marinsalinas/hevy-cli/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hevy-cli)](https://pypi.org/project/hevy-cli/)
[![Python](https://img.shields.io/pypi/pyversions/hevy-cli)](https://pypi.org/project/hevy-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🏋️ Full Hevy API coverage — workouts, routines, folders, exercises, history
- 📊 Multiple output formats — table (rich), JSON, YAML
- 🔄 Auto-pagination — fetch all results with `--all`
- 🔐 Flexible auth — env var, flag, or config file
- ⚡ Fast startup — lazy-loaded command groups
- 🔁 Retry logic — exponential backoff on rate limits and server errors
- 🧪 Well-tested — pytest + respx, 80%+ coverage target

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

## License

MIT — see [LICENSE](LICENSE).
