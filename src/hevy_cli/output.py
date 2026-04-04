"""Output formatting — JSON, table (rich), YAML."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from collections.abc import Sequence


def _to_dicts(data: Any) -> Any:
    """Convert Pydantic models or lists of models to dicts."""
    if isinstance(data, BaseModel):
        return data.model_dump()
    if isinstance(data, list):
        return [_to_dicts(item) for item in data]
    return data


def format_json(data: Any) -> str:
    """Format data as pretty JSON."""
    return json.dumps(_to_dicts(data), indent=2, default=str)


def format_yaml(data: Any) -> str:
    """Format data as YAML."""
    result: str = yaml.dump(_to_dicts(data), default_flow_style=False, sort_keys=False)
    return result


def format_table(
    data: Sequence[Any],
    columns: list[tuple[str, str]],
    title: str | None = None,
) -> None:
    """Render data as a rich table to stdout.

    Args:
        data: List of items (dicts or Pydantic models).
        columns: List of (header, key) tuples.
        title: Optional table title.
    """
    console = Console()
    table = Table(title=title, show_lines=False, pad_edge=True)

    for header, _ in columns:
        table.add_column(header, overflow="fold")

    for item in data:
        d = item.model_dump() if isinstance(item, BaseModel) else item
        row = []
        for _, key in columns:
            value = d.get(key, "")
            row.append(str(value) if value is not None else "—")
        table.add_row(*row)

    console.print(table)


def output(
    data: Any,
    fmt: str = "table",
    columns: list[tuple[str, str]] | None = None,
    title: str | None = None,
) -> None:
    """Route output to the correct formatter.

    Args:
        data: Data to output (model, list, dict).
        fmt: Format — "json", "yaml", or "table".
        columns: Column specs for table format.
        title: Table title.
    """
    if fmt == "json":
        print(format_json(data))
    elif fmt == "yaml":
        print(format_yaml(data))
    elif fmt == "table" and columns:
        items = data if isinstance(data, list) else [data]
        format_table(items, columns, title=title)
    else:
        # Fallback to JSON if no columns specified for table
        print(format_json(data))


def detect_format(explicit: str | None) -> str:
    """Detect output format: explicit > TTY detection."""
    if explicit:
        return explicit
    return "table" if sys.stdout.isatty() else "json"
