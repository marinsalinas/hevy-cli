"""Tests for routine CLI commands."""

from __future__ import annotations

import respx
from click.testing import CliRunner
from httpx import Response

from hevy_cli.cli import cli


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
