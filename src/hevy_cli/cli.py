"""Main CLI entry point with lazy-loaded command groups."""

from __future__ import annotations

import logging
import os
import sys
from typing import ClassVar

import click
import structlog

from . import __version__
from .client import HevyClient
from .config import get_nested, load_config
from .exceptions import HevyError


def _configure_logging(verbose: bool, debug: bool) -> None:
    """Configure structlog based on verbosity."""
    if debug:
        level = "DEBUG"
    elif verbose:
        level = "INFO"
    else:
        level = "ERROR"

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level, 40)  # 40 = ERROR
        ),
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
    )


class LazyGroup(click.Group):
    """Click group that lazy-loads subcommands on first access."""

    COMMAND_MAP: ClassVar[dict[str, str]] = {
        "workouts": "hevy_cli.commands.workouts:workouts",
        "routines": "hevy_cli.commands.routines:routines",
        "folders": "hevy_cli.commands.folders:folders",
        "exercises": "hevy_cli.commands.exercises:exercises",
        "config": "hevy_cli.commands.config_cmd:config",
    }

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(self.COMMAND_MAP.keys())

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name not in self.COMMAND_MAP:
            return None
        import importlib
        module_path, attr = self.COMMAND_MAP[cmd_name].rsplit(":", 1)
        module = importlib.import_module(module_path)
        return getattr(module, attr)


@click.group(cls=LazyGroup)
@click.version_option(version=__version__, prog_name="hevy")
@click.option("--api-key", envvar="HEVY_API_KEY", help="Hevy API key")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "yaml"]), help="Output format")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--debug", is_flag=True, help="Debug output (includes HTTP requests)")
@click.pass_context
def cli(ctx: click.Context, api_key: str | None, output_format: str | None, verbose: bool, debug: bool) -> None:
    """hevy — CLI for the Hevy workout tracking API."""
    _configure_logging(verbose, debug)
    ctx.ensure_object(dict)

    config = load_config()
    ctx.obj["config"] = config
    ctx.obj["output_format"] = output_format

    # Resolve API key: flag > env > config
    resolved_key = api_key or os.environ.get("HEVY_API_KEY") or get_nested(config, "auth.api_key")
    if resolved_key:
        ctx.obj["client"] = HevyClient(
            api_key=resolved_key,
            base_url=get_nested(config, "api.base_url") or "https://api.hevy.com",
            timeout=get_nested(config, "api.timeout") or 30,
            max_retries=get_nested(config, "api.max_retries") or 3,
        )
    else:
        ctx.obj["client"] = None  # Will fail on commands that need it


def get_client(ctx: click.Context) -> HevyClient:
    """Get the HevyClient from context, raising if not configured."""
    client = ctx.obj.get("client")
    if client is None:
        raise click.ClickException(
            "API key required. Set HEVY_API_KEY, use --api-key, or run: hevy config set auth.api_key YOUR_KEY"
        )
    return client


def main() -> None:
    """Entry point for the CLI."""
    try:
        cli()
    except HevyError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
