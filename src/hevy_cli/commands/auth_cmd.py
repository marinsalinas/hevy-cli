"""Authentication commands backed by the operating system credential store."""

from __future__ import annotations

import os

import click

from ..config import get_nested, load_config
from ..credentials import CredentialStoreError, delete_api_key, get_api_key, store_api_key


def _credential_error(exc: CredentialStoreError) -> click.ClickException:
    detail = f": {exc}" if str(exc) else ""
    return click.ClickException(f"Unable to access the system credential store{detail}")


@click.group("auth")
def auth() -> None:
    """Manage Hevy API authentication."""


@auth.command("login")
def login() -> None:
    """Store a Hevy API key securely in the system credential store."""
    api_key = click.prompt("Hevy API key", hide_input=True).strip()
    if not api_key:
        raise click.ClickException("API key cannot be empty")

    try:
        store_api_key(api_key)
    except CredentialStoreError as exc:
        raise _credential_error(exc) from exc

    click.echo("API key stored securely in the system credential store.", err=True)


@auth.command("status")
def status() -> None:
    """Show which authentication source the CLI will use."""
    if os.environ.get("HEVY_API_KEY"):
        click.echo("Authenticated via HEVY_API_KEY (overrides stored credentials).")
        return

    try:
        stored_key = get_api_key(strict=True)
    except CredentialStoreError as exc:
        raise _credential_error(exc) from exc

    if stored_key:
        click.echo("Authenticated via the system credential store.")
        return

    config_key = get_nested(load_config(), "auth.api_key")
    if config_key:
        click.echo("Authenticated via plaintext config (legacy). Run `hevy auth login` to migrate.")
        return

    raise click.ClickException("Not authenticated. Run: hevy auth login")


@auth.command("logout")
def logout() -> None:
    """Remove the Hevy API key from the system credential store."""
    try:
        removed = delete_api_key()
    except CredentialStoreError as exc:
        raise _credential_error(exc) from exc

    if removed:
        click.echo("API key removed from the system credential store.", err=True)
    else:
        click.echo("No API key was stored in the system credential store.", err=True)
