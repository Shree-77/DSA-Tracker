"""Password hashing and JWT helpers.

Kept dependency-light and framework-agnostic so it can be unit-tested in
isolation. Password hashing uses bcrypt directly (avoids passlib's fragile
bcrypt-version detection); tokens are signed with the app's JWT secret.

bcrypt only considers the first 72 bytes of a password, so inputs are
pre-truncated to 72 *bytes* (not chars) to avoid ValueError on long inputs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import settings

_MAX_BCRYPT_BYTES = 72


def _prepare(password: str) -> bytes:
    """Encode and truncate a password to bcrypt's 72-byte input limit."""
    return password.encode("utf-8")[:_MAX_BCRYPT_BYTES]


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash (utf-8 string) for a plaintext password."""
    hashed = bcrypt.hashpw(_prepare(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time verification of a plaintext password against its hash."""
    try:
        return bcrypt.checkpw(
            _prepare(plain_password), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        # Malformed/legacy hash in the DB — treat as a failed match.
        return False


def create_access_token(
    subject: str | int, *, expires_minutes: int | None = None
) -> str:
    """Create a signed JWT whose ``sub`` claim is the user id."""
    minutes = expires_minutes or settings.access_token_expire_minutes
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT. Returns the claims dict or None if invalid."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None
