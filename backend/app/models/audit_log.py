import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stable task archive that survives deletion of users and trips."""

    __tablename__ = "audit_tasks"

    task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_type: Mapped[str] = mapped_column(String(64), default="trip_planning", index=True)
    title: Mapped[str] = mapped_column(String(255))
    destination_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="planning", index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    username_snapshot: Mapped[str] = mapped_column(String(64), index=True)
    email_snapshot: Mapped[str] = mapped_column(String(255), index=True)
    display_name_snapshot: Mapped[str | None] = mapped_column(String(128), nullable=True)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, unique=True, index=True
    )
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    generation_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    deletion_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delete_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditAction(UUIDPrimaryKeyMixin, Base):
    """Append-only, privacy-minimised operation record for one audit task."""

    __tablename__ = "audit_actions"
    __table_args__ = (
        Index("ix_audit_actions_task_occurred", "task_id", "occurred_at"),
        Index("ix_audit_actions_user_occurred", "user_id", "occurred_at"),
    )

    action_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("audit_tasks.task_id", ondelete="RESTRICT"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    username_snapshot: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(32), default="user")
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="success", index=True)
    before_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    after_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    error_message_safe: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    job_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AdminAuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "admin_audit_logs"

    admin_identity: Mapped[str] = mapped_column(String(255), index=True)
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    search_term_masked: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
