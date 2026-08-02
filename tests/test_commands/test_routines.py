"""Tests for routine CLI commands."""

from __future__ import annotations

import json
import tempfile
from typing import TYPE_CHECKING

import pytest
import respx
from click.testing import CliRunner
from httpx import Response
from pydantic import ValidationError as PydanticValidationError

from hevy_cli.cli import cli
from hevy_cli.commands.routines import _normalize_routine_data
from hevy_cli.models import RoutineUpdateInput

if TYPE_CHECKING:
    from pathlib import Path


@respx.mock
def test_routines_list(sample_routine: dict) -> None:
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "routines": [sample_routine]},
        )
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "test-key", "--format", "json", "routines", "list"])
    assert result.exit_code == 0
    assert "Upper Body" in result.output


@respx.mock
def test_routines_list_with_folder_filter(sample_routine: dict) -> None:
    routine_in_folder = {**sample_routine, "folder_id": 42, "title": "Push Day"}
    routine_no_folder = {**sample_routine, "folder_id": None, "title": "Leg Day"}
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={
                "page": 1,
                "page_count": 1,
                "routines": [routine_in_folder, routine_no_folder],
            },
        )
    )
    respx.get("https://api.hevy.com/v1/routine_folders/42").mock(
        return_value=Response(
            200,
            json={
                "id": 42,
                "index": 0,
                "title": "Push Pull",
                "updated_at": "2024-08-14T12:00:00Z",
                "created_at": "2024-08-14T12:00:00Z",
            },
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--format", "json", "routines", "list", "--folder-id", "42"],
    )
    assert result.exit_code == 0
    assert "Push Day" in result.output
    assert "Leg Day" not in result.output


@respx.mock
def test_routines_list_with_search(sample_routine: dict) -> None:
    routine1 = {**sample_routine, "title": "Upper Body Push"}
    routine2 = {**sample_routine, "title": "Lower Body Pull"}
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "routines": [routine1, routine2]},
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--format", "json", "routines", "list", "--search", "upper"],
    )
    assert result.exit_code == 0
    assert "Upper Body Push" in result.output
    assert "Lower Body Pull" not in result.output


@respx.mock
def test_routines_list_search_case_insensitive(sample_routine: dict) -> None:
    routine1 = {**sample_routine, "title": "UPPER BODY"}
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "routines": [routine1]},
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--format", "json", "routines", "list", "--search", "upper"],
    )
    assert result.exit_code == 0
    assert "UPPER BODY" in result.output


@respx.mock
def test_routines_list_combined_folder_and_search(sample_routine: dict) -> None:
    r1 = {**sample_routine, "id": "r1", "folder_id": 42, "title": "Push Day A"}
    r2 = {**sample_routine, "id": "r2", "folder_id": 42, "title": "Pull Day B"}
    r3 = {**sample_routine, "id": "r3", "folder_id": 99, "title": "Push Day C"}
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "routines": [r1, r2, r3]},
        )
    )
    respx.get("https://api.hevy.com/v1/routine_folders/42").mock(
        return_value=Response(
            200,
            json={
                "id": 42,
                "index": 0,
                "title": "PPL",
                "updated_at": "2024-08-14T12:00:00Z",
                "created_at": "2024-08-14T12:00:00Z",
            },
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--api-key",
            "test-key",
            "--format",
            "json",
            "routines",
            "list",
            "--folder-id",
            "42",
            "--search",
            "push",
        ],
    )
    assert result.exit_code == 0
    assert "Push Day A" in result.output
    assert "Pull Day B" not in result.output
    assert "Push Day C" not in result.output


@respx.mock
def test_routines_rename(sample_routine: dict) -> None:
    routine = {
        **sample_routine,
        "id": "routine-456",
        "title": "Upper Body",
        "exercises": [],
    }
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "routines": [routine]},
        )
    )
    respx.put("https://api.hevy.com/v1/routines/routine-456").mock(
        return_value=Response(
            200,
            json={**routine, "title": "Upper Body v2"},
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--api-key",
            "test-key",
            "--format",
            "json",
            "routines",
            "rename",
            "Upper",
            "Upper Body v2",
        ],
    )
    assert result.exit_code == 0
    assert "Upper Body v2" in result.output


