# Analysing training volume

Recipes for "how much have I lifted lately" questions. All snippets assume `hevy` is installed and authenticated.

## Total weekly volume across all exercises

Volume here means `sum(weight_kg * reps)` over working sets (excluding warmup).

```bash
hevy workouts list --all --format json \
  | jq '
    [.[]
      | select(.start_time >= "2026-04-19T00:00:00Z")
      | .exercises[].sets[]
      | select(.type != "warmup")
      | (.weight_kg // 0) * (.reps // 0)
    ] | add
  '
```

Read out as `<number> kg total weekly volume`.

## Per-muscle-group volume

Hevy attaches a `primary_muscle_group` to each exercise template, but workout payloads only include `exercise_template_id`. You have to join.

```python
import json, subprocess
from collections import defaultdict

workouts = json.loads(subprocess.check_output(["hevy", "workouts", "list", "--all", "--format", "json"]))
templates = json.loads(subprocess.check_output(["hevy", "exercises", "list", "--all", "--page-size", "100", "--format", "json"]))

muscle_by_id = {t["id"]: t.get("primary_muscle_group", "unknown") for t in templates}
volume = defaultdict(float)
for w in workouts:
    if w["start_time"] < "2026-04-19T00:00:00Z":
        continue
    for ex in w["exercises"]:
        muscle = muscle_by_id.get(ex["exercise_template_id"], "unknown")
        for s in ex["sets"]:
            if s.get("type") == "warmup":
                continue
            volume[muscle] += (s.get("weight_kg") or 0) * (s.get("reps") or 0)

for muscle, kg in sorted(volume.items(), key=lambda x: -x[1]):
    print(f"{muscle:20} {kg:>10.0f} kg")
```

## Trend across mesocycles

For week-over-week comparison, group by ISO week:

```python
import json, subprocess, datetime
from collections import defaultdict

workouts = json.loads(subprocess.check_output(["hevy", "workouts", "list", "--all", "--format", "json"]))
weekly = defaultdict(float)
for w in workouts:
    iso = datetime.datetime.fromisoformat(w["start_time"].replace("Z", "+00:00")).isocalendar()
    week_key = f"{iso.year}-W{iso.week:02d}"
    for ex in w["exercises"]:
        for s in ex["sets"]:
            if s.get("type") != "warmup":
                weekly[week_key] += (s.get("weight_kg") or 0) * (s.get("reps") or 0)

for week, kg in sorted(weekly.items()):
    print(f"{week} {kg:>10.0f} kg")
```

## Notes

- Hevy stores weight in kg internally regardless of the user's display unit. If the user thinks in lb, multiply by 2.20462 only at the presentation layer.
- `set.type` values seen in the wild: `normal`, `warmup`, `failure`, `dropset`. Filter accordingly per analysis.
- Workouts marked `is_private: true` still appear in the user's own data — only matters when sharing.
