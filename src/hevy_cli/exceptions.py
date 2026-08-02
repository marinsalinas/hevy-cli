"""Custom exception hierarchy for Hevy API errors."""

from __future__ import annotations


class HevyError(Exception):
    """Base exception for all Hevy CLI errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(HevyError):
    """Raised when API key is missing or invalid (401/403)."""

    def __init__(self, message: str = "Invalid or missing API key") -> None:
        super().__init__(message, status_code=401)


class NotFoundError(HevyError):
    """Raised when a resource is not found (404)."""

    def __init__(self, resource: str, resource_id: str | None = None) -> None:
        message = (
            f"{resource} '{resource_id}' not found" if resource_id else f"{resource} not found"
        )
        super().__init__(message, status_code=404)


class ValidationError(HevyError):
    """Raised when request body is invalid (400)."""

    def __init__(self, message: str = "Invalid request") -> None:
        super().__init__(message, status_code=400)


class RateLimitError(HevyError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f" — retry after {retry_after}s"
        super().__init__(msg, status_code=429)


class ServerError(HevyError):
    """Raised on server-side errors (5xx)."""

    def __init__(self, status_code: int = 500, message: str = "Server error") -> None:
        super().__init__(message, status_code=status_code)


class ConfigError(HevyError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
