"""Secure API-key storage using the operating system credential store."""

from __future__ import annotations

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

SERVICE_NAME = "hevy-cli"
ACCOUNT_NAME = "api-key"


class CredentialStoreError(RuntimeError):
    """Raised when the system credential store cannot complete an operation."""


def get_api_key(*, strict: bool = False) -> str | None:
    """Return the API key from the system credential store.

    Normal CLI commands treat an unavailable keyring as an absent credential so
    legacy config-file authentication can still work. Authentication-management
    commands use strict mode to surface keyring failures to the user.
    """
    try:
        return keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
    except KeyringError as exc:
        if strict:
            raise CredentialStoreError(str(exc)) from exc
        return None


def store_api_key(api_key: str) -> None:
    """Store an API key in the system credential store."""
    try:
        keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, api_key)
    except KeyringError as exc:
        raise CredentialStoreError(str(exc)) from exc


def delete_api_key() -> bool:
    """Delete the stored API key, returning whether one was removed."""
    try:
        keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
    except PasswordDeleteError:
        return False
    except KeyringError as exc:
        raise CredentialStoreError(str(exc)) from exc
    return True
