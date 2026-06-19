from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.responses import success_response
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db_session
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import AuthResponse, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.common import ApiResponse
from app.schemas.domain import UserProfileRead

router = APIRouter()
settings = get_settings()

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _load_user_profile(db: Session, user_id: UUID) -> User:
    user = db.scalar(select(User).options(selectinload(User.preference)).where(User.id == user_id))
    if user is None:
        raise AppException(status_code=404, code="user_not_found", message="用户不存在")
    return user


def _build_token_response(user_id: UUID) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post(
    "/register",
    response_model=ApiResponse[AuthResponse],
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    request: Request,
    db: SessionDep,
) -> ApiResponse[AuthResponse]:
    existing = db.scalar(
        select(User).where((User.email == payload.email) | (User.username == payload.username))
    )
    if existing is not None:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="user_already_exists",
            message="邮箱或用户名已被注册",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="user_already_exists",
            message="邮箱或用户名已被注册",
        ) from exc
    db.refresh(user)

    user = _load_user_profile(db, user.id)
    data = AuthResponse(
        token=_build_token_response(user.id),
        user=UserProfileRead.model_validate(user),
    )
    return success_response(data, request)


@router.post("/login", response_model=ApiResponse[AuthResponse])
def login(
    request: Request,
    db: SessionDep,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> ApiResponse[AuthResponse]:
    # OAuth2PasswordRequestForm uses `username` field; we treat it as email.
    email = form.username
    password = form.password

    user = db.scalar(
        select(User).options(selectinload(User.preference)).where(User.email == email)
    )
    if (
        user is None
        or user.password_hash is None
        or not verify_password(password, user.password_hash)
    ):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_credentials",
            message="邮箱或密码错误",
        )

    data = AuthResponse(
        token=_build_token_response(user.id),
        user=UserProfileRead.model_validate(user),
    )
    return success_response(data, request)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh(
    payload: RefreshRequest,
    request: Request,
    db: SessionDep,
) -> ApiResponse[TokenResponse]:
    try:
        token_payload = decode_token(payload.refresh_token)
    except jwt.PyJWTError as exc:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
            message="无效的刷新令牌",
        ) from exc

    if token_payload.get("type") != "refresh":
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
            message="无效的刷新令牌",
        )

    user_id_raw = token_payload.get("sub")
    if not user_id_raw:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
            message="无效的刷新令牌",
        )

    try:
        user_id = UUID(user_id_raw)
    except (ValueError, AttributeError) as exc:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
            message="无效的刷新令牌",
        ) from exc

    user = db.get(User, user_id)
    if user is None:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
            message="无效的刷新令牌",
        )

    data = TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
    return success_response(data, request)


@router.get("/me", response_model=ApiResponse[UserProfileRead])
def me(request: Request, current_user: CurrentUser, db: SessionDep) -> ApiResponse[UserProfileRead]:
    user = _load_user_profile(db, current_user.id)
    return success_response(UserProfileRead.model_validate(user), request)
