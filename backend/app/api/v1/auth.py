from __future__ import annotations

import re
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.responses import success_response
from app.core.config import Settings, get_settings
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
from app.schemas.auth import (
    AuthResponse,
    DataCenterAdminCreate,
    DataCenterAdminRead,
    DataCenterLoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import ApiResponse
from app.schemas.domain import UserProfileRead
from app.services.analytics_admin_service import (
    add_analytics_admin,
    ensure_analytics_admin,
    has_any_analytics_admin,
    is_analytics_admin_email,
    list_analytics_admins,
)

router = APIRouter()
settings = get_settings()

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


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


def _authenticate_user(db: Session, email: str, password: str) -> User:
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
    return user


def _normalise_email(email: str) -> str:
    return email.strip().lower()


def _default_username(email: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]+", "_", email.split("@", 1)[0]).strip("_")
    return base[:48] or "analytics_admin"


def _unique_username(db: Session, email: str) -> str:
    base = _default_username(email)
    username = base
    index = 2
    while db.scalar(select(User).where(User.username == username, User.email != email)):
        username = f"{base}_{index}"
        index += 1
    return username


def _get_or_create_data_center_user(db: Session, email: str) -> User:
    normalised = _normalise_email(email)
    user = db.scalar(
        select(User).options(selectinload(User.preference)).where(User.email == normalised)
    )
    if user is not None:
        return user

    user = User(
        email=normalised,
        username=_unique_username(db, normalised),
        display_name=normalised.split("@", 1)[0],
        password_hash=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _load_user_profile(db, user.id)


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
    user = _authenticate_user(db, form.username, form.password)

    data = AuthResponse(
        token=_build_token_response(user.id),
        user=UserProfileRead.model_validate(user),
    )
    return success_response(data, request)


@router.post("/data-center/login", response_model=ApiResponse[AuthResponse])
def data_center_login(
    payload: DataCenterLoginRequest,
    request: Request,
    db: SessionDep,
    settings: SettingsDep,
) -> ApiResponse[AuthResponse]:
    email = _normalise_email(payload.email)
    if not has_any_analytics_admin(settings, db):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="analytics_admin_not_configured",
            message="数据中台白名单未配置，请先添加白名单账号",
        )

    if not is_analytics_admin_email(email, settings, db):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="analytics_forbidden",
            message="当前邮箱不在数据中台白名单中",
        )

    user = _get_or_create_data_center_user(db, email)

    data = AuthResponse(
        token=_build_token_response(user.id),
        user=UserProfileRead.model_validate(user),
    )
    return success_response(data, request)


@router.get("/data-center/admins", response_model=ApiResponse[list[DataCenterAdminRead]])
def list_data_center_admins(
    request: Request,
    db: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUser,
) -> ApiResponse[list[DataCenterAdminRead]]:
    ensure_analytics_admin(current_user, settings, db)
    admins = [
        DataCenterAdminRead(**item)
        for item in list_analytics_admins(settings, db)
    ]
    return success_response(admins, request)


@router.post("/data-center/admins", response_model=ApiResponse[DataCenterAdminRead])
def create_data_center_admin(
    payload: DataCenterAdminCreate,
    request: Request,
    db: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUser,
) -> ApiResponse[DataCenterAdminRead]:
    ensure_analytics_admin(current_user, settings, db)
    admin = add_analytics_admin(db, payload.email, payload.display_name)
    data = DataCenterAdminRead(
        email=admin.email,
        display_name=admin.display_name,
        source="database",
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
