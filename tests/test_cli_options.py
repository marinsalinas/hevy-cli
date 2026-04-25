"""Cross-cutting tests for shared CLI option decorators.

These tests assert that option decorators defined in `hevy_cli.options`
work after the subcommand name on every read-path command in the CLI.
See issue #10.
"""

from __future__ import annotations

import pytest
import respx
from click.testing import CliRunner
from httpx import Response

from hevy_cli.cli import cli

BASE_URL = "https://api.hevy.com"


# ── List / count / events / history endpoints ────────────────────────────────
# Bodies here are minimal shapes that pass pydantic validation. The test only
# asserts exit_code == 0, so empty collections are sufficient.

LIST_STYLE_CASES: list[tuple[list[str], str, dict[str, object]]] = [
    (
        ["workouts", "list"],
        "/v1/workouts",
        {"page": 1, "page_count": 1, "workouts": []},
    ),
    (
        ["workouts", "count"],
        "/v1/workouts/count",
        {"workout_count": 0},
    ),
    (
        ["workouts", "events"],
        "/v1/workouts/events",
        {"page": 1, "page_count": 1, "events": []},
    ),
    (
        ["routines", "list"],
        "/v1/routines",
        {"page": 1, "page_count": 1, "routines": []},
    ),
    (
        ["folders", "list"],
        "/v1/routine_folders",
        {"page": 1, "page_count": 1, "routine_folders": []},
    ),
    (
        ["exercises", "list"],
        "/v1/exercise_templates",
        {"page": 1, "page_count": 1, "exercise_templates": []},
    ),
    (
        ["exercises", "history", "D04AC939"],
        "/v1/exercise_history/D04AC939",
        {"exercise_history": []},
    ),
]


@pytest.mark.parametrize("cmd_path,mock_path,mock_body", LIST_STYLE_CASES)
@respx.mock
def test_format_after_subcommand_list_style(
    cmd_path: list[str],
    mock_path: str,
    mock_body: dict[str, object],
) -> None:
    respx.get(f"{BASE_URL}{mock_path}").mock(return_value=Response(200, json=mock_body))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", *cmd_path, "--format", "json"],
    )
    assert result.exit_code == 0, result.output


# ── Single-object GET endpoints ──────────────────────────────────────────────
# Use the existing fixtures in conftest.py for realistic response bodies that
# satisfy pydantic validation on the typed models.

GET_STYLE_CASES: list[tuple[list[str], str, str]] = [
    (["workouts", "get", "abc-123"], "/v1/workouts/abc-123", "sample_workout"),
    (["routines", "get", "routine-456"], "/v1/routines/routine-456", "sample_routine"),
    (["folders", "get", "42"], "/v1/routine_folders/42", "sample_folder"),
    (
        ["exercises", "get", "D04AC939"],
        "/v1/exercise_templates/D04AC939",
        "sample_exercise_template",
    ),
]


@pytest.mark.parametrize("cmd_path,mock_path,fixture_name", GET_STYLE_CASES)
@respx.mock
def test_format_after_subcommand_get_style(
    cmd_path: list[str],
    mock_path: str,
    fixture_name: str,
    request: pytest.FixtureRequest,
) -> None:
    body = request.getfixturevalue(fixture_name)
    respx.get(f"{BASE_URL}{mock_path}").mock(return_value=Response(200, json=body))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", *cmd_path, "--format", "json"],
    )
    assert result.exit_code == 0, result.output
