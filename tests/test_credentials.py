"""Tests for secure credential storage."""

from __future__ import annotations

import pytest
from keyring.errors import KeyringError, PasswordDeleteError

from hevy_cli.credentials import (
    ACCOUNT_NAME,
    SERVICE_NAME,
    CredentialStoreError,
    delete_api_key,
    get_api_key,
    store_api_key,
)


def test_get_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda service, account: "stored-key")

    assert get_api_key() == "stored-key"


def test_get_api_key_uses_stable_identifiers(monkeypatch: pytest.MonkeyPatch) -> None:
    called_with: tuple[str, str] | None = None

    def fake_get_password(service: str, account: str) -> str:
        nonlocal called_with
        called_with = (service, account)
        return "stored-key"

    monkeypatch.setattr("keyring.get_password", fake_get_password)

    get_api_key()

    assert called_with == (SERVICE_NAME, ACCOUNT_NAME)


def test_get_api_key_treats_unavailable_keyring_as_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: str) -> str:
        raise KeyringError("unavailable")

    monkeypatch.setattr("keyring.get_password", fail)

    assert get_api_key() is None


def test_get_api_key_strict_surfaces_keyring_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: str) -> str:
        raise KeyringError("unavailable")

    monkeypatch.setattr("keyring.get_password", fail)

    with pytest.raises(CredentialStoreError, match="unavailable"):
        get_api_key(strict=True)


def test_store_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    called_with: tuple[str, str, str] | None = None

    def fake_set_password(service: str, account: str, api_key: str) -> None:
        nonlocal called_with
        called_with = (service, account, api_key)

    monkeypatch.setattr("keyring.set_password", fake_set_password)

    store_api_key("secret")

    assert called_with == (SERVICE_NAME, ACCOUNT_NAME, "secret")


def test_store_api_key_surfaces_keyring_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: str) -> None:
        raise KeyringError("locked")

    monkeypatch.setattr("keyring.set_password", fail)

    with pytest.raises(CredentialStoreError, match="locked"):
        store_api_key("secret")


def test_delete_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("keyring.delete_password", lambda service, account: None)

    assert delete_api_key() is True


def test_delete_api_key_returns_false_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(*args: str) -> None:
        raise PasswordDeleteError("not found")

    monkeypatch.setattr("keyring.delete_password", missing)

    assert delete_api_key() is False
