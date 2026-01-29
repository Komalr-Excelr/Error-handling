from typing import Optional


class AppError(Exception):
    """Base application error with a category attribute."""

    def __init__(self, message: str, service: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.service = service

    @property
    def category(self) -> str:
        return "unknown"


class TransientError(AppError):
    @property
    def category(self) -> str:
        return "transient"


class PermanentError(AppError):
    @property
    def category(self) -> str:
        return "permanent"


# Specific errors
class ServiceUnavailableError(TransientError):
    """HTTP 503 Service Unavailable"""


class TimeoutError(TransientError):
    """Network timeout or similar transient connectivity issue."""


class UnauthorizedError(PermanentError):
    """HTTP 401 Unauthorized"""


class InvalidPayloadError(PermanentError):
    """Bad request due to invalid payload."""


class QuotaExceededError(PermanentError):
    """Quota exceeded at provider."""


class FailFastError(TransientError):
    """Raised when circuit breaker is open and call should fail fast."""
