"""Configuration management commands."""

from __future__ import annotations

import click

from ..config import config_path, get_nested, load_config, save_config, set_nested
from ..output import format_json


@click.group("config")
def config() -> None:
    """Manage CLI configuration."""


@config.command("show")
def show_config() -> None:
    """Show current configuration."""
    cfg = load_config()
    # Mask API key for display
    if cfg.get("auth", {}).get("api_key"):
        key = cfg["auth"]["api_key"]
        cfg["auth"]["api_key"] = key[:4] + "..." + key[-4:] if len(key) > 8 else "***"
    click.echo(format_json(cfg))
    click.echo(f"\nConfig file: {config_path()}", err=True)


@config.command("get")
@click.argument("key")
def get_value(key: str) -> None:
    """Get a config value (dot notation, e.g. auth.api_key)."""
    cfg = load_config()
    value = get_nested(cfg, key)
    if value is None:
        raise click.ClickException(f"Key '{key}' not found")
    click.echo(value)


@config.command("set")
@click.argument("key")
@click.argument("value")
def set_value(key: str, value: str) -> None:
    """Set a config value (dot notation, e.g. auth.api_key YOUR_KEY)."""
    cfg = load_config()
    set_nested(cfg, key, value)
    save_config(cfg)
    click.echo(f"✅ Set {key}", err=True)


@config.command("path")
def show_path() -> None:
    """Show the config file path."""
    click.echo(config_path())
