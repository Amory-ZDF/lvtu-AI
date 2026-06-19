import uuid

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PhotoSpotRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "photo_spot_recommendations"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        index=True,
    )
    trip_point_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_points.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    composition: Mapped[str | None] = mapped_column(Text(), nullable=True)
    best_time: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tips: Mapped[str | None] = mapped_column(Text(), nullable=True)
    images: Mapped[list] = mapped_column(JSON, default=list)

    trip = relationship("Trip", back_populates="photo_spot_recommendations")
    trip_point = relationship("TripPoint", back_populates="photo_spot_recommendations")
