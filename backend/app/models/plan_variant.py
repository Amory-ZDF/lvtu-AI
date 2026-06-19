import uuid

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PlanVariant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plan_variants"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        index=True,
    )
    variant_name: Mapped[str] = mapped_column(String(255))
    pace: Mapped[str] = mapped_column(String(32))
    estimated_budget: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    itinerary_summary: Mapped[list] = mapped_column(JSON, default=list)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    trip = relationship("Trip", back_populates="plan_variants")
