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
    # functools.wraps below shadows the wrapper's signature with fn's, which
    # some mypy versions read as incompatible with pass_context's expected
    # Callable shape. The `unused-ignore` tag quiets the newer mypy that can
    # actually see through it. Either way, the call is safe at runtime.
    @click.pass_context  # type: ignore[arg-type, unused-ignore]
    @functools.wraps(fn)
    def wrapper(ctx: click.Context, output_format: str, *args: Any, **kwargs: Any) -> Any:
        if ctx.get_parameter_source("output_format") == ParameterSource.COMMANDLINE:
            ctx.obj["output_format"] = output_format

        return fn(*args, **kwargs)

    return wrapper
