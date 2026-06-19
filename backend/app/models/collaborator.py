import uuid

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Collaborator(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "collaborators"
    __table_args__ = (
        UniqueConstraint("trip_id", "user_id", name="uq_collaborators_trip_id_user_id"),
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), default="viewer")
    module_locks: Mapped[dict] = mapped_column(JSON, default=dict)

    trip = relationship("Trip", back_populates="collaborators")
    user = relationship("User", back_populates="collaborators")
