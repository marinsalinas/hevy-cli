"""Tests for workout CLI commands."""

from __future__ import annotations

import json

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


@respx.mock
def test_workouts_list_with_since(multi_workout_response: dict) -> None:
    respx.get("https://api.hevy.com/v1/workouts").mock(
        return_value=Response(
            200,
            json=multi_workout_response,
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--format", "json", "workouts", "list", "--since", "2024-08-12"],
    )
    assert result.exit_code == 0

    parsed = json.loads(result.output)
    ids = [w["id"] for w in parsed]

    assert len(ids) == 2
    assert "workout-aug-10" not in ids
    assert "workout-aug-14" in ids
    assert "workout-aug-20" in ids


@respx.mock
def test_workouts_list_with_until(multi_workout_response: dict) -> None:
    respx.get("https://api.hevy.com/v1/workouts").mock(
        return_value=Response(
            200,
            json=multi_workout_response,
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--format", "json", "workouts", "list", "--until", "2024-08-15"],
    )
    assert result.exit_code == 0

    parsed = json.loads(result.output)
    ids = [w["id"] for w in parsed]

    assert len(ids) == 2
    assert "workout-aug-20" not in ids
    assert "workout-aug-14" in ids
    assert "workout-aug-10" in ids


@respx.mock
def test_workouts_list_with_since_and_until(multi_workout_response: dict) -> None:
    respx.get("https://api.hevy.com/v1/workouts").mock(
        return_value=Response(
            200,
            json=multi_workout_response,
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
            "workouts",
            "list",
            "--since",
            "2024-08-12",
            "--until",
            "2024-08-18",
        ],
    )
    assert result.exit_code == 0

    parsed = json.loads(result.output)
    ids = [w["id"] for w in parsed]

    assert len(ids) == 1
    assert "workout-aug-10" not in ids
    assert "workout-aug-20" not in ids
    assert "workout-aug-14" in ids


def test_workouts_list_invalid_date(multi_workout_response: dict) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--format", "json", "workouts", "list", "--until", "08-15-2024"],
    )
    assert result.exit_code != 0

    assert "is not valid" in result.output
