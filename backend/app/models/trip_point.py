import uuid
from datetime import time
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TripPoint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_points"
    __table_args__ = (
        UniqueConstraint("trip_day_id", "sort_order", name="uq_trip_points_trip_day_id_sort_order"),
    )

    trip_day_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trip_days.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    point_type: Mapped[str] = mapped_column(String(64), default="spot")
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time(), nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time(), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    trip_day = relationship("TripDay", back_populates="points")
    photo_spot_recommendations = relationship(
        "PhotoSpotRecommendation", back_populates="trip_point"
    )
