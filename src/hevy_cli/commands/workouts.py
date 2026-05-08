"""Workout commands."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import click

from ..cli import get_client
from ..models import WorkoutInput
from ..options import format_option
from ..output import detect_format, output

WORKOUT_COLUMNS = [
    ("ID", "id"),
    ("Title", "title"),
    ("Start", "start_time"),
    ("End", "end_time"),
    ("Exercises", "_exercise_count"),
]


def _enrich_workout(w: dict[str, Any]) -> dict[str, Any]:
    """Add computed fields for display."""
    w["_exercise_count"] = len(w.get("exercises", []))
    return w


def _parse_date(ctx: click.Context, param: click.Parameter, value: str | None) -> str | None:
    """Parse a date string in YYYY-MM-DD format, returning ISO string, or raise BadParameter if invalid."""

    if value is None:
        return None
    try:
        # Accept YYYY-MM-DD format, add more formats as needed
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise click.BadParameter(
            f"Date '{value}' is not valid. Please use YYYY-MM-DD format."
        ) from exc


def _within_range(w: dict[str, Any], since: str | None, until: str | None) -> bool:
    """Return True if workout w's start_time date is within [since, until] (inclusive), or since/until are None."""
    # Get date portion from ISO string "YYYY-MM-DDTHH:MM:SSZ"
    workout_date = w.get("start_time", "")[:10]

    return not (
        (since is not None and workout_date < since) or (until is not None and workout_date > until)
    )


@click.group()
def workouts() -> None:
    """Manage workouts."""


@workouts.command("list")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--page-size", default=5, type=int, help="Items per page (max 10)")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@click.option("--since", callback=_parse_date, help="Show workouts since this date (YYYY-MM-DD)")
@click.option("--until", callback=_parse_date, help="Show workouts until this date (YYYY-MM-DD)")
@format_option
@click.pass_context
def list_workouts(
    ctx: click.Context,
    page: int,
    page_size: int,
    fetch_all: bool,
    since: str | None,
    until: str | None,
) -> None:
    """List workouts."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))

    if fetch_all:
        items = [
            _enrich_workout(w)
            for w in client.iter_all_workouts(page_size=page_size)
            if _within_range(w, since, until)
        ]
        output(items, fmt=fmt, columns=WORKOUT_COLUMNS, title="All Workouts")
    else:
        result = client.list_workouts(page=page, page_size=page_size)
        items = []
        for w in result.workouts:
            d = w.model_dump()
            if _within_range(d, since, until):
                items.append(_enrich_workout(d))
        output(
            items,
            fmt=fmt,
            columns=WORKOUT_COLUMNS,
            title=f"Workouts (page {result.page}/{result.page_count})",
        )


@workouts.command("get")
@click.argument("workout_id")
@format_option
@click.pass_context
def get_workout(ctx: click.Context, workout_id: str) -> None:
    """Get a workout by ID."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    result = client.get_workout(workout_id)
    output(result, fmt=fmt, columns=WORKOUT_COLUMNS, title="Workout")


@workouts.command("create")
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="JSON file with workout data",
)
@format_option
@click.pass_context
def create_workout(ctx: click.Context, file_path: str) -> None:
    """Create a workout from a JSON file."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    data = client.load_json_file(file_path)
    workout_data = data.get("workout", data)
    workout = WorkoutInput.model_validate(workout_data)
    result = client.create_workout(workout)
    output(result, fmt=fmt, columns=WORKOUT_COLUMNS, title="Created Workout")
    click.echo("✅ Workout created", err=True)


@workouts.command("update")
@click.argument("workout_id")
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="JSON file with workout data",
)
@format_option
@click.pass_context
def update_workout(ctx: click.Context, workout_id: str, file_path: str) -> None:
    """Update an existing workout."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    data = client.load_json_file(file_path)
    workout_data = data.get("workout", data)
    workout = WorkoutInput.model_validate(workout_data)
    result = client.update_workout(workout_id, workout)
    output(result, fmt=fmt, columns=WORKOUT_COLUMNS, title="Updated Workout")
    click.echo("✅ Workout updated", err=True)


@workouts.command("count")
@format_option
@click.pass_context
def count_workouts(ctx: click.Context) -> None:
    """Get total workout count."""
    client = get_client(ctx)
    count = client.count_workouts()
    fmt = detect_format(ctx.obj.get("output_format"))
    if fmt == "table":
        click.echo(f"Total workouts: {count}")
    else:
        output({"workout_count": count}, fmt=fmt)


@workouts.command("events")
@click.option("--since", help="ISO 8601 date to fetch events since")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--page-size", default=5, type=int, help="Items per page (max 10)")
@format_option
@click.pass_context
def list_events(ctx: click.Context, since: str | None, page: int, page_size: int) -> None:
    """List workout events (updates/deletes) since a date."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    result = client.list_workout_events(since=since, page=page, page_size=page_size)
    output(result, fmt=fmt)
