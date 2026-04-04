"""Exercise template commands."""

from __future__ import annotations

import click

from ..cli import get_client
from ..models import CustomExerciseInput
from ..output import detect_format, output

EXERCISE_COLUMNS = [
    ("ID", "id"),
    ("Title", "title"),
    ("Type", "type"),
    ("Primary Muscle", "primary_muscle_group"),
    ("Custom", "is_custom"),
]

HISTORY_COLUMNS = [
    ("Workout", "workout_title"),
    ("Date", "workout_start_time"),
    ("Weight (kg)", "weight_kg"),
    ("Reps", "reps"),
    ("RPE", "rpe"),
    ("Set Type", "set_type"),
]


@click.group()
def exercises() -> None:
    """Manage exercise templates."""


@exercises.command("list")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--page-size", default=5, type=int, help="Items per page (max 100)")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@click.pass_context
def list_exercises(ctx: click.Context, page: int, page_size: int, fetch_all: bool) -> None:
    """List exercise templates."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))

    if fetch_all:
        items = list(client.iter_all_exercises(page_size=min(page_size, 100)))
        output(items, fmt=fmt, columns=EXERCISE_COLUMNS, title="All Exercise Templates")
    else:
        result = client.list_exercises(page=page, page_size=min(page_size, 100))
        items = [e.model_dump() for e in result.exercise_templates]
        output(items, fmt=fmt, columns=EXERCISE_COLUMNS, title=f"Exercises (page {result.page}/{result.page_count})")


@exercises.command("get")
@click.argument("exercise_id")
@click.pass_context
def get_exercise(ctx: click.Context, exercise_id: str) -> None:
    """Get an exercise template by ID."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    result = client.get_exercise(exercise_id)
    output(result, fmt=fmt, columns=EXERCISE_COLUMNS, title="Exercise Template")


@exercises.command("create")
@click.option("--file", "-f", "file_path", required=True, type=click.Path(exists=True), help="JSON file with exercise data")
@click.pass_context
def create_exercise(ctx: click.Context, file_path: str) -> None:
    """Create a custom exercise template from a JSON file."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    data = client.load_json_file(file_path)
    exercise_data = data.get("exercise", data)
    exercise = CustomExerciseInput.model_validate(exercise_data)
    result = client.create_exercise(exercise)
    output(result, fmt=fmt)
    click.echo("✅ Custom exercise created", err=True)


@exercises.command("history")
@click.argument("exercise_id")
@click.option("--start", "start_date", help="Start date (ISO 8601, e.g. 2024-01-01T00:00:00Z)")
@click.option("--end", "end_date", help="End date (ISO 8601, e.g. 2024-12-31T23:59:59Z)")
@click.pass_context
def exercise_history(ctx: click.Context, exercise_id: str, start_date: str | None, end_date: str | None) -> None:
    """Get exercise history for a template."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    results = client.get_exercise_history(exercise_id, start_date=start_date, end_date=end_date)
    items = [r.model_dump() for r in results]
    output(items, fmt=fmt, columns=HISTORY_COLUMNS, title=f"Exercise History ({len(items)} sets)")
