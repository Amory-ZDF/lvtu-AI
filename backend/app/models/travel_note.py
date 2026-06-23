from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TravelNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """旅行笔记知识库表（采集自小红书等平台，供 RAG 检索和 AI 上下文增强）。"""

    __tablename__ = "travel_notes"

    title: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(32), default="xiaohongshu")
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    destination_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text())
    raw_content: Mapped[str | None] = mapped_column(Text(), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    season: Mapped[str | None] = mapped_column(String(32), nullable=True)
    budget_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    travel_style: Mapped[list] = mapped_column(JSON, default=list)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    images: Mapped[list] = mapped_column(JSON, default=list)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    collect_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    author_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    published_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
