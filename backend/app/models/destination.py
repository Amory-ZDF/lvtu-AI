from sqlalchemy import JSON, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Destination(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """目的地知识库表（持久化，区别于 destination_candidates 推荐结果缓存）。"""

    __tablename__ = "destinations"

    name: Mapped[str] = mapped_column(String(255), index=True)
    country_or_region: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    best_season: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget_range: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vibe_tags: Mapped[list] = mapped_column(JSON, default=list)
    highlights: Mapped[list] = mapped_column(JSON, default=list)
    climate: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    hero_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gallery: Mapped[list] = mapped_column(JSON, default=list)
    average_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    popularity: Mapped[int] = mapped_column(Integer, default=0)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
