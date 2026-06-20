from sqlalchemy import JSON, Float, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PhotoSpot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """机位知识库表（持久化，区别于 photo_spot_recommendations 推荐结果缓存）。"""

    __tablename__ = "photo_spots"

    name: Mapped[str] = mapped_column(String(255), index=True)
    destination_name: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    composition: Mapped[str | None] = mapped_column(Text(), nullable=True)
    best_time: Mapped[str | None] = mapped_column(String(128), nullable=True)
    best_season: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tips: Mapped[str | None] = mapped_column(Text(), nullable=True)
    equipment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    images: Mapped[list] = mapped_column(JSON, default=list)
