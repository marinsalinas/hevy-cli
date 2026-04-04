"""Routine commands."""

from __future__ import annotations

import click

from ..cli import get_client
from ..models import RoutineInput, RoutineUpdateInput
from ..output import detect_format, output

ROUTINE_COLUMNS = [
    ("ID", "id"),
    ("Title", "title"),
    ("Folder", "folder_id"),
    ("Exercises", "_exercise_count"),
    ("Updated", "updated_at"),
]


def _enrich_routine(r: dict) -> dict:
    r["_exercise_count"] = len(r.get("exercises", []))
    return r


@click.group()
def routines() -> None:
    """Manage routines."""


@routines.command("list")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--page-size", default=5, type=int, help="Items per page (max 10)")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@click.pass_context
def list_routines(ctx: click.Context, page: int, page_size: int, fetch_all: bool) -> None:
    """List routines."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))

    if fetch_all:
        items = [_enrich_routine(r) for r in client.iter_all_routines(page_size=page_size)]
        output(items, fmt=fmt, columns=ROUTINE_COLUMNS, title="All Routines")
    else:
        result = client.list_routines(page=page, page_size=page_size)
        items = [_enrich_routine(r.model_dump()) for r in result.routines]
        output(items, fmt=fmt, columns=ROUTINE_COLUMNS, title=f"Routines (page {result.page}/{result.page_count})")


@routines.command("get")
@click.argument("routine_id")
@click.pass_context
def get_routine(ctx: click.Context, routine_id: str) -> None:
    """Get a routine by ID."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    result = client.get_routine(routine_id)
    output(result, fmt=fmt, columns=ROUTINE_COLUMNS, title="Routine")


@routines.command("create")
@click.option("--file", "-f", "file_path", required=True, type=click.Path(exists=True), help="JSON file with routine data")
@click.pass_context
def create_routine(ctx: click.Context, file_path: str) -> None:
    """Create a routine from a JSON file."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    data = client.load_json_file(file_path)
    routine_data = data.get("routine", data)
    routine = RoutineInput.model_validate(routine_data)
    result = client.create_routine(routine)
    output(result, fmt=fmt, columns=ROUTINE_COLUMNS, title="Created Routine")
    click.echo("✅ Routine created", err=True)


@routines.command("update")
@click.argument("routine_id")
@click.option("--file", "-f", "file_path", required=True, type=click.Path(exists=True), help="JSON file with routine data")
@click.pass_context
def update_routine(ctx: click.Context, routine_id: str, file_path: str) -> None:
    """Update an existing routine."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    data = client.load_json_file(file_path)
    routine_data = data.get("routine", data)
    routine = RoutineUpdateInput.model_validate(routine_data)
    result = client.update_routine(routine_id, routine)
    output(result, fmt=fmt, columns=ROUTINE_COLUMNS, title="Updated Routine")
    click.echo("✅ Routine updated", err=True)
