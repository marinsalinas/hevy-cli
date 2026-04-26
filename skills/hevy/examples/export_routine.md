# Exporting and importing routines

Recipes for "back up my routines", "share this routine", or "duplicate this routine and tweak it" workflows.

## Export one routine to a file

Routines accept either UUID or partial-name search:

```bash
hevy routines get "Push Day" --format json > push-day.json
```

If multiple routines match the search, the CLI prompts. To avoid the prompt, use the UUID (find it via `hevy routines list --format json | jq -r '.[] | "\(.id) \(.title)"'`).

## Export every routine

```bash
mkdir -p routines-backup
hevy routines list --all --format json \
  | jq -c '.[]' \
  | while read -r r; do
      id=$(jq -r '.id' <<<"$r")
      title=$(jq -r '.title' <<<"$r" | tr '/ ' '__')
      hevy routines get "$id" --format json > "routines-backup/${title}.json"
    done
```

Each routine lands in its own file, named after the routine title (with `/` and spaces replaced for filesystem safety).

## Import — create a new routine from a file

```bash
hevy routines create --file push-day.json --format json
```

The file must match the create-input schema (see `examples/routine.json` in the repo for a reference). Common gotchas:

- `folder_id` is optional and may be `null`; the API rejects unknown folder IDs.
- `rest_seconds` should be an integer (seconds), not a string. Older payloads sometimes had this as a string — the CLI fixes it on read in `0.2.0+`.
- Exercises reference `exercise_template_id`, not the human title. Look up IDs via `hevy exercises list`.

## Duplicate-and-tweak workflow

Common pattern: clone an existing routine, change something, re-create:

```python
import json, subprocess, sys

source_id = sys.argv[1]
new_title = sys.argv[2]

routine = json.loads(subprocess.check_output(["hevy", "routines", "get", source_id, "--format", "json"]))

# Strip server-managed fields so we can POST it as a new routine
for f in ("id", "created_at", "updated_at"):
    routine.pop(f, None)
routine["title"] = new_title

# Tweak example: bump rest by 30s on every exercise
for ex in routine.get("exercises", []):
    ex["rest_seconds"] = (ex.get("rest_seconds") or 0) + 30

# Write to a temp file and create
import tempfile
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump({"routine": routine}, f)
    path = f.name

subprocess.run(["hevy", "routines", "create", "--file", path], check=True)
```

Note the `{"routine": ...}` wrapper — `hevy routines create` expects the payload to be wrapped, matching Hevy's API contract.

## Renaming without re-creating

For a simple title change, no file dance needed:

```bash
hevy routines rename "Push Day" "Push Day v2"
```

Accepts a UUID or a partial name match.

## Notes

- Hevy's API has no DELETE endpoint for routines (acknowledged limitation per upstream OpenAPI spec). To "delete" a routine, the user has to do it in the Hevy app.
- Folders are first-class but minimal — you can list and create them, but the API does not currently expose folder rename or delete.
- Exporting a routine to file then re-importing it produces a *new* routine with a new UUID. It does not update in place. For in-place edits use `hevy routines update <id> --file ...`.
