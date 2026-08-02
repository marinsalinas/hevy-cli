"""Routine commands."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import click
import structlog

from hevy_cli.options import format_option

from ..cli import get_client
from ..models import RoutineInput, RoutineUpdateInput
from ..output import detect_format, output
from ..utils import (
    calculate_dropset_weight,
    calculate_rest_seconds,
    calculate_warmup_weight,
    enhance_coach_notes,
    extract_rep_range_from_notes,
    extract_rpe_from_notes,
    get_rpe_for_range,
    parse_rep_range,
    sanitize_routine_for_update,
)

logger = structlog.get_logger()

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


_VALID_SET_TYPES = frozenset({"warmup", "normal", "dropset", "failure"})


def _normalize_routine_data(data: dict[str, Any]) -> dict[str, Any]:
    """Convert response-format routine data to update-input format.

    Strips read-only fields and maps field-name differences so that JSON
    obtained from ``routines get`` can be fed directly into ``routines update``.

    CRITICAL: Never includes folder_id - Hevy API rejects PUT with folder_id (400 error).
    Preserves all set types (warmup, normal, dropset, failure).
    """
    # Use centralized sanitization to strip all forbidden/read-only fields
    sanitize_routine_for_update(data)

    normalized: dict[str, Any] = {
        "title": data["title"],
        "notes": data.get("notes"),
        "exercises": [],
    }

    # Validate and log set types being preserved
    set_type_counts: dict[str, int] = {}

    for ex in data.get("exercises", []):
        norm_sets = []
        for s in ex.get("sets", []):
            set_type = s.get("type", "normal")

            # Validate set type (Hevy API only accepts these 4 values)
            if set_type not in _VALID_SET_TYPES:
                logger.warning(
                    "invalid_set_type_detected",
                    exercise=ex.get("title", "unknown"),
                    set_type=set_type,
                    defaulting_to="normal",
                )
                set_type = "normal"

            set_type_counts[set_type] = set_type_counts.get(set_type, 0) + 1

            rep_range = s.get("rep_range")
            norm_sets.append(
                {
                    "type": set_type,
                    "weight_kg": s.get("weight_kg"),
                    "reps": s.get("reps"),
                    "distance_meters": s.get("distance_meters"),
                    "duration_seconds": s.get("duration_seconds"),
                    "custom_metric": s.get("custom_metric"),
                    "rep_range": rep_range,
                }
            )
        normalized["exercises"].append(
            {
                "exercise_template_id": ex["exercise_template_id"],
                # Response uses "supersets_id"; input model uses "superset_id"
                "superset_id": ex.get("superset_id") or ex.get("supersets_id"),
                "rest_seconds": ex.get("rest_seconds"),
                "notes": ex.get("notes"),
                "sets": norm_sets,
            }
        )

    logger.debug(
        "normalized_routine_data",
        title=normalized["title"],
        exercise_count=len(normalized["exercises"]),
        set_types=set_type_counts,
    )

    return normalized


@click.group()
def routines() -> None:
    """Manage routines."""


@routines.command("list")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--page-size", default=5, type=int, help="Items per page (max 10)")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@click.option("--folder-id", type=int, default=None, help="Filter by folder ID")
@click.option("--search", type=str, default=None, help="Search routines by name (case-insensitive)")
@format_option
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
@format_option
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
@format_option
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
@format_option
@click.pass_context
def update_routine(ctx: click.Context, routine_id: str, file_path: str) -> None:
    """Update an existing routine.

    Follows the read-first pattern: verifies the routine exists before updating.
    Normalizes payload to strip folder_id and preserve set types.
    """
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))

    # Step 1: Verify routine exists (read-first pattern from lessons learned)
    try:
        existing = client.get_routine(routine_id)
        logger.debug(
            "update_read_first",
            routine_id=routine_id,
            title=existing.title,
            exercise_count=len(existing.exercises),
        )
    except Exception as e:
        raise click.ClickException(f"Routine {routine_id} not found: {e}") from None

    # Step 2: Load and normalize the update payload
    data = client.load_json_file(file_path)
    routine_data = data.get("routine", data)
    normalized = _normalize_routine_data(routine_data)
    routine = RoutineUpdateInput.model_validate(normalized)

    # Step 3: Apply update
    result = client.update_routine(routine_id, routine)
    output(result, fmt=fmt, columns=ROUTINE_COLUMNS, title="Updated Routine")
    click.echo("✅ Routine updated", err=True)


@routines.command("rename")
@click.argument("id_or_search")
@click.argument("new_name")
@format_option
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
    normalized = _normalize_routine_data(routine)
    normalized["title"] = new_name
    update_data = RoutineUpdateInput.model_validate(normalized)

    result = client.update_routine(routine_id, update_data)
    output(result, fmt=fmt, columns=ROUTINE_COLUMNS, title="Renamed Routine")
    click.echo(f"✅ Routine renamed: '{old_title}' → '{new_name}'", err=True)


@routines.command("enhance")
@click.argument("routine_id")
@click.option(
    "--output", "-o", "output_path", type=click.Path(), help="Save enhanced routine to JSON file"
)
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option(
    "--rest-only",
    is_flag=True,
    help="Apply only rest_seconds; leave exercise notes and weights untouched",
)
@click.option(
    "--working-weight-multiplier",
    default=1.0,
    type=float,
    help="Multiplier for working weights (e.g., 0.9 for deload)",
)
@format_option
@click.pass_context
def enhance_routine(
    ctx: click.Context,
    routine_id: str,
    output_path: str | None,
    dry_run: bool,
    rest_only: bool,
    working_weight_multiplier: float,
) -> None:
    """Enhance a routine with smart defaults (rest_seconds, RPE, progression rules).

    Follows the 3-step pattern: read → enhance → update.
    Preserves all coach data (set types, notes, exercise order). Existing
    RPE@N or RPE@N-M guidance takes precedence over generated RPE guidance.
    With --rest-only, only rest_seconds is changed.

    ROUTINE_ID is the UUID of the routine to enhance.
    """
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))

    if rest_only and working_weight_multiplier != 1.0:
        click.echo(
            "⚠️ --working-weight-multiplier is ignored with --rest-only",
            err=True,
        )

    logger.info("enhancing_routine", routine_id=routine_id, dry_run=dry_run)

    # Step 1: Read original routine
    click.echo(f"📖 Reading routine {routine_id}...", err=True)
    try:
        routine = client.get_routine(routine_id)
    except Exception as e:
        raise click.ClickException(f"Failed to fetch routine: {e}") from None

    routine_dict = routine.model_dump()
    original_exercises = routine_dict.get("exercises", [])

    click.echo(f"   Found {len(original_exercises)} exercises", err=True)

    # Step 2: Enhance exercises
    enhanced_exercises = []
    changes_log = []

    for _idx, ex in enumerate(original_exercises):
        original_notes = ex.get("notes", "") or ""
        sets = ex.get("sets", [])

        # Extract rep range from notes
        rep_range = extract_rep_range_from_notes(original_notes)
        rep_low, rep_high = parse_rep_range(rep_range)
        inferred_single_reps = rep_low is not None and rep_low == rep_high

        # Calculate rest_seconds based on rep range
        rest_seconds = calculate_rest_seconds(rep_range) if rep_range else 90
        original_rest = ex.get("rest_seconds")
        if original_rest != rest_seconds:
            original_rest_display = original_rest if original_rest is not None else "unset"
            changes_log.append(
                f"  {ex.get('title', 'Exercise')}: rest {original_rest_display} -> {rest_seconds}"
            )

        # Prefer the coach's maximum permitted RPE over a generic default.
        coach_rpe = extract_rpe_from_notes(original_notes)
        target_rpe = (
            coach_rpe
            if coach_rpe is not None
            else (get_rpe_for_range(rep_range) if rep_range and not inferred_single_reps else None)
        )

        # Build progression rule based on rep range
        progression_rule = None
        if rep_range and not inferred_single_reps:
            progression_rule = f"Add weight when hitting top of {rep_range} rep range"

        # Enhance notes (append, never replace)
        enhanced_notes = original_notes
        if not rest_only:
            enhanced_notes = enhance_coach_notes(
                original_notes,
                target_rpe=target_rpe,
                progression_rule=progression_rule,
            )

        if enhanced_notes != original_notes:
            changes_log.append(f"  {ex.get('title', 'Exercise')}: enhanced notes")

        # Process sets - preserve types, calculate weights for warmup/dropset
        enhanced_sets = []
        working_weight = None

        for s in sets:
            set_type = s.get("type", "normal")
            weight_kg = s.get("weight_kg")

            # Track working weight from first normal set
            if set_type == "normal" and weight_kg and working_weight is None:
                working_weight = weight_kg * working_weight_multiplier

            # Calculate warmup/dropset weights if working weight known
            final_weight = weight_kg
            if not rest_only and working_weight and weight_kg is None:
                if set_type == "warmup":
                    final_weight = calculate_warmup_weight(working_weight)
                    changes_log.append(f"    Added warmup: {final_weight}kg")
                elif set_type == "dropset":
                    final_weight = calculate_dropset_weight(working_weight)
                    changes_log.append(f"    Added dropset: {final_weight}kg")

            enhanced_sets.append(
                {
                    "type": set_type,
                    "weight_kg": final_weight,
                    "reps": s.get("reps"),
                    "distance_meters": s.get("distance_meters"),
                    "duration_seconds": s.get("duration_seconds"),
                    "custom_metric": s.get("custom_metric"),
                    "rep_range": s.get("rep_range"),
                }
            )

        enhanced_exercises.append(
            {
                "exercise_template_id": ex["exercise_template_id"],
                "superset_id": ex.get("superset_id") or ex.get("supersets_id"),
                "rest_seconds": rest_seconds,
                "notes": enhanced_notes,
                "sets": enhanced_sets,
            }
        )

    # Build enhanced routine payload (NO folder_id - lesson learned!)
    enhanced_payload = {
        "title": routine_dict["title"],
        "notes": routine_dict.get("notes"),
        "exercises": enhanced_exercises,
    }

    # Show changes
    click.echo("\n📝 Changes to be applied:", err=True)
    if changes_log:
        for line in changes_log:
            click.echo(line, err=True)
    else:
        click.echo("  No significant changes needed", err=True)

    click.echo(f"\n   Exercises: {len(enhanced_exercises)}", err=True)
    click.echo(
        f"   Average rest: {sum(e.get('rest_seconds', 90) for e in enhanced_exercises) // len(enhanced_exercises)}s",
        err=True,
    )

    # Save to file if requested
    if output_path:
        output_data = {"routine": enhanced_payload}
        Path(output_path).write_text(json.dumps(output_data, indent=2))
        click.echo(f"\n💾 Saved enhanced routine to {output_path}", err=True)

    # Step 3: Update if not dry-run
    if not dry_run:
        click.echo("\n🚀 Updating routine...", err=True)
        try:
            update_data = RoutineUpdateInput.model_validate(enhanced_payload)
            result = client.update_routine(routine_id, update_data)
            output(result, fmt=fmt, columns=ROUTINE_COLUMNS, title="Enhanced Routine")
            click.echo("✅ Routine enhanced successfully", err=True)
        except Exception as e:
            raise click.ClickException(f"Failed to update routine: {e}") from None
    else:
        click.echo("\n⏸️ Dry run - no changes applied", err=True)
        if fmt == "json":
            output({"routine": enhanced_payload}, fmt="json")
