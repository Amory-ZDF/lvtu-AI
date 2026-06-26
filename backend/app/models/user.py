from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text(), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    preference = relationship("UserPreference", back_populates="user", uselist=False)
    trips = relationship("Trip", back_populates="user")
    behaviors = relationship("UserBehavior", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    media_assets = relationship("MediaAsset", back_populates="uploader")
    collaborators = relationship("Collaborator", back_populates="user")
