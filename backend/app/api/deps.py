"""Shared API dependencies (authentication)."""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services import AuthService
from app.services.auth_service import AuthError

# auto_error=False so we can raise our own consistent AppError envelope.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the ``Authorization: Bearer`` header."""
    if credentials is None or not credentials.credentials:
        raise AuthError("Not authenticated.", code="NOT_AUTHENTICATED")
    return AuthService(db).user_from_token(credentials.credentials)
