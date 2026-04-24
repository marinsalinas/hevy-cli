"""Tests for workout CLI commands."""

from __future__ import annotations

import respx
from click.testing import CliRunner
from httpx import Response

from hevy_cli.cli import cli


@respx.mock
def test_workouts_list(sample_workout: dict) -> None:
    respx.get("https://api.hevy.com/v1/workouts").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "workouts": [sample_workout]},
        )
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "test-key", "--format", "json", "workouts", "list"])
    assert result.exit_code == 0
    assert "Morning Workout" in result.output


@respx.mock
def test_workouts_list_format_works_after_subcommand(sample_workout: dict) -> None:
    respx.get("https://api.hevy.com/v1/workouts").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "workouts": [sample_workout]},
        )
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "test-key", "workouts", "list", "--format", "json"])
    assert result.exit_code == 0
    assert "Morning Workout" not in result.output


@respx.mock
def test_workouts_count() -> None:
    respx.get("https://api.hevy.com/v1/workouts/count").mock(
        return_value=Response(200, json={"workout_count": 42})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "test-key", "workouts", "count"])
    assert result.exit_code == 0
    assert "42" in result.output


def test_workouts_list_no_api_key() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["workouts", "list"], env={"HEVY_API_KEY": ""})
    assert result.exit_code != 0
    assert "API key required" in result.output
