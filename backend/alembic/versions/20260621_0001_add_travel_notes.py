# ruff: noqa: E501
"""add travel_notes table for crawled xiaohongshu content"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260621_0001"
down_revision = "20260620_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "travel_notes",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("destination_name", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("season", sa.String(length=32), nullable=True),
        sa.Column("budget_level", sa.String(length=32), nullable=True),
        sa.Column("travel_style", sa.JSON(), nullable=False),
        sa.Column("cover_image_url", sa.String(length=512), nullable=True),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False),
        sa.Column("collect_count", sa.Integer(), nullable=False),
        sa.Column("comment_count", sa.Integer(), nullable=False),
        sa.Column("author_name", sa.String(length=128), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_travel_notes_title"), "travel_notes", ["title"], unique=False)
    op.create_index(op.f("ix_travel_notes_source_id"), "travel_notes", ["source_id"], unique=False)
    op.create_index(op.f("ix_travel_notes_destination_name"), "travel_notes", ["destination_name"], unique=False)
    op.create_index(op.f("ix_travel_notes_category"), "travel_notes", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_travel_notes_category"), table_name="travel_notes")
    op.drop_index(op.f("ix_travel_notes_destination_name"), table_name="travel_notes")
    op.drop_index(op.f("ix_travel_notes_source_id"), table_name="travel_notes")
    op.drop_index(op.f("ix_travel_notes_title"), table_name="travel_notes")
    op.drop_table("travel_notes")
