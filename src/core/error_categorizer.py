from typing import Optional, Type

from src.exceptions.errors import (
    ServiceUnavailableError,
    TimeoutError,
    UnauthorizedError,
    InvalidPayloadError,
    QuotaExceededError,
    TransientError,
    PermanentError,
)


class ErrorCategorizer:
    """Categorizes errors based on status codes or exception types."""

    @staticmethod
    def from_status(service: str, status_code: int, message: str = ""):
        if status_code in (500, 502, 503, 504):
            return ServiceUnavailableError(message or f"{service} transient error {status_code}", service)
        if status_code == 401:
            return UnauthorizedError(message or f"{service} unauthorized", service)
        if status_code == 400:
            return InvalidPayloadError(message or f"{service} invalid payload", service)
        if status_code == 429:
            return QuotaExceededError(message or f"{service} quota exceeded", service)
        # Default: treat 4xx other than 401/400/429 as permanent
        if 400 <= status_code < 500:
            return InvalidPayloadError(message or f"{service} client error {status_code}", service)
        # Default server-side errors transient
        if status_code >= 500:
            return ServiceUnavailableError(message or f"{service} server error {status_code}", service)
        return InvalidPayloadError(message or f"{service} unexpected status {status_code}", service)

    @staticmethod
    def is_transient(error: Exception) -> bool:
        return isinstance(error, TransientError)

    @staticmethod
    def is_permanent(error: Exception) -> bool:
        return isinstance(error, PermanentError)
