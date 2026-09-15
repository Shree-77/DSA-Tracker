"""Domain-specific exception hierarchy.

Every application error carries a stable machine-readable ``code``, a human
message, an HTTP status, and an optional ``details`` payload. Raw database
exceptions are never surfaced to clients (see ``handlers.py``).
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all handled application errors."""

    code: str = "APP_ERROR"
    status_code: int = 400
    message: str = "Application error"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details or {}
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404
    message = "Resource not found"


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409
    message = "Resource conflict"


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422
    message = "Validation error"


class ImportValidationError(AppError):
    """Raised when an Excel import fails validation.

    ``details['errors']`` holds a list of per-row error messages so the client
    can display them clearly (e.g. "Row 17: Day number is missing.").
    """

    code = "IMPORT_VALIDATION_ERROR"
    status_code = 422
    message = "The uploaded plan could not be imported"

    def __init__(
        self,
        errors: list[str],
        *,
        message: str | None = None,
    ) -> None:
        super().__init__(message=message, details={"errors": errors})
