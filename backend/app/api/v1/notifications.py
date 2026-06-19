from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.responses import paginated_response, success_response
from app.db.session import get_db_session
from app.middleware.auth import get_current_user_optional
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.notification import NotificationRead
from app.services.notification_service import (
    get_unread_count,
    list_notifications,
    mark_all_as_read,
    mark_as_read,
)

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]


@router.get("", tags=["notifications"])
def list_user_notifications(
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    user_id: UUID = Query(..., description="用户 ID"),
    unread_only: bool = Query(default=False, description="仅返回未读通知"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    notifications, total = list_notifications(
        db, user_id, page=page, page_size=page_size, unread_only=unread_only
    )
    items = [NotificationRead.model_validate(n).model_dump(mode="json") for n in notifications]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)


@router.patch("/{notification_id}/read", tags=["notifications"])
def mark_notification_read(
    notification_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    user_id: UUID = Query(..., description="用户 ID"),
) -> ApiResponse:
    notification = mark_as_read(db, notification_id, user_id)
    return success_response(
        NotificationRead.model_validate(notification).model_dump(mode="json"),
        request,
    )


@router.post("/read-all", tags=["notifications"])
def mark_all_notifications_read(
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    user_id: UUID = Query(..., description="用户 ID"),
) -> ApiResponse:
    updated_count = mark_all_as_read(db, user_id)
    return success_response(
        {"user_id": str(user_id), "updated_count": updated_count},
        request,
    )


@router.get("/unread-count", tags=["notifications"])
def get_unread_notification_count(
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    user_id: UUID = Query(..., description="用户 ID"),
) -> ApiResponse:
    count = get_unread_count(db, user_id)
    return success_response(
        {"user_id": str(user_id), "unread_count": count},
        request,
    )
