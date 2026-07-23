import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Trip(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trips"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), index=True)
    destination_name: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="upcoming")
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    deletion_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user = relationship("User", back_populates="trips")
    days = relationship("TripDay", back_populates="trip")
    packing_items = relationship("PackingItem", back_populates="trip")
    outfit_recommendations = relationship("OutfitRecommendation", back_populates="trip")
    photo_spot_recommendations = relationship("PhotoSpotRecommendation", back_populates="trip")
    plan_variants = relationship("PlanVariant", back_populates="trip")
    trip_versions = relationship("TripVersion", back_populates="trip")
    collaborators = relationship("Collaborator", back_populates="trip")
