"""Configuration management using XDG directories and TOML."""

from __future__ import annotations

import copy
import tomllib
from pathlib import Path
from typing import Any

import platformdirs
import tomli_w

APP_NAME = "hevy"
DEFAULT_BASE_URL = "https://api.hevy.com"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_OUTPUT_FORMAT = "table"

DEFAULT_CONFIG: dict[str, Any] = {
    "auth": {"api_key": ""},
    "output": {"format": DEFAULT_OUTPUT_FORMAT, "color": True},
    "api": {
        "base_url": DEFAULT_BASE_URL,
        "timeout": DEFAULT_TIMEOUT,
        "max_retries": DEFAULT_MAX_RETRIES,
    },
}


def config_dir() -> Path:
    """Return the XDG config directory for the app."""
    return Path(platformdirs.user_config_dir(APP_NAME))


def data_dir() -> Path:
    """Return the XDG data directory for the app."""
    return Path(platformdirs.user_data_dir(APP_NAME))


def config_path() -> Path:
    """Return the path to config.toml."""
    return config_dir() / "config.toml"


def load_config() -> dict[str, Any]:
    """Load config from TOML file, merging with defaults."""
    path = config_path()
    if not path.exists():
        return copy.deepcopy(DEFAULT_CONFIG)

    with open(path, "rb") as f:
        user_config = tomllib.load(f)

    # Deep merge: defaults ← user overrides. deepcopy is required because
    # _deep_merge mutates its `base` argument in place; a shallow .copy()
    # would let it write through into DEFAULT_CONFIG's nested dicts.
    merged = _deep_merge(copy.deepcopy(DEFAULT_CONFIG), user_config)
    return merged


def save_config(config: dict[str, Any]) -> None:
    """Save config to TOML file."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config, f)


def get_nested(config: dict[str, Any], key: str) -> Any:
    """Get a nested config value using dot notation (e.g., 'auth.api_key')."""
    parts = key.split(".")
    current: Any = config
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def set_nested(config: dict[str, Any], key: str, value: Any) -> None:
    """Set a nested config value using dot notation."""
    parts = key.split(".")
    current = config
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    # Attempt type coercion based on defaults
    default_val = get_nested(DEFAULT_CONFIG, key)
    if isinstance(default_val, bool):
        value = value.lower() in ("true", "1", "yes") if isinstance(value, str) else bool(value)
    elif isinstance(default_val, int):
        value = int(value)
    current[parts[-1]] = value


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override into base."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
