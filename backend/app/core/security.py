from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _create_token(
    user_id: UUID,
    token_type: str,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "exp": now + expires_delta,
        "iat": now,
        "type": token_type,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token for the given user."""
    delta = expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return _create_token(user_id, "access", delta)


def create_refresh_token(user_id: UUID) -> str:
    """Create a JWT refresh token for the given user."""
    delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    return _create_token(user_id, "refresh", delta)


def decode_token(token: str) -> dict:
    """Decode a JWT token and return its payload.

    Raises jwt.PyJWTError (or subclass) when the token is invalid or expired.
    """
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
