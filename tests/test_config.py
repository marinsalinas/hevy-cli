"""Tests for configuration management."""

from __future__ import annotations

from pathlib import Path

import pytest

from hevy_cli.config import (
    DEFAULT_CONFIG,
    _deep_merge,
    config_dir,
    config_path,
    data_dir,
    get_nested,
    load_config,
    save_config,
    set_nested,
)


class TestDeepMerge:
    def test_simple_merge(self) -> None:
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self) -> None:
        base = {"auth": {"api_key": "", "extra": True}}
        override = {"auth": {"api_key": "new-key"}}
        result = _deep_merge(base, override)
        assert result["auth"]["api_key"] == "new-key"
        assert result["auth"]["extra"] is True


class TestGetNested:
    def test_get_top_level(self) -> None:
        assert get_nested({"a": 1}, "a") == 1

    def test_get_nested(self) -> None:
        assert get_nested({"auth": {"api_key": "test"}}, "auth.api_key") == "test"

    def test_get_missing(self) -> None:
        assert get_nested({"a": 1}, "b.c") is None


class TestSetNested:
    def test_set_existing(self) -> None:
        config: dict = {"auth": {"api_key": ""}}
        set_nested(config, "auth.api_key", "new-key")
        assert config["auth"]["api_key"] == "new-key"

    def test_set_creates_intermediate(self) -> None:
        config: dict = {}
        set_nested(config, "new.nested.key", "value")
        assert config["new"]["nested"]["key"] == "value"

    def test_set_bool_coercion(self) -> None:
        config: dict = {"output": {"color": True}}
        set_nested(config, "output.color", "false")
        assert config["output"]["color"] is False

    def test_set_int_coercion(self) -> None:
        config: dict = {"api": {"timeout": 30}}
        set_nested(config, "api.timeout", "60")
        assert config["api"]["timeout"] == 60


class TestLoadSave:
    def test_load_returns_defaults_when_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "hevy_cli.config.config_path", lambda: tmp_path / "nonexistent" / "config.toml"
        )
        config = load_config()
        assert config["api"]["base_url"] == "https://api.hevy.com"

    def test_save_and_load(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr("hevy_cli.config.config_path", lambda: config_file)

        config = DEFAULT_CONFIG.copy()
        config["auth"]["api_key"] = "test-key-123"
        save_config(config)

        loaded = load_config()
        assert loaded["auth"]["api_key"] == "test-key-123"


# ── Path resolvers ────────────────────────────────────────────────────────────
# These opt out of the autouse `isolated_config` fixture in conftest.py so the
# real config_path()/config_dir()/data_dir() functions execute, with platformdirs
# mocked instead. Without the opt-out, `config_path` is monkeypatched to a stub
# and its body is never exercised.


@pytest.mark.no_isolated_config
def test_config_dir_wraps_platformdirs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hevy_cli.config.platformdirs.user_config_dir", lambda app: "/fake/conf")
    assert config_dir() == Path("/fake/conf")


@pytest.mark.no_isolated_config
def test_data_dir_wraps_platformdirs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hevy_cli.config.platformdirs.user_data_dir", lambda app: "/fake/data")
    assert data_dir() == Path("/fake/data")


@pytest.mark.no_isolated_config
def test_config_path_appends_config_toml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hevy_cli.config.platformdirs.user_config_dir", lambda app: "/fake/conf")
    assert config_path() == Path("/fake/conf") / "config.toml"
