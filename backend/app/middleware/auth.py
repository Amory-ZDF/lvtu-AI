from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import decode_token
from app.db.session import get_db_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _resolve_user_from_token(token: str, db: Session) -> User:
    """Decode the token and return the matching User, or raise AppException(401)."""
    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise AppException(status_code=401, code="unauthorized", message="无效的认证凭据") from exc

    if payload.get("type") != "access":
        raise AppException(status_code=401, code="unauthorized", message="无效的认证凭据")

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise AppException(status_code=401, code="unauthorized", message="无效的认证凭据")

    try:
        user_id = UUID(user_id_raw)
    except (ValueError, AttributeError) as exc:
        raise AppException(status_code=401, code="unauthorized", message="无效的认证凭据") from exc

    user = db.get(User, user_id)
    if user is None:
        raise AppException(status_code=401, code="unauthorized", message="无效的认证凭据")

    return user


TokenDep = Annotated[str | None, Depends(oauth2_scheme)]
DbSessionDep = Annotated[Session, Depends(get_db_session)]


def get_current_user(token: TokenDep, db: DbSessionDep) -> User:
    """Resolve the current user from the Authorization Bearer token."""
    if token is None:
        raise AppException(status_code=401, code="unauthorized", message="无效的认证凭据")

    return _resolve_user_from_token(token, db)


def get_current_user_optional(token: TokenDep, db: DbSessionDep) -> User | None:
    """Optional auth dependency. Returns None when no token is provided.

    Used for gradual migration of existing routes that previously had no auth.
    If a token is provided but invalid, an AppException(401) is raised so that
    clients sending bad tokens get a clear error rather than silently anonymous.
    """
    if token is None:
        return None

    return _resolve_user_from_token(token, db)


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the current user is active. Currently all users are considered active."""
    return current_user
