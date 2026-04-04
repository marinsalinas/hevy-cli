"""Routine folder commands."""

from __future__ import annotations

import click

from ..cli import get_client
from ..output import detect_format, output

FOLDER_COLUMNS = [
    ("ID", "id"),
    ("Title", "title"),
    ("Index", "index"),
    ("Updated", "updated_at"),
    ("Created", "created_at"),
]


@click.group()
def folders() -> None:
    """Manage routine folders."""


@folders.command("list")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--page-size", default=5, type=int, help="Items per page (max 10)")
@click.pass_context
def list_folders(ctx: click.Context, page: int, page_size: int) -> None:
    """List routine folders."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    result = client.list_folders(page=page, page_size=page_size)
    items = [f.model_dump() for f in result.routine_folders]
    output(
        items,
        fmt=fmt,
        columns=FOLDER_COLUMNS,
        title=f"Folders (page {result.page}/{result.page_count})",
    )


@folders.command("get")
@click.argument("folder_id")
@click.pass_context
def get_folder(ctx: click.Context, folder_id: str) -> None:
    """Get a folder by ID."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    result = client.get_folder(folder_id)
    output(result, fmt=fmt, columns=FOLDER_COLUMNS, title="Folder")


@folders.command("create")
@click.argument("title")
@click.pass_context
def create_folder(ctx: click.Context, title: str) -> None:
    """Create a routine folder."""
    client = get_client(ctx)
    fmt = detect_format(ctx.obj.get("output_format"))
    result = client.create_folder(title)
    output(result, fmt=fmt, columns=FOLDER_COLUMNS, title="Created Folder")
    click.echo("✅ Folder created", err=True)
