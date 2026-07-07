# ruff: noqa: E501
"""add analytics events table"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260707_0001"
down_revision = "20260621_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_events",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("visitor_id", sa.String(length=128), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("event_name", sa.String(length=64), nullable=False),
        sa.Column("event_category", sa.String(length=32), nullable=False),
        sa.Column("page_path", sa.String(length=512), nullable=False),
        sa.Column("page_title", sa.String(length=255), nullable=True),
        sa.Column("referrer", sa.String(length=512), nullable=True),
        sa.Column("element_text", sa.String(length=255), nullable=True),
        sa.Column("element_role", sa.String(length=64), nullable=True),
        sa.Column("element_id", sa.String(length=128), nullable=True),
        sa.Column("target_url", sa.String(length=512), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("viewport_width", sa.Integer(), nullable=True),
        sa.Column("viewport_height", sa.Integer(), nullable=True),
        sa.Column("device_type", sa.String(length=32), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analytics_events_user_id"), "analytics_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_analytics_events_visitor_id"), "analytics_events", ["visitor_id"], unique=False)
    op.create_index(op.f("ix_analytics_events_session_id"), "analytics_events", ["session_id"], unique=False)
    op.create_index(op.f("ix_analytics_events_event_name"), "analytics_events", ["event_name"], unique=False)
    op.create_index(op.f("ix_analytics_events_event_category"), "analytics_events", ["event_category"], unique=False)
    op.create_index(op.f("ix_analytics_events_page_path"), "analytics_events", ["page_path"], unique=False)
    op.create_index(op.f("ix_analytics_events_device_type"), "analytics_events", ["device_type"], unique=False)
    op.create_index(op.f("ix_analytics_events_occurred_at"), "analytics_events", ["occurred_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analytics_events_occurred_at"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_device_type"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_page_path"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_event_category"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_event_name"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_session_id"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_visitor_id"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_user_id"), table_name="analytics_events")
    op.drop_table("analytics_events")
