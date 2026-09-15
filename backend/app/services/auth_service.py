"""Auth service: registration, login, and current-user resolution."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import AppError, ConflictError, NotFoundError
from app.models import User
from app.repositories import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# Precomputed bcrypt hash used to equalise login timing when the username
# does not exist (mitigates username enumeration via response timing).
_DUMMY_HASH = hash_password("dummy-password-for-timing-equalisation")


class AuthError(AppError):
    """401 for bad credentials / invalid tokens."""

    code = "AUTH_ERROR"
    status_code = 401
    message = "Could not authenticate"


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> TokenResponse:
        # Fast-path uniqueness check (case-insensitive).
        if self.users.get_by_username(payload.username) is not None:
            raise ConflictError(
                "That username is already taken.",
                code="USERNAME_TAKEN",
                details={"username": payload.username},
            )
        try:
            user = self.users.create(
                username=payload.username,
                password_hash=hash_password(payload.password),
            )
            self.db.commit()
        except IntegrityError:
            # Race: another request registered the same username concurrently.
            self.db.rollback()
            raise ConflictError(
                "That username is already taken.",
                code="USERNAME_TAKEN",
                details={"username": payload.username},
            )
        self.db.refresh(user)
        return self._token_response(user)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users.get_by_username(payload.username)
        # Verify even when the user is missing to reduce username enumeration
        # timing signals, then fail with a generic message.
        password_ok = (
            verify_password(payload.password, user.password_hash)
            if user is not None
            else verify_password(payload.password, _DUMMY_HASH)
        )
        if user is None or not password_ok:
            raise AuthError(
                "Invalid username or password.", code="INVALID_CREDENTIALS"
            )
        return self._token_response(user)

    def user_from_token(self, token: str) -> User:
        claims = decode_access_token(token)
        if not claims or "sub" not in claims:
            raise AuthError("Invalid or expired token.", code="INVALID_TOKEN")
        try:
            user_id = int(claims["sub"])
        except (TypeError, ValueError):
            raise AuthError("Invalid token subject.", code="INVALID_TOKEN")
        user = self.users.get(user_id)
        if user is None:
            raise AuthError("User no longer exists.", code="INVALID_TOKEN")
        return user

    # -- helpers -------------------------------------------------------------
    @staticmethod
    def _token_response(user: User) -> TokenResponse:
        token = create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )
