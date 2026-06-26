# ruff: noqa: E501
"""add knowledge base tables (destinations, photo_spots, outfits)"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260620_0001"
down_revision = "20260618_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # destinations（知识库，区别于 destination_candidates）
    op.create_table(
        "destinations",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country_or_region", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("best_season", sa.String(length=255), nullable=True),
        sa.Column("budget_range", sa.String(length=128), nullable=True),
        sa.Column("vibe_tags", sa.JSON(), nullable=False),
        sa.Column("highlights", sa.JSON(), nullable=False),
        sa.Column("climate", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("currency", sa.String(length=64), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("hero_image_url", sa.String(length=512), nullable=True),
        sa.Column("gallery", sa.JSON(), nullable=False),
        sa.Column("average_days", sa.Integer(), nullable=True),
        sa.Column("popularity", sa.Integer(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_destinations_name"), "destinations", ["name"], unique=False)
    op.create_index(op.f("ix_destinations_country_or_region"), "destinations", ["country_or_region"], unique=False)

    # photo_spots（知识库，区别于 photo_spot_recommendations）
    op.create_table(
        "photo_spots",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("destination_name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("composition", sa.Text(), nullable=True),
        sa.Column("best_time", sa.String(length=128), nullable=True),
        sa.Column("best_season", sa.String(length=255), nullable=True),
        sa.Column("photo_score", sa.Float(), nullable=True),
        sa.Column("tips", sa.Text(), nullable=True),
        sa.Column("equipment", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_photo_spots_name"), "photo_spots", ["name"], unique=False)
    op.create_index(op.f("ix_photo_spots_destination_name"), "photo_spots", ["destination_name"], unique=False)

    # outfits（知识库，区别于 outfit_recommendations）
    op.create_table(
        "outfits",
        sa.Column("destination_name", sa.String(length=255), nullable=True),
        sa.Column("season", sa.String(length=32), nullable=False),
        sa.Column("scene", sa.String(length=128), nullable=False),
        sa.Column("style", sa.String(length=64), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("tips", sa.Text(), nullable=True),
        sa.Column("weather_note", sa.String(length=255), nullable=True),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outfits_destination_name"), "outfits", ["destination_name"], unique=False)
    op.create_index(op.f("ix_outfits_season"), "outfits", ["season"], unique=False)
    op.create_index(op.f("ix_outfits_scene"), "outfits", ["scene"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_outfits_scene"), table_name="outfits")
    op.drop_index(op.f("ix_outfits_season"), table_name="outfits")
    op.drop_index(op.f("ix_outfits_destination_name"), table_name="outfits")
    op.drop_table("outfits")

    op.drop_index(op.f("ix_photo_spots_destination_name"), table_name="photo_spots")
    op.drop_index(op.f("ix_photo_spots_name"), table_name="photo_spots")
    op.drop_table("photo_spots")

    op.drop_index(op.f("ix_destinations_country_or_region"), table_name="destinations")
    op.drop_index(op.f("ix_destinations_name"), table_name="destinations")
    op.drop_table("destinations")
