"""Tests for authentication commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner

from hevy_cli.cli import cli

if TYPE_CHECKING:
    from pathlib import Path


def test_auth_login_stores_hidden_prompt_value(monkeypatch) -> None:
    stored: list[str] = []
    monkeypatch.setattr("hevy_cli.commands.auth_cmd.store_api_key", stored.append)

    result = CliRunner().invoke(cli, ["auth", "login"], input="secret-key\n")

    assert result.exit_code == 0, result.output
    assert stored == ["secret-key"]
    assert "secret-key" not in result.output
    assert "stored securely" in result.output


def test_auth_status_reports_environment_override(monkeypatch) -> None:
    monkeypatch.setattr("hevy_cli.commands.auth_cmd.get_api_key", lambda **kwargs: "stored-key")

    result = CliRunner().invoke(
        cli,
        ["auth", "status"],
        env={"HEVY_API_KEY": "environment-key"},
    )

    assert result.exit_code == 0
    assert "HEVY_API_KEY" in result.output
    assert "overrides" in result.output


def test_auth_status_reports_keychain(monkeypatch) -> None:
    monkeypatch.setattr("hevy_cli.commands.auth_cmd.get_api_key", lambda **kwargs: "stored-key")

    result = CliRunner().invoke(cli, ["auth", "status"], env={"HEVY_API_KEY": ""})

    assert result.exit_code == 0
    assert "system credential store" in result.output


def test_auth_status_reports_legacy_config(monkeypatch, isolated_config: Path) -> None:
    isolated_config.write_text('[auth]\napi_key = "legacy-key"\n')
    monkeypatch.setattr("hevy_cli.commands.auth_cmd.get_api_key", lambda **kwargs: None)

    result = CliRunner().invoke(cli, ["auth", "status"], env={"HEVY_API_KEY": ""})

    assert result.exit_code == 0
    assert "plaintext config (legacy)" in result.output
    assert "auth login" in result.output


def test_auth_logout_removes_key(monkeypatch) -> None:
    monkeypatch.setattr("hevy_cli.commands.auth_cmd.delete_api_key", lambda: True)

    result = CliRunner().invoke(cli, ["auth", "logout"])

    assert result.exit_code == 0
    assert "removed" in result.output


def test_auth_logout_is_idempotent(monkeypatch) -> None:
    monkeypatch.setattr("hevy_cli.commands.auth_cmd.delete_api_key", lambda: False)

    result = CliRunner().invoke(cli, ["auth", "logout"])

    assert result.exit_code == 0
    assert "No API key" in result.output