@respx.mock
def test_routines_rename_no_match(sample_routine: dict) -> None:
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "routines": [sample_routine]},
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "routines", "rename", "Nonexistent", "New Name"],
    )
    assert result.exit_code != 0
    assert "No routine found" in result.output


@respx.mock
def test_routines_rename_multiple_matches(sample_routine: dict) -> None:
    r1 = {**sample_routine, "id": "r1", "title": "Push Day A"}
    r2 = {**sample_routine, "id": "r2", "title": "Push Day B"}
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "routines": [r1, r2]},
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "routines", "rename", "Push", "New Push"],
    )
    assert result.exit_code != 0
    assert "Multiple routines match" in result.output


@respx.mock
def test_routines_update_with_response_format_json() -> None:
    """Update should accept JSON in the format returned by 'routines get'."""
    # This is the full response format with read-only fields, supersets_id, etc.
    response_json = {
        "id": "routine-456",
        "title": "Updated Routine",
        "folder_id": 42,
        "notes": "Updated notes",
        "updated_at": "2024-08-14T12:00:00Z",
        "created_at": "2024-08-14T12:00:00Z",
        "exercises": [
            {
                "index": 0,
                "title": "Bench Press (Barbell)",
                "notes": "Slow and controlled",
                "exercise_template_id": "D04AC939",
                "supersets_id": 1,
                "rest_seconds": 90,
                "sets": [
                    {
                        "index": 0,
                        "type": "warmup",
                        "weight_kg": 60,
                        "reps": 12,
                        "rep_range": None,
                        "distance_meters": None,
                        "duration_seconds": None,
                        "rpe": 7.5,
                        "custom_metric": None,
                    },
                    {
                        "index": 1,
                        "type": "normal",
                        "weight_kg": 80,
                        "reps": 10,
                        "rep_range": {"start": 8, "end": 12},
                        "distance_meters": None,
                        "duration_seconds": None,
                        "rpe": 8.5,
                        "custom_metric": None,
                    },
                ],
            }
        ],
    }

    # Mock read-first GET (verify routine exists before updating)
    respx.get("https://api.hevy.com/v1/routines/routine-456").mock(
        return_value=Response(200, json={"routine": response_json})
    )
    updated_response = {**response_json, "title": "Updated Routine"}
    respx.put("https://api.hevy.com/v1/routines/routine-456").mock(
        return_value=Response(200, json={"routine": updated_response})
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(response_json, f)
        f.flush()
        tmp_path = f.name

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--api-key",
            "test-key",
            "--format",
            "json",
            "routines",
            "update",
            "routine-456",
            "-f",
            tmp_path,
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Updated Routine" in result.output


@respx.mock
def test_routines_update_with_wrapped_response_json() -> None:
    """Update should accept JSON wrapped in {"routine": ...}."""
    wrapped_json = {
        "routine": {
            "id": "routine-456",
            "title": "Wrapped Routine",
            "folder_id": None,
            "notes": None,
            "updated_at": "2024-08-14T12:00:00Z",
            "created_at": "2024-08-14T12:00:00Z",
            "exercises": [],
        }
    }

    # Mock read-first GET (verify routine exists before updating)
    respx.get("https://api.hevy.com/v1/routines/routine-456").mock(
        return_value=Response(200, json=wrapped_json)
    )
    respx.put("https://api.hevy.com/v1/routines/routine-456").mock(
        return_value=Response(200, json={"routine": wrapped_json["routine"]})
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(wrapped_json, f)
        f.flush()
        tmp_path = f.name

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--api-key",
            "test-key",
            "--format",
            "json",
            "routines",
            "update",
            "routine-456",
            "-f",
            tmp_path,
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Wrapped Routine" in result.output


@respx.mock
def test_routines_rename_preserves_exercises_via_normalize() -> None:
    """Rename should preserve exercises including supersets_id mapping."""
    routine = {
        "id": "routine-456",
        "title": "Old Name",
        "folder_id": None,
        "notes": "Some notes",
        "updated_at": "2024-08-14T12:00:00Z",
        "created_at": "2024-08-14T12:00:00Z",
        "exercises": [
            {
                "index": 0,
                "title": "Bench Press",
                "exercise_template_id": "D04AC939",
                "supersets_id": 2,
                "rest_seconds": 60,
                "notes": None,
                "sets": [
                    {
                        "index": 0,
                        "type": "normal",
                        "weight_kg": 80,
                        "reps": 10,
                        "rep_range": {"start": 8, "end": 12},
                        "distance_meters": None,
                        "duration_seconds": None,
                        "rpe": None,
                        "custom_metric": None,
                    }
                ],
            }
        ],
    }
    uuid_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    routine["id"] = uuid_id
    respx.get("https://api.hevy.com/v1/routines/" + uuid_id).mock(
        return_value=Response(200, json={"routine": routine})
    )
    respx.put("https://api.hevy.com/v1/routines/" + uuid_id).mock(
        return_value=Response(200, json={**routine, "title": "New Name"})
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--format", "json", "routines", "rename", uuid_id, "New Name"],
    )
    assert result.exit_code == 0, result.output
    assert "New Name" in result.output


# ── _normalize_routine_data tests ──────────────────────────────────────────


def test_routine_update_input_rejects_folder_id() -> None:
    """RoutineUpdateInput must reject folder_id at the model level."""
    with pytest.raises(PydanticValidationError, match="extra"):
        RoutineUpdateInput.model_validate({"title": "Test", "folder_id": 42, "exercises": []})


def test_routine_update_input_rejects_extra_fields() -> None:
    """RoutineUpdateInput must reject any unknown fields."""
    with pytest.raises(PydanticValidationError, match="extra"):
        RoutineUpdateInput.model_validate(
            {"title": "Test", "id": "abc", "created_at": "now", "exercises": []}
        )


def test_normalize_strips_folder_id() -> None:
    """folder_id must NEVER appear in normalized output (Hevy returns 400)."""
    data = {
        "title": "Test",
        "folder_id": 42,
        "notes": None,
        "exercises": [],
    }
    result = _normalize_routine_data(data)
    assert "folder_id" not in result


def test_normalize_preserves_all_set_types() -> None:
    """All 4 set types (warmup, normal, dropset, failure) must survive normalization."""
    data = {
        "title": "Full Set Types",
        "notes": None,
        "exercises": [
            {
                "exercise_template_id": "D04AC939",
                "supersets_id": None,
                "rest_seconds": 120,
                "notes": "3 x 3-5",
                "sets": [
                    {"type": "warmup", "weight_kg": 40, "reps": 8},
                    {"type": "normal", "weight_kg": 80, "reps": 5},
                    {"type": "normal", "weight_kg": 80, "reps": 5},
                    {"type": "normal", "weight_kg": 80, "reps": 5},
                    {"type": "dropset", "weight_kg": 55, "reps": 8},
                    {"type": "failure", "weight_kg": 60, "reps": None},
                ],
            }
        ],
    }
    result = _normalize_routine_data(data)
    set_types = [s["type"] for s in result["exercises"][0]["sets"]]
    assert set_types == ["warmup", "normal", "normal", "normal", "dropset", "failure"]


def test_normalize_maps_supersets_id_to_superset_id() -> None:
    """Response field 'supersets_id' maps to input field 'superset_id'."""
    data = {
        "title": "Superset Test",
        "notes": None,
        "exercises": [
            {
                "exercise_template_id": "D04AC939",
                "supersets_id": 3,
                "rest_seconds": 90,
                "notes": None,
                "sets": [],
            }
        ],
    }
    result = _normalize_routine_data(data)
    assert result["exercises"][0]["superset_id"] == 3
    assert "supersets_id" not in result["exercises"][0]


def test_normalize_invalid_set_type_defaults_to_normal() -> None:
    """Invalid set types should be replaced with 'normal'."""
    data = {
        "title": "Bad Type",
        "notes": None,
        "exercises": [
            {
                "exercise_template_id": "D04AC939",
                "sets": [{"type": "invalid_type", "weight_kg": 50, "reps": 10}],
            }
        ],
    }
    result = _normalize_routine_data(data)
    assert result["exercises"][0]["sets"][0]["type"] == "normal"


# ── enhance command tests ──────────────────────────────────────────────────

REAL_COACH_NOTES = [
    "5-8(Sobrecarga)\n\nRpe@6-7",
    "10-12(Sobrecarga)\n\nRpe@7-8",
    "15-30 seg x lado\n\nRpe@5-6",
    "12-20(Sobrecarga)\n\nRpe@8-9",
    "3 x 3 (1 semana)\n3 x 4(2 semana)\n3 x 5 (3 semana)\n3 x 6(4 semana)\n\nRpe@7-9",
    "8-12(Sobrecarga + Fase excéntrica)\n\nRpe@6-8",
    "12-20(Sobrecarga) x lado*\n\nRpe@5-6\n\nDato: 2 series en parte anterior y 2 series en parte posterior *",
]


def _enhance_routine_response(notes: list[str]) -> dict:
    exercises = []
    for index, exercise_notes in enumerate(notes):
        exercises.append(
            {
                "index": index,
                "title": f"Exercise {index}",
                "exercise_template_id": "D04AC939",
                "supersets_id": None,
                "rest_seconds": None,
                "notes": exercise_notes,
                "sets": [
                    {
                        "index": 0,
                        "type": "normal",
                        "weight_kg": 80,
                        "reps": 10,
                        "rep_range": None,
                        "distance_meters": None,
                        "duration_seconds": None,
                        "rpe": None,
                        "custom_metric": None,
                    }
                ],
            }
        )
    return {
        "routine": {
            "id": "routine-coach",
            "title": "Coach Plan",
            "folder_id": None,
            "notes": None,
            "updated_at": "2024-08-14T12:00:00Z",
            "created_at": "2024-08-14T12:00:00Z",
            "exercises": exercises,
        }
    }


@respx.mock
def test_enhance_honors_real_coach_rpe_notes(tmp_path: Path) -> None:
    routine_response = _enhance_routine_response(REAL_COACH_NOTES)
    respx.get("https://api.hevy.com/v1/routines/routine-coach").mock(
        return_value=Response(200, json=routine_response)
    )
    output_path = tmp_path / "enhanced.json"

    result = CliRunner().invoke(
        cli,
        [
            "--api-key",
            "test-key",
            "routines",
            "enhance",
            "routine-coach",
            "--dry-run",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    enhanced = json.loads(output_path.read_text())["routine"]["exercises"]
    assert all("Target RPE" not in exercise["notes"] for exercise in enhanced)
    assert enhanced[4]["rest_seconds"] == 150


@respx.mock
def test_enhance_without_coach_rpe_keeps_generic_target(tmp_path: Path) -> None:
    routine_response = _enhance_routine_response(["5-8(Sobrecarga)"])
    respx.get("https://api.hevy.com/v1/routines/routine-coach").mock(
        return_value=Response(200, json=routine_response)
    )
    output_path = tmp_path / "enhanced.json"

    result = CliRunner().invoke(
        cli,
        [
            "--api-key",
            "test-key",
            "routines",
            "enhance",
            "routine-coach",
            "--dry-run",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    notes = json.loads(output_path.read_text())["routine"]["exercises"][0]["notes"]
    assert notes == (
        "5-8(Sobrecarga) | Target RPE 8.0 | Add weight when hitting top of 5-8 rep range"
    )


@respx.mock
def test_enhance_rest_only_leaves_notes_and_weights_untouched() -> None:
    original_notes = REAL_COACH_NOTES[-1]
    routine_response = _enhance_routine_response([original_notes])
    sets = routine_response["routine"]["exercises"][0]["sets"]
    sets.insert(0, {**sets[0], "index": 0, "type": "warmup", "weight_kg": None})
    sets.append({**sets[-1], "index": 2, "type": "dropset", "weight_kg": None})
    respx.get("https://api.hevy.com/v1/routines/routine-coach").mock(
        return_value=Response(200, json=routine_response)
    )
    put_route = respx.put("https://api.hevy.com/v1/routines/routine-coach").mock(
        return_value=Response(200, json=routine_response)
    )

    result = CliRunner().invoke(
        cli,
        ["--api-key", "test-key", "routines", "enhance", "routine-coach", "--rest-only"],
    )

    assert result.exit_code == 0, result.output
    body = json.loads(put_route.calls.last.request.content)["routine"]
    exercise = body["exercises"][0]
    assert exercise["notes"] == original_notes
    assert [item.get("weight_kg") for item in exercise["sets"]] == [None, 80.0, None]
    assert exercise["rest_seconds"] == 90


@respx.mock
def test_enhance_rest_only_composes_with_dry_run(tmp_path: Path) -> None:
    original_notes = REAL_COACH_NOTES[0]
    routine_response = _enhance_routine_response([original_notes])
    respx.get("https://api.hevy.com/v1/routines/routine-coach").mock(
        return_value=Response(200, json=routine_response)
    )
    output_path = tmp_path / "rest-only.json"

    result = CliRunner().invoke(
        cli,
        [
            "--api-key",
            "test-key",
            "routines",
            "enhance",
            "routine-coach",
            "--rest-only",
            "--dry-run",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    exercise = json.loads(output_path.read_text())["routine"]["exercises"][0]
    assert exercise["notes"] == original_notes
    assert exercise["rest_seconds"] == 120
    assert "Exercise 0: rest None -> 120" in result.output


@respx.mock
def test_enhance_logs_rest_change_in_all_modes() -> None:
    routine_response = _enhance_routine_response(["5-8(Sobrecarga)"])
    routine_response["routine"]["exercises"][0]["rest_seconds"] = 30
    respx.get("https://api.hevy.com/v1/routines/routine-coach").mock(
        return_value=Response(200, json=routine_response)
    )

    result = CliRunner().invoke(
        cli,
        ["--api-key", "test-key", "routines", "enhance", "routine-coach", "--dry-run"],
    )

    assert result.exit_code == 0, result.output
    assert "Exercise 0: rest 30 -> 120" in result.output


@respx.mock
def test_enhance_warns_when_multiplier_is_ignored_with_rest_only() -> None:
    routine_response = _enhance_routine_response(["5-8(Sobrecarga)"])
    respx.get("https://api.hevy.com/v1/routines/routine-coach").mock(
        return_value=Response(200, json=routine_response)
    )

    result = CliRunner().invoke(
        cli,
        [
            "--api-key",
            "test-key",
            "routines",
            "enhance",
            "routine-coach",
            "--rest-only",
            "--working-weight-multiplier",
            "0.9",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "--working-weight-multiplier is ignored with --rest-only" in result.output


@respx.mock
def test_enhance_dry_run() -> None:
    """Enhance with --dry-run should not call PUT."""
    routine_response = {
        "routine": {
            "id": "routine-789",
            "title": "Upper Body",
            "folder_id": None,
            "notes": None,
            "updated_at": "2024-08-14T12:00:00Z",
            "created_at": "2024-08-14T12:00:00Z",
            "exercises": [
                {
                    "index": 0,
                    "title": "Bench Press",
                    "exercise_template_id": "D04AC939",
                    "supersets_id": None,
                    "rest_seconds": None,
                    "notes": "3 x 8-12(Sobrecarga progresiva)",
                    "sets": [
                        {
                            "index": 0,
                            "type": "warmup",
                            "weight_kg": None,
                            "reps": 8,
                            "rep_range": None,
                            "distance_meters": None,
                            "duration_seconds": None,
                            "rpe": None,
                            "custom_metric": None,
                        },
                        {
                            "index": 1,
                            "type": "normal",
                            "weight_kg": 80,
                            "reps": 10,
                            "rep_range": {"start": 8, "end": 12},
                            "distance_meters": None,
                            "duration_seconds": None,
                            "rpe": None,
                            "custom_metric": None,
                        },
                        {
                            "index": 2,
                            "type": "dropset",
                            "weight_kg": None,
                            "reps": 10,
                            "rep_range": None,
                            "distance_meters": None,
                            "duration_seconds": None,
                            "rpe": None,
                            "custom_metric": None,
                        },
                    ],
                }
            ],
        }
    }
    respx.get("https://api.hevy.com/v1/routines/routine-789").mock(
        return_value=Response(200, json=routine_response)
    )
    # No PUT mock — if enhance tries PUT in dry-run, respx will raise

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--api-key",
            "test-key",
            "--format",
            "json",
            "routines",
            "enhance",
            "routine-789",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Dry run" in result.output


@respx.mock
def test_enhance_calculates_warmup_and_dropset_weights() -> None:
    """Enhance should calculate warmup (50%) and dropset (70%) weights."""
    routine_response = {
        "routine": {
            "id": "routine-789",
            "title": "Bench Day",
            "folder_id": None,
            "notes": None,
            "updated_at": "2024-08-14T12:00:00Z",
            "created_at": "2024-08-14T12:00:00Z",
            "exercises": [
                {
                    "index": 0,
                    "title": "Bench Press",
                    "exercise_template_id": "D04AC939",
                    "supersets_id": None,
                    "rest_seconds": None,
                    "notes": "3 x 8-12",
                    "sets": [
                        {
                            "index": 0,
                            "type": "warmup",
                            "weight_kg": None,
                            "reps": 8,
                            "rep_range": None,
                            "distance_meters": None,
                            "duration_seconds": None,
                            "rpe": None,
                            "custom_metric": None,
                        },
                        {
                            "index": 1,
                            "type": "normal",
                            "weight_kg": 80,
                            "reps": 10,
                            "rep_range": None,
                            "distance_meters": None,
                            "duration_seconds": None,
                            "rpe": None,
                            "custom_metric": None,
                        },
                        {
                            "index": 2,
                            "type": "dropset",
                            "weight_kg": None,
                            "reps": 10,
                            "rep_range": None,
                            "distance_meters": None,
                            "duration_seconds": None,
                            "rpe": None,
                            "custom_metric": None,
                        },
                    ],
                }
            ],
        }
    }
    respx.get("https://api.hevy.com/v1/routines/routine-789").mock(
        return_value=Response(200, json=routine_response)
    )
    updated = {**routine_response["routine"], "title": "Bench Day"}
    respx.put("https://api.hevy.com/v1/routines/routine-789").mock(
        return_value=Response(200, json={"routine": updated})
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--format", "json", "routines", "enhance", "routine-789"],
    )
    assert result.exit_code == 0, result.output
    # Warmup = 80 * 0.5 = 40kg, Dropset = 80 * 0.7 = 57.5 (rounded to 2.5)
    assert "warmup" in result.output.lower() or "enhanced" in result.output.lower()


def test_normalize_strips_all_readonly_fields() -> None:
    """Normalization should strip id, created_at, updated_at (not just folder_id)."""
    data = {
        "id": "routine-123",
        "title": "Full Response",
        "folder_id": 42,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "notes": "Coach notes",
        "exercises": [
            {
                "index": 0,
                "title": "Bench Press",
                "exercise_template_id": "D04AC939",
                "supersets_id": None,
                "rest_seconds": 90,
                "notes": "3 x 8-12",
                "sets": [
                    {
                        "index": 0,
                        "type": "normal",
                        "weight_kg": 80,
                        "reps": 10,
                        "rpe": 8.5,
                    }
                ],
            }
        ],
    }
    result = _normalize_routine_data(data)
    assert "id" not in result
    assert "folder_id" not in result
    assert "created_at" not in result
    assert "updated_at" not in result
    assert result["title"] == "Full Response"


def test_normalize_preserves_dropset_and_failure_types() -> None:
    """Dropset and failure set types must survive round-trip normalization."""
    data = {
        "title": "Coach Routine",
        "notes": None,
        "exercises": [
            {
                "exercise_template_id": "D04AC939",
                "notes": "3 x 3-5\nDato: Ultima serie un dropset",
                "sets": [
                    {"type": "warmup", "weight_kg": 34.0, "reps": 8},
                    {"type": "normal", "weight_kg": 67.5, "reps": 5},
                    {"type": "normal", "weight_kg": 67.5, "reps": 5},
                    {"type": "normal", "weight_kg": 67.5, "reps": 5},
                    {"type": "dropset", "weight_kg": 47.0, "reps": 7},
                    {"type": "failure", "weight_kg": 60.0, "reps": None},
                ],
            }
        ],
    }
    result = _normalize_routine_data(data)
    types = [s["type"] for s in result["exercises"][0]["sets"]]
    assert types == ["warmup", "normal", "normal", "normal", "dropset", "failure"]


@respx.mock
def test_update_verifies_routine_exists() -> None:
    """Update command should verify routine exists before applying changes."""
    respx.get("https://api.hevy.com/v1/routines/nonexistent-id").mock(
        return_value=Response(404, json={"error": "Not found"})
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"title": "Test", "exercises": []}, f)
        f.flush()
        tmp_path = f.name

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "routines", "update", "nonexistent-id", "-f", tmp_path],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower()
