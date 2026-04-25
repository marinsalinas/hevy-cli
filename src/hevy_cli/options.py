import functools
from collections.abc import Callable
from typing import Any

import click
from click.core import ParameterSource


def format_option(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Attach ``--format`` to a subcommand and plumb it into ``ctx.obj``.

    The value only overrides ``ctx.obj["output_format"]`` when the user
    passed ``--format`` explicitly at this level (detected via
    ``ParameterSource.COMMANDLINE``). Otherwise the group-level value
    set in ``cli.py`` wins, preserving the TTY auto-detect behavior in
    ``output.detect_format``.
    """

    @click.option(
        "--format",
        "output_format",
        type=click.Choice(["json", "table", "yaml"]),
        help="Output format",
        default=None,
    )
    @click.pass_context  # type: ignore[arg-type]  # functools.wraps wraps the signature in a way mypy can't see through
    @functools.wraps(fn)
    def wrapper(ctx: click.Context, output_format: str, *args: Any, **kwargs: Any) -> Any:
        if ctx.get_parameter_source("output_format") == ParameterSource.COMMANDLINE:
            ctx.obj["output_format"] = output_format

        return fn(*args, **kwargs)

    return wrapper
