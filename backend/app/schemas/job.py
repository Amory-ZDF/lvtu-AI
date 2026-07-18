from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.domain import ORMModel


class JobRead(ORMModel):
    job_id: str
    job_type: str
    status: str
    progress: int
    user_id: UUID | None = None
    input_data: dict
    output_data: dict | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobCreateRequest(BaseModel):
    job_type: str
    input_data: dict = Field(default_factory=dict)


class AdjustmentRequest(BaseModel):
    instruction: str = Field(min_length=2, max_length=1000)
    target_day_id: UUID | None = None
