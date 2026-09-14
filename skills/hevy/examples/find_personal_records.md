# Finding personal records

Recipes for "what's my PR on X" or "show me all my recent PRs" questions.

## PR for a single exercise

PR here means highest single-set `weight_kg * reps` (a rough 1RM proxy) on a working set.

```bash
# Step 1 — find the exercise template ID by partial name
hevy exercises list --all --format json \
  | jq -r '.[] | select(.title | test("Bench Press \\(Barbell\\)"; "i")) | .id'

# Step 2 — pull all-time history
hevy exercises history <template-id> --format json \
  | jq '
    [.[] | .sets[] | select(.type != "warmup")]
    | max_by((.weight_kg // 0) * (.reps // 0))
  '
```

Output is the single best set; format it as `<weight> kg × <reps>` for the user.

## Best e1RM ever (Epley formula)

Epley: `weight × (1 + reps / 30)`. Useful when comparing across rep ranges.

```python
import json, subprocess, sys

template_id = sys.argv[1] if len(sys.argv) > 1 else input("template id: ")
sets_json = subprocess.check_output(
    ["hevy", "exercises", "history", template_id, "--format", "json"]
)
sets = [
    s for entry in json.loads(sets_json) for s in entry.get("sets", []) if s.get("type") != "warmup"
]


def epley(s):
    w, r = s.get("weight_kg") or 0, s.get("reps") or 0
    return w * (1 + r / 30) if r > 0 else 0


best = max(sets, key=epley)
print(f"e1RM = {epley(best):.1f} kg  ({best['weight_kg']} kg × {best['reps']} reps)")
```

## Recent PRs (last 30 days vs all-time)

For each exercise the user trained recently, check if a working set in the last 30 days beat the all-time prior best:

```python
import json, subprocess, datetime, collections

workouts = json.loads(
    subprocess.check_output(["hevy", "workouts", "list", "--all", "--format", "json"])
)
cutoff = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=30)).isoformat()

# Index every set by exercise template, keyed by date
sets_by_ex: dict[str, list[tuple[str, int, float, int]]] = collections.defaultdict(list)
for w in workouts:
    for ex in w["exercises"]:
        for s in ex["sets"]:
            if s.get("type") == "warmup":
                continue
            weight = s.get("weight_kg") or 0
            reps = s.get("reps") or 0
            sets_by_ex[ex["exercise_template_id"]].append(
                (w["start_time"], weight * reps, weight, reps)
            )

prs = []
for ex_id, history in sets_by_ex.items():
    history.sort()  # by date
    recent = [h for h in history if h[0] >= cutoff]
    if not recent:
        continue
    prior_best = max((h[1] for h in history if h[0] < cutoff), default=0)
    new_best = max(recent, key=lambda h: h[1])
    if new_best[1] > prior_best:
        prs.append((ex_id, new_best, prior_best))

# Resolve exercise names
templates = {
    t["id"]: t["title"]
    for t in json.loads(
        subprocess.check_output(
            ["hevy", "exercises", "list", "--all", "--page-size", "100", "--format", "json"]
        )
    )
}

for ex_id, (date, _, w, r), prior in prs:
    print(
        f"PR! {templates.get(ex_id, ex_id)}: {w}kg × {r} on {date[:10]} (prior best volume: {prior})"
    )
```

## Notes

- Hevy doesn't compute or store a "PR" flag — it's derived. Different definitions (max weight, max e1RM, max volume per set) give different answers; ask the user which they want.
- `weight_kg` can be `null` for bodyweight exercises. Treat null as 0 for ranking, but flag bodyweight separately so the user understands what's happening.
- `start_time` is ISO 8601 UTC. Compare lexicographically — works because of fixed format width.
