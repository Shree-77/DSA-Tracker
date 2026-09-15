"""Authentication schemas (register/login requests and responses)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCredentials(BaseModel):
    """Shared shape for register/login requests."""

    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def _normalise_username(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Username must not be blank.")
        if any(c.isspace() for c in cleaned):
            raise ValueError("Username must not contain spaces.")
        return cleaned


class RegisterRequest(UserCredentials):
    pass


class LoginRequest(UserCredentials):
    pass


class UserResponse(BaseModel):
    """Public representation of a user (never exposes the password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    """Returned on successful register/login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
