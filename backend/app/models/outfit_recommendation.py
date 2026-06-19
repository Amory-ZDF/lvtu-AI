import uuid

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OutfitRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "outfit_recommendations"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        index=True,
    )
    scene: Mapped[str] = mapped_column(String(128))
    season: Mapped[str] = mapped_column(String(32))
    style: Mapped[str] = mapped_column(String(64))
    items: Mapped[list] = mapped_column(JSON, default=list)
    tips: Mapped[str | None] = mapped_column(Text(), nullable=True)
    images: Mapped[list] = mapped_column(JSON, default=list)

    trip = relationship("Trip", back_populates="outfit_recommendations")
