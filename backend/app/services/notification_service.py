from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: UUID,
    type: str,
    title: str,
    content: str | None = None,
    related_resource_type: str | None = None,
    related_resource_id: str | None = None,
) -> Notification:
    """Create a notification for the given user."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        related_resource_type=related_resource_type,
        related_resource_id=related_resource_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_notifications(
    db: Session,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
) -> tuple[list[Notification], int]:
    """Return (notifications, total) for the given user, paginated."""
    base_filter = Notification.user_id == user_id
    count_stmt = select(func.count()).select_from(Notification).where(base_filter)
    list_stmt = select(Notification).where(base_filter)

    if unread_only:
        unread_filter = Notification.is_read.is_(False)
        count_stmt = count_stmt.where(unread_filter)
        list_stmt = list_stmt.where(unread_filter)

    total = db.scalar(count_stmt) or 0
    list_stmt = (
        list_stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    notifications = list(db.scalars(list_stmt))
    return notifications, total


def mark_as_read(db: Session, notification_id: UUID, user_id: UUID) -> Notification:
    """Mark a single notification as read. Raises 404 if not found or not owned."""
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    if notification is None:
        raise AppException(
            status_code=404,
            code=ErrorCode.NOT_FOUND,
            message="通知不存在",
        )
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(db: Session, user_id: UUID) -> int:
    """Mark all unread notifications as read for the given user. Returns count updated."""
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return result.rowcount or 0


def get_unread_count(db: Session, user_id: UUID) -> int:
    """Return the number of unread notifications for the given user."""
    return (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        or 0
    )
