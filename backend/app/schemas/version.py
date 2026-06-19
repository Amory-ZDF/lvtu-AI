from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TripVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    version_number: int
    snapshot: dict[str, Any]
    created_by: UUID | None
    note: str | None
    created_at: datetime


class TripVersionRestoreResponse(BaseModel):
    trip_id: UUID
    version_number: int
    restored_at: datetime
