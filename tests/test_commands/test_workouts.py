"""Tests for workout CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import respx
from click.testing import CliRunner
from httpx import Response

from hevy_cli.cli import cli

if TYPE_CHECKING:
    from pathlib import Path


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
def test_debug_logs_stay_out_of_json_stdout(sample_workout: dict) -> None:
    respx.get("https://api.hevy.com/v1/workouts").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "workouts": [sample_workout]},
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--debug", "--format", "json", "workouts", "list"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)[0]["id"] == sample_workout["id"]
    assert "hevy_request" not in result.stdout
    assert "hevy_request" in result.stderr


@respx.mock
def test_workouts_count() -> None:
    respx.get("https://api.hevy.com/v1/workouts/count").mock(
        return_value=Response(200, json={"workout_count": 42})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "test-key", "workouts", "count"])
    assert result.exit_code == 0
    assert "42" in result.output


@respx.mock
def test_authentication_error_is_clean() -> None:
    respx.get("https://api.hevy.com/v1/workouts/count").mock(
        return_value=Response(401, json={"error": "InvalidApiKey: secret-test-key"})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "secret-test-key", "workouts", "count"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == (
        "Error: InvalidApiKey: [REDACTED]\n"
        "Check HEVY_API_KEY or run 'hevy config show' to verify your configuration.\n"
    )
    assert "Traceback" not in result.stderr
    assert "secret-test-key" not in result.stderr
    assert "secret-test-key" not in result.stdout


@respx.mock
def test_authentication_error_with_debug_includes_traceback() -> None:
    respx.get("https://api.hevy.com/v1/workouts/count").mock(
        return_value=Response(401, json={"error": "InvalidApiKey: secret-test-key"})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "secret-test-key", "--debug", "workouts", "count"])

    assert result.exit_code == 1
    assert "Traceback (most recent call last)" in result.stderr
    assert "AuthenticationError: InvalidApiKey: [REDACTED]" in result.stderr
    assert "secret-test-key" not in result.stderr
    assert "secret-test-key" not in result.stdout


@respx.mock
def test_not_found_error_is_clean() -> None:
    respx.get("https://api.hevy.com/v1/workouts/count").mock(
        return_value=Response(404, json={"error": "missing"})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "test-key", "workouts", "count"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "Error: Resource 'missing' not found\n"
    assert "Traceback" not in result.stderr


@respx.mock
def test_authentication_error_is_clean_for_folders_subgroup() -> None:
    respx.get("https://api.hevy.com/v1/routine_folders").mock(
        return_value=Response(401, json={"error": "InvalidApiKey"})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "test-key", "folders", "list"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == (
        "Error: InvalidApiKey\n"
        "Check HEVY_API_KEY or run 'hevy config show' to verify your configuration.\n"
    )
    assert "Traceback" not in result.stderr


@respx.mock
def test_json_error_does_not_write_partial_output() -> None:
    respx.get("https://api.hevy.com/v1/workouts").mock(
        return_value=Response(401, json={"error": "InvalidApiKey"})
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--api-key", "test-key", "--format", "json", "workouts", "list"],
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("Error: InvalidApiKey\n")


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


@respx.mock
def test_workouts_list_uses_api_key_and_base_url_from_config(
    isolated_config: Path, sample_workout: dict
) -> None:
    """Auth + base_url resolve from XDG config when --api-key/env are absent.

    Exercises the cli.py fallback path: load_config() -> get_nested(config, ...)
    for both auth.api_key and api.base_url, plus the HevyClient construction
    branch that uses the config-supplied values.
    """
    isolated_config.write_text(
        '[auth]\napi_key = "key-from-config"\n[api]\nbase_url = "https://config.api.example"\n'
    )
    respx.get("https://config.api.example/v1/workouts").mock(
        return_value=Response(
            200,
            json={"page": 1, "page_count": 1, "workouts": [sample_workout]},
        )
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--format", "json", "workouts", "list"],
        env={"HEVY_API_KEY": ""},
    )
    assert result.exit_code == 0, result.output
    assert "abc-123" in result.output
