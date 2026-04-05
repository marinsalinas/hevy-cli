"""Routine commands."""

from __future__ import annotations

import re
from typing import Any

import click

from ..cli import get_client
from ..models import RoutineInput, RoutineUpdateInput
from ..output import detect_format, output

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

ROUTINE_COLUMNS = [
    ("ID", "id"),
    ("Title", "title"),
    ("Folder", "folder_id"),
    ("Exercises", "_exercise_count"),
    ("Updated", "updated_at"),
]

ROUTINE_COLUMNS_WITH_FOLDER = [
    ("ID", "id"),
    ("Title", "title"),
    ("Folder", "_folder_name"),
    ("Exercises", "_exercise_count"),
    ("Updated", "updated_at"),
]


def _enrich_routine(r: dict[str, Any]) -> dict[str, Any]:
    r["_exercise_count"] = len(r.get("exercises", []))
    return r


def _resolve_folder_names(routines: list[dict[str, Any]], client: Any) -> list[dict[str, Any]]:
    """Add _folder_name to each routine by resolving folder IDs."""
    folder_ids: set[int] = set()
    for r in routines:
        fid = r.get("folder_id")
        if fid is not None:
            folder_ids.add(int(fid))
    folder_map: dict[int, str] = {}
    for fid_int in folder_ids:
        try:
            folder = client.get_folder(str(fid_int))
            folder_map[fid_int] = folder.title
        except Exception:
            folder_map[fid_int] = str(fid_int)
    for r in routines:
        raw_fid = r.get("folder_id")
        if raw_fid is not None:
            r["_folder_name"] = folder_map.get(int(raw_fid), "—")
        else:
            r["_folder_name"] = "—"
    return routines


@click.group()
def routines() -> None:
    """Manage routines."""


@routines.command("list")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--page-size", default=5, type=int, help="Items per page (max 10)")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@click.option("--folder-id", type=int, default=None, help="Filter by folder ID")
@click.option("--search", type=str, default=None, help="Search routines by name (case-insensitive)")
@click.pass_context
def list_routines(
    ctx: click.Context,
    page: int,
    page_size: int,
    fetch_all: bool,
    folder_id: int | None,
    search: str | None,
) -> None:
    """List routines."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))

    # When filtering by folder or searching, we must fetch all routines
    needs_all = fetch_all or folder_id is not None or search is not None

    if needs_all:
        items = [_enrich_routine(r) for r in client.iter_all_routines(page_size=page_size)]

        if folder_id is not None:
            items = [r for r in items if r.get("folder_id") == folder_id]

        if search is not None:
            search_lower = search.lower()
            items = [r for r in items if search_lower in r.get("title", "").lower()]

        # Resolve folder names for display
        items = _resolve_folder_names(items, client)
        columns = ROUTINE_COLUMNS_WITH_FOLDER

        title_parts = ["Routines"]
        if folder_id is not None:
            folder_name = items[0]["_folder_name"] if items else str(folder_id)
            title_parts.append(f"in folder '{folder_name}'")
        if search is not None:
            title_parts.append(f"matching '{search}'")
        title = " ".join(title_parts) + f" ({len(items)} found)"

        output(items, fmt=fmt, columns=columns, title=title)
    else:
        result = client.list_routines(page=page, page_size=page_size)
        items = [_enrich_routine(r.model_dump()) for r in result.routines]
        output(
            items,
            fmt=fmt,
            columns=ROUTINE_COLUMNS,
            title=f"Routines (page {result.page}/{result.page_count})",
        )


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
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="JSON file with routine data",
)
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
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="JSON file with routine data",
)
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


@routines.command("rename")
@click.argument("id_or_search")
@click.argument("new_name")
@click.pass_context
def rename_routine(ctx: click.Context, id_or_search: str, new_name: str) -> None:
    """Rename a routine by ID or partial name match.

    ID_OR_SEARCH is either a routine UUID or a partial name to search for.
    NEW_NAME is the new title for the routine.
    """
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))

    if _UUID_RE.match(id_or_search):
        # Direct lookup by ID
        result = client.get_routine(id_or_search)
        routine = result.model_dump()
        routine_id = routine["id"]
        old_title = routine["title"]
    else:
        # Find routine by partial name match
        all_routines = list(client.iter_all_routines(page_size=10))
        name_lower = id_or_search.lower()
        matches = [r for r in all_routines if name_lower in r.get("title", "").lower()]

        if not matches:
            raise click.ClickException(f"No routine found matching '{id_or_search}'")

        if len(matches) > 1:
            titles = "\n".join(f"  - {r['title']} (ID: {r['id']})" for r in matches)
            raise click.ClickException(
                f"Multiple routines match '{id_or_search}':\n{titles}\nPlease be more specific."
            )

        routine = matches[0]
        routine_id = routine["id"]
        old_title = routine["title"]

    # Build update payload preserving existing data
    update_data = RoutineUpdateInput(
        title=new_name,
        notes=routine.get("notes"),
        exercises=[],
    )
    # Preserve exercises from the existing routine
    existing_exercises = routine.get("exercises", [])
    if existing_exercises:
        from ..models import RepRange, RoutineExerciseInput, RoutineSetInput

        exercise_inputs = []
        for ex in existing_exercises:
            set_inputs = []
            for s in ex.get("sets", []):
                rep_range = None
                if s.get("rep_range"):
                    rep_range = RepRange(
                        start=s["rep_range"].get("start"),
                        end=s["rep_range"].get("end"),
                    )
                set_inputs.append(
                    RoutineSetInput(
                        type=s.get("type", "normal"),
                        weight_kg=s.get("weight_kg"),
                        reps=s.get("reps"),
                        distance_meters=s.get("distance_meters"),
                        duration_seconds=s.get("duration_seconds"),
                        custom_metric=s.get("custom_metric"),
                        rep_range=rep_range,
                    )
                )
            exercise_inputs.append(
                RoutineExerciseInput(
                    exercise_template_id=ex["exercise_template_id"],
                    superset_id=ex.get("superset_id"),
                    rest_seconds=ex.get("rest_seconds"),
                    notes=ex.get("notes"),
                    sets=set_inputs,
                )
            )
        update_data.exercises = exercise_inputs

    result = client.update_routine(routine_id, update_data)
    output(result, fmt=fmt, columns=ROUTINE_COLUMNS, title="Renamed Routine")
    click.echo(f"✅ Routine renamed: '{old_title}' → '{new_name}'", err=True)
