"""add task audit archive and trip soft deletion

Revision ID: 20260722_0001
Revises: 20260708_0001
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260722_0001"
down_revision = "20260708_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("trips", sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("trips", sa.Column("deletion_reason", sa.String(length=255), nullable=True))
    op.create_index("ix_trips_deleted_at", "trips", ["deleted_at"])

    op.create_table(
        "audit_tasks",
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("destination_summary", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("username_snapshot", sa.String(64), nullable=False),
        sa.Column("email_snapshot", sa.String(255), nullable=False),
        sa.Column("display_name_snapshot", sa.String(128), nullable=True),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deletion_reason", sa.String(255), nullable=True),
        sa.Column("delete_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
        sa.UniqueConstraint("trip_id"),
    )
    for column in (
        "task_id",
        "task_type",
        "status",
        "user_id",
        "username_snapshot",
        "email_snapshot",
        "trip_id",
    ):
        op.create_index(f"ix_audit_tasks_{column}", "audit_tasks", [column])

    op.create_table(
        "audit_actions",
        sa.Column("action_id", sa.String(64), nullable=False),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("username_snapshot", sa.String(64), nullable=True),
        sa.Column("email_snapshot", sa.String(255), nullable=True),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=True),
        sa.Column("target_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("before_summary", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("after_summary", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message_safe", sa.Text(), nullable=True),
        sa.Column("query_id", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("job_id", sa.String(128), nullable=True),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["audit_tasks.task_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("action_id"),
    )
    for column in (
        "action_id",
        "task_id",
        "user_id",
        "action_type",
        "status",
        "error_code",
        "query_id",
        "request_id",
        "job_id",
        "trace_id",
        "occurred_at",
    ):
        op.create_index(f"ix_audit_actions_{column}", "audit_actions", [column])
    op.create_index("ix_audit_actions_task_occurred", "audit_actions", ["task_id", "occurred_at"])
    op.create_index("ix_audit_actions_user_occurred", "audit_actions", ["user_id", "occurred_at"])

    op.create_table(
        "admin_audit_logs",
        sa.Column("admin_identity", sa.String(255), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("search_term_masked", sa.String(255), nullable=True),
        sa.Column("target_task_id", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("admin_identity", "action_type", "target_task_id", "occurred_at"):
        op.create_index(f"ix_admin_audit_logs_{column}", "admin_audit_logs", [column])


def downgrade() -> None:
    op.drop_table("admin_audit_logs")
    op.drop_table("audit_actions")
    op.drop_table("audit_tasks")
    op.drop_index("ix_trips_deleted_at", table_name="trips")
    op.drop_column("trips", "deletion_reason")
    op.drop_column("trips", "deleted_by")
    op.drop_column("trips", "deleted_at")
