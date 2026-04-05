"""Tests for routines rename command — ID and search paths."""

from __future__ import annotations

import respx
from click.testing import CliRunner
from httpx import Response

from hevy_cli.cli import cli

ROUTINE_BASE = {
    "id": "9289019e-4266-4775-bad9-668c8015f747",
    "title": "Upper - Lunes",
    "folder_id": None,
    "notes": "Focus on form",
    "updated_at": "2024-08-14T12:00:00Z",
    "created_at": "2024-08-14T12:00:00Z",
    "exercises": [
        {
            "index": 0,
            "title": "Bench Press (Barbell)",
            "exercise_template_id": "D04AC939",
            "supersets_id": None,
            "rest_seconds": 90,
            "notes": "",
            "sets": [
                {
                    "index": 0,
                    "type": "normal",
                    "weight_kg": 60,
                    "reps": 10,
                    "distance_meters": None,
                    "duration_seconds": None,
                    "custom_metric": None,
                    "rep_range": None,
                }
            ],
        }
    ],
}


@respx.mock
def test_rename_by_uuid() -> None:
    """When first arg is a UUID, fetch routine by ID directly (no search)."""
    rid = ROUTINE_BASE["id"]
    respx.get(f"https://api.hevy.com/v1/routines/{rid}").mock(
        return_value=Response(200, json={"routine": ROUTINE_BASE})
    )
    respx.put(f"https://api.hevy.com/v1/routines/{rid}").mock(
        return_value=Response(200, json={**ROUTINE_BASE, "title": "2026.04.01 - Upper"})
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
            rid,
            "2026.04.01 - Upper",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "2026.04.01" in result.output


@respx.mock
def test_rename_by_search() -> None:
    """When first arg is NOT a UUID, search all routines by partial name."""
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "routines": [ROUTINE_BASE]},
        )
    )
    respx.put(f"https://api.hevy.com/v1/routines/{ROUTINE_BASE['id']}").mock(
        return_value=Response(200, json={**ROUTINE_BASE, "title": "2026.04.01 - Upper"})
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
            "Upper - Lunes",
            "2026.04.01 - Upper",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "2026.04.01" in result.output


@respx.mock
def test_rename_by_search_no_match() -> None:
    """Search that matches nothing should fail with a clear message."""
    respx.get("https://api.hevy.com/v1/routines").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "routines": [ROUTINE_BASE]},
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
def test_rename_by_search_multiple_matches() -> None:
    """Multiple matches should fail listing the ambiguous routines."""
    r1 = {**ROUTINE_BASE, "id": "r1", "title": "Push Day A"}
    r2 = {**ROUTINE_BASE, "id": "r2", "title": "Push Day B"}
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
