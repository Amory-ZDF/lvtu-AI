# ruff: noqa: E501
"""add extended tables"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260618_0002"
down_revision = "20260618_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # outfit_recommendations
    op.create_table(
        "outfit_recommendations",
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene", sa.String(length=128), nullable=False),
        sa.Column("season", sa.String(length=32), nullable=False),
        sa.Column("style", sa.String(length=64), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("tips", sa.Text(), nullable=True),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outfit_recommendations_trip_id"), "outfit_recommendations", ["trip_id"], unique=False)

    # photo_spot_recommendations
    op.create_table(
        "photo_spot_recommendations",
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_point_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("composition", sa.Text(), nullable=True),
        sa.Column("best_time", sa.String(length=128), nullable=True),
        sa.Column("photo_score", sa.Float(), nullable=True),
        sa.Column("tips", sa.Text(), nullable=True),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_point_id"], ["trip_points.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_photo_spot_recommendations_trip_id"), "photo_spot_recommendations", ["trip_id"], unique=False)
    op.create_index(
        op.f("ix_photo_spot_recommendations_trip_point_id"),
        "photo_spot_recommendations",
        ["trip_point_id"],
        unique=False,
    )

    # plan_variants
    op.create_table(
        "plan_variants",
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_name", sa.String(length=255), nullable=False),
        sa.Column("pace", sa.String(length=32), nullable=False),
        sa.Column("estimated_budget", sa.String(length=128), nullable=True),
        sa.Column("photo_score", sa.Float(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("itinerary_summary", sa.JSON(), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plan_variants_trip_id"), "plan_variants", ["trip_id"], unique=False)

    # destination_candidates
    op.create_table(
        "destination_candidates",
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country_or_region", sa.String(length=128), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("budget_range", sa.String(length=128), nullable=True),
        sa.Column("best_season", sa.String(length=255), nullable=True),
        sa.Column("vibe_tags", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("hero_image_url", sa.String(length=512), nullable=True),
        sa.Column("gallery", sa.JSON(), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_destination_candidates_session_id"),
        "destination_candidates",
        ["session_id"],
        unique=False,
    )

    # generation_jobs
    op.create_table(
        "generation_jobs",
        sa.Column("job_id", sa.String(length=128), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index(op.f("ix_generation_jobs_job_id"), "generation_jobs", ["job_id"], unique=True)
    op.create_index(op.f("ix_generation_jobs_job_type"), "generation_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_generation_jobs_status"), "generation_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_generation_jobs_user_id"), "generation_jobs", ["user_id"], unique=False)

    # trip_versions
    op.create_table(
        "trip_versions",
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trip_id", "version_number", name="uq_trip_versions_trip_id_version_number"),
    )
    op.create_index(op.f("ix_trip_versions_trip_id"), "trip_versions", ["trip_id"], unique=False)

    # collaborators
    op.create_table(
        "collaborators",
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("module_locks", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trip_id", "user_id", name="uq_collaborators_trip_id_user_id"),
    )
    op.create_index(op.f("ix_collaborators_trip_id"), "collaborators", ["trip_id"], unique=False)
    op.create_index(op.f("ix_collaborators_user_id"), "collaborators", ["user_id"], unique=False)

    # user_behaviors
    op.create_table(
        "user_behaviors",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_behaviors_user_id"), "user_behaviors", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_behaviors_event_type"), "user_behaviors", ["event_type"], unique=False)
    op.create_index(op.f("ix_user_behaviors_occurred_at"), "user_behaviors", ["occurred_at"], unique=False)

    # notifications
    op.create_table(
        "notifications",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("related_resource_type", sa.String(length=64), nullable=True),
        sa.Column("related_resource_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False)

    # media_assets
    op.create_table(
        "media_assets",
        sa.Column("asset_type", sa.String(length=64), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=512), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("alt", sa.String(length=255), nullable=True),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_resource_type", sa.String(length=64), nullable=True),
        sa.Column("related_resource_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_media_assets_asset_type"), "media_assets", ["asset_type"], unique=False)
    op.create_index(op.f("ix_media_assets_uploader_id"), "media_assets", ["uploader_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_media_assets_uploader_id"), table_name="media_assets")
    op.drop_index(op.f("ix_media_assets_asset_type"), table_name="media_assets")
    op.drop_table("media_assets")

    op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(op.f("ix_user_behaviors_occurred_at"), table_name="user_behaviors")
    op.drop_index(op.f("ix_user_behaviors_event_type"), table_name="user_behaviors")
    op.drop_index(op.f("ix_user_behaviors_user_id"), table_name="user_behaviors")
    op.drop_table("user_behaviors")

    op.drop_index(op.f("ix_collaborators_user_id"), table_name="collaborators")
    op.drop_index(op.f("ix_collaborators_trip_id"), table_name="collaborators")
    op.drop_table("collaborators")

    op.drop_index(op.f("ix_trip_versions_trip_id"), table_name="trip_versions")
    op.drop_table("trip_versions")

    op.drop_index(op.f("ix_generation_jobs_user_id"), table_name="generation_jobs")
    op.drop_index(op.f("ix_generation_jobs_status"), table_name="generation_jobs")
    op.drop_index(op.f("ix_generation_jobs_job_type"), table_name="generation_jobs")
    op.drop_index(op.f("ix_generation_jobs_job_id"), table_name="generation_jobs")
    op.drop_table("generation_jobs")

    op.drop_index(op.f("ix_destination_candidates_session_id"), table_name="destination_candidates")
    op.drop_table("destination_candidates")

    op.drop_index(op.f("ix_plan_variants_trip_id"), table_name="plan_variants")
    op.drop_table("plan_variants")

    op.drop_index(op.f("ix_photo_spot_recommendations_trip_point_id"), table_name="photo_spot_recommendations")
    op.drop_index(op.f("ix_photo_spot_recommendations_trip_id"), table_name="photo_spot_recommendations")
    op.drop_table("photo_spot_recommendations")

    op.drop_index(op.f("ix_outfit_recommendations_trip_id"), table_name="outfit_recommendations")
    op.drop_table("outfit_recommendations")
