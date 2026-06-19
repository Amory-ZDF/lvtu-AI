from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DestinationCandidate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "destination_candidates"

    session_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(255))
    country_or_region: Mapped[str] = mapped_column(String(128))
    match_score: Mapped[int] = mapped_column(Integer)
    budget_range: Mapped[str | None] = mapped_column(String(128), nullable=True)
    best_season: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vibe_tags: Mapped[list] = mapped_column(JSON, default=list)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    hero_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gallery: Mapped[list] = mapped_column(JSON, default=list)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
