from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppException
from app.models.analytics_admin import AnalyticsAdmin
from app.models.user import User


def _normalise_email(email: str) -> str:
    return email.strip().lower()


def _allowed_admin_emails(settings: Settings) -> set[str]:
    return {_normalise_email(email) for email in settings.analytics_admin_emails if email.strip()}


def is_analytics_admin_email(email: str, settings: Settings, db: Session) -> bool:
    normalised = _normalise_email(email)
    if normalised in _allowed_admin_emails(settings):
        return True

    return (
        db.scalar(
            select(AnalyticsAdmin).where(
                AnalyticsAdmin.email == normalised,
                AnalyticsAdmin.is_active.is_(True),
            )
        )
        is not None
    )


def has_any_analytics_admin(settings: Settings, db: Session) -> bool:
    if _allowed_admin_emails(settings):
        return True
    return (
        db.scalar(select(AnalyticsAdmin.id).where(AnalyticsAdmin.is_active.is_(True)))
        is not None
    )


def ensure_analytics_admin(user: User, settings: Settings, db: Session) -> None:
    allowed_emails = _allowed_admin_emails(settings)
    if not allowed_emails and not has_any_analytics_admin(settings, db):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="analytics_admin_not_configured",
            message="数据中台白名单未配置，请先从后端添加白名单账号",
        )

    if not is_analytics_admin_email(user.email, settings, db):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="analytics_forbidden",
            message="当前账号不在数据中台白名单中",
        )


def list_analytics_admins(settings: Settings, db: Session) -> list[dict[str, str | None]]:
    seen: set[str] = set()
    items: list[dict[str, str | None]] = []

    for email in sorted(_allowed_admin_emails(settings)):
        seen.add(email)
        items.append({"email": email, "display_name": None, "source": "env"})

    rows = db.scalars(
        select(AnalyticsAdmin)
        .where(AnalyticsAdmin.is_active.is_(True))
        .order_by(AnalyticsAdmin.created_at.asc())
    )
    for row in rows:
        email = _normalise_email(row.email)
        if email in seen:
            continue
        items.append(
            {
                "email": email,
                "display_name": row.display_name,
                "source": "database",
            }
        )
    return items


def add_analytics_admin(db: Session, email: str, display_name: str | None = None) -> AnalyticsAdmin:
    normalised = _normalise_email(email)
    admin = db.scalar(select(AnalyticsAdmin).where(AnalyticsAdmin.email == normalised))
    if admin is None:
        admin = AnalyticsAdmin(email=normalised, display_name=display_name, is_active=True)
        db.add(admin)
    else:
        admin.is_active = True
        if display_name is not None:
            admin.display_name = display_name
    db.commit()
    db.refresh(admin)
    return admin
