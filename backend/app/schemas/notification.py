from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: str
    title: str
    content: str | None
    is_read: bool
    related_resource_type: str | None
    related_resource_id: str | None
    created_at: datetime


class NotificationCreate(BaseModel):
    user_id: UUID
    type: str
    title: str
    content: str | None = None
    related_resource_type: str | None = None
    related_resource_id: str | None = None
