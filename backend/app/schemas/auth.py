from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.domain import UserProfileRead

_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterRequest(BaseModel):
    email: str = Field(pattern=_EMAIL_PATTERN, max_length=255)
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(pattern=_EMAIL_PATTERN, max_length=255)
    password: str


class DataCenterLoginRequest(BaseModel):
    email: str = Field(pattern=_EMAIL_PATTERN, max_length=255)


class DataCenterAdminCreate(BaseModel):
    email: str = Field(pattern=_EMAIL_PATTERN, max_length=255)
    display_name: str | None = Field(default=None, max_length=128)


class DataCenterAdminRead(BaseModel):
    email: str
    display_name: str | None = None
    source: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    display_name: str
    avatar_url: str | None = None
    bio: str | None = None
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    token: TokenResponse
    user: UserProfileRead


class RefreshRequest(BaseModel):
    refresh_token: str
