import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    related_resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    user = relationship("User", back_populates="notifications")
