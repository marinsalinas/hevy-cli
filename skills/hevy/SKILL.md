---
name: hevy
description: Access Hevy workout tracking data through the hevy-cli command-line tool. Use when the user asks about their workouts, routines, exercise templates, training history, personal records, or wants to analyze fitness data from their Hevy account.
---

# Hevy CLI

You have access to a typed Python CLI named `hevy` that wraps the Hevy v1 REST API. Use it for any task involving the user's workouts, routines, folders, or exercise templates.

## Core principle — invoke the CLI, do not write HTTP code

When the user asks about Hevy data, **always run `hevy <subcommand> --format json` via the Bash tool** and parse the JSON. Never write `httpx`, `requests`, or any direct HTTP calls. The CLI already handles authentication, retries, pagination, rate-limit backoff, error mapping, and pydantic validation. Bypassing it loses all of that and wastes tokens reproducing logic.

If `hevy --version` fails (command not found), tell the user to run `pip install hevy-cli` and stop. Do not attempt a workaround.

## Prerequisites

Before invoking any Hevy command, verify the environment is ready:

```bash
hevy --version            # confirms the CLI is installed
hevy config show          # confirms HEVY_API_KEY or config.toml is set (key is masked)
```

If `config show` reports no API key, tell the user to either:
- `export HEVY_API_KEY="..."` (preferred), or
- `hevy config set auth.api_key "..."`

A Hevy Pro subscription is required to obtain an API key (`https://hevy.com/settings?developer`).

## Available commands

All commands accept `--format json` (default for piping) or `--format table|yaml` for human display. Always pass `--format json` when programmatically consuming output.

### Workouts

| Operation | Command | Notes |
|---|---|---|
| List recent workouts | `hevy workouts list --format json` | Paginated, default 5/page; add `--all` to fetch all pages. Filter by date with `--since YYYY-MM-DD` and/or `--until YYYY-MM-DD` (both bounds inclusive) |
| Get one workout | `hevy workouts get <id> --format json` | |
| Total count | `hevy workouts count` | Returns just the integer |
| Sync events | `hevy workouts events --since 2026-01-01T00:00:00Z --format json` | Updates/deletes since timestamp |

### Routines

| Operation | Command |
|---|---|
| List routines | `hevy routines list --format json` (add `--all` for full set) |
| Get one routine | `hevy routines get <id-or-uuid> --format json` |
| Rename a routine | `hevy routines rename <id-or-search> "<new title>"` |
| Enhance with smart defaults | `hevy routines enhance <id> --format json` (adds rest_seconds, RPE) |

### Folders

| Operation | Command |
|---|---|
| List folders | `hevy folders list --format json` |
| Get folder | `hevy folders get <folder-id> --format json` |

### Exercise templates

| Operation | Command |
|---|---|
| List templates | `hevy exercises list --format json` (add `--page-size 100` for max per page) |
| Get template | `hevy exercises get <template-id> --format json` |
| Per-exercise history | `hevy exercises history <template-id> --start 2026-01-01 --end 2026-12-31 --format json` |

## Output handling

Hevy responses are nested. Always extract just what the user asked for; never dump the whole payload.

```bash
# Good — extract titles only
hevy workouts list --all --format json | jq -r '.[].title'

# Bad — dumps everything to context, wastes tokens
hevy workouts list --all --format json
```

For ad-hoc analysis, prefer Python over jq when the logic gets non-trivial:

```python
import json, subprocess
data = json.loads(subprocess.check_output(["hevy", "workouts", "list", "--all", "--format", "json"]))
```

## Error patterns to expect

| Exit code / output | Meaning | What to tell the user |
|---|---|---|
| `AuthenticationError: InvalidApiKey` | API key wrong or missing | Check `HEVY_API_KEY` env var or run `hevy config show` |
| `NotFoundError` | ID does not exist | Confirm the ID; for routines, try search-by-name with `hevy routines rename` |
| `RateLimitError` | Hit the per-minute limit | The CLI auto-retries with backoff; if still failing, suggest a brief pause |
| `Error: No such option: --foo` | You typed a flag wrong | Re-check `hevy <subcommand> --help` before retrying |

The CLI suppresses tracebacks by default. Pass `--debug` to see HTTP requests and full traces, but only when actively diagnosing — debug output is verbose and burns context.

## Worked examples

### Show this week's workouts

Prefer `--since` over jq filtering — it pushes the filter into the CLI and avoids dumping unwanted workouts into context:

```bash
hevy workouts list --since 2026-04-19 --all --format json | jq -r '.[] | "\(.start_time[:10])  \(.title)"'
```

Then summarise titles, dates, and total volume in plain text.

### Find PRs for a specific exercise

1. Look up the exercise template ID:
   ```bash
   hevy exercises list --all --format json | jq -r '.[] | select(.title | test("Bench Press"; "i")) | "\(.id) \(.title)"'
   ```
2. Pull history with weights:
   ```bash
   hevy exercises history <template-id> --format json | jq '[.[] | .sets[]] | max_by(.weight_kg)'
   ```

### Export a routine to a local file

```bash
hevy routines get "Push Day" --format json > push-day.json
```

Routine commands accept either UUID or partial-name search.

### List routines grouped by folder

```bash
hevy routines list --all --format json | jq 'group_by(.folder_id) | map({folder: .[0].folder_id, routines: [.[] | .title]})'
```

## Out of scope

Do not, even when it seems convenient:

- Write `httpx`, `requests`, or `urllib` calls to `api.hevy.com` directly. Use the CLI.
- Hardcode API keys in scripts. Read from `HEVY_API_KEY`.
- Skip `--format json` and try to parse table output. The table format is for humans.
- Use `--debug` in production scripts. It dumps request bodies including headers (sanitised, but still noisy).
- Loop over individual `hevy workouts get <id>` calls when `hevy workouts list --all` returns the same data in one paginated stream.

## Additional reading

For longer worked examples, see:

- `examples/analyze_volume.md` — weekly/monthly volume analysis
- `examples/find_personal_records.md` — PR detection across history
- `examples/export_routine.md` — routine import/export workflows

These are sibling files in the skill directory. Read them with the Read tool when the user's request matches their topic.
