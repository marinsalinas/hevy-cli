# Usage Guide

## Authentication

You need a Hevy Pro account to use the API. Get your key at [hevy.com/settings?developer](https://hevy.com/settings?developer).

Four ways to authenticate:

```bash
# 1. Operating system credential store (recommended)
hevy auth login
hevy auth status

# 2. Environment variable
export HEVY_API_KEY="your-api-key"

# 3. Config file (legacy; stores the key as plaintext)
hevy config set auth.api_key "your-api-key"

# 4. Per-command flag
hevy --api-key "your-api-key" workouts list
```

`hevy auth login` uses macOS Keychain, Windows Credential Locker, or a
Secret Service-compatible keyring on Linux. Remove the stored credential with
`hevy auth logout`.

## Workouts

### List workouts

```bash
hevy workouts list                    # Default: page 1, 5 items
hevy workouts list --page 2           # Page 2
hevy workouts list --page-size 10     # 10 per page (max)
hevy workouts list --all              # All workouts (auto-paginate)
```

### Get a workout

```bash
hevy workouts get abc-123-def
```

### Create a workout

```bash
hevy workouts create --file workout.json
```

Example `workout.json`:
```json
{
  "workout": {
    "title": "Leg Day 🔥",
    "start_time": "2024-08-14T12:00:00Z",
    "end_time": "2024-08-14T13:00:00Z",
    "is_private": false,
    "exercises": [
      {
        "exercise_template_id": "D04AC939",
        "notes": "Felt good",
        "sets": [
          {"type": "warmup", "weight_kg": 60, "reps": 12},
          {"type": "normal", "weight_kg": 100, "reps": 10},
          {"type": "normal", "weight_kg": 100, "reps": 8, "rpe": 9}
        ]
      }
    ]
  }
}
```

### Update a workout

```bash
hevy workouts update abc-123 --file updated-workout.json
```

### Count workouts

```bash
hevy workouts count
```

### Workout events (sync)

```bash
hevy workouts events --since 2024-01-01T00:00:00Z
```

## Routines

### List routines

```bash
hevy routines list
hevy routines list --all
```

### Get a routine

```bash
hevy routines get routine-456
```

### Create a routine

```bash
hevy routines create --file routine.json
```

Example `routine.json`:
```json
{
  "routine": {
    "title": "Push Day",
    "folder_id": null,
    "notes": "Focus on form",
    "exercises": [
      {
        "exercise_template_id": "D04AC939",
        "rest_seconds": 90,
        "notes": "Slow and controlled",
        "sets": [
          {"type": "warmup", "weight_kg": 60, "reps": 12},
          {"type": "normal", "weight_kg": 100, "reps": 10},
          {"type": "normal", "weight_kg": 100, "reps": 10}
        ]
      }
    ]
  }
}
```

### Update a routine

```bash
hevy routines update routine-456 --file updated-routine.json
```

## Routine Folders

```bash
hevy folders list
hevy folders get 42
hevy folders create "Push Pull Legs"
```

## Exercise Templates

### List exercises

```bash
hevy exercises list                    # 5 per page
hevy exercises list --page-size 100    # Max per page
hevy exercises list --all              # All exercises
```

### Get exercise details

```bash
hevy exercises get D04AC939
```

### Create custom exercise

```bash
hevy exercises create --file custom-exercise.json
```

Example `custom-exercise.json`:
```json
{
  "exercise": {
    "title": "Cable Crunch (Kneeling)",
    "exercise_type": "weight_reps",
    "equipment_category": "machine",
    "muscle_group": "abdominals",
    "other_muscles": []
  }
}
```

### Exercise history

```bash
hevy exercises history D04AC939
hevy exercises history D04AC939 --start 2024-01-01T00:00:00Z --end 2024-12-31T23:59:59Z
```

## Configuration

```bash
hevy auth status                       # Show the active credential source
hevy config show                       # Show non-secret configuration
hevy config set output.format yaml     # Set a value
hevy config path                       # Show config file path
```

## Output Formats

```bash
hevy workouts list                     # Table (in terminal)
hevy workouts list --format json       # JSON
hevy workouts list --format yaml       # YAML
hevy workouts list | jq '.[0].title'   # Auto-JSON when piped
```

## Logging

```bash
hevy -v workouts list                  # Verbose (INFO)
hevy --debug workouts list             # Debug (includes HTTP requests)
```

## API Coverage

Mapped against the [Hevy OpenAPI v0.0.1 spec](https://api.hevyapp.com/docs).

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

### Not in the upstream API

The following operations have no corresponding Hevy API endpoint and are therefore not supported:

- Workout delete (no `DELETE /v1/workouts/{id}`)
- Routine delete (no `DELETE /v1/routines/{id}`)
- Routine folder update/delete (no `PUT` / `DELETE /v1/routine_folders/{id}`)
- User profile (no endpoint in spec)
