from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Outfit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """穿搭知识库表（持久化，区别于 outfit_recommendations 推荐结果缓存）。"""

    __tablename__ = "outfits"

    destination_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    season: Mapped[str] = mapped_column(String(32), index=True)
    scene: Mapped[str] = mapped_column(String(128), index=True)
    style: Mapped[str] = mapped_column(String(64))
    items: Mapped[list] = mapped_column(JSON, default=list)
    tips: Mapped[str | None] = mapped_column(Text(), nullable=True)
    weather_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    images: Mapped[list] = mapped_column(JSON, default=list)
