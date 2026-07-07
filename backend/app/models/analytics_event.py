import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AnalyticsEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_events"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    visitor_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    event_name: Mapped[str] = mapped_column(String(64), index=True)
    event_category: Mapped[str] = mapped_column(String(32), index=True)
    page_path: Mapped[str] = mapped_column(String(512), index=True)
    page_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(512), nullable=True)
    element_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    element_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    element_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    viewport_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    viewport_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    user = relationship("User")
