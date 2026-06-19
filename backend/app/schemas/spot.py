from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.domain import ORMModel


class PhotoSpotRecommendationCreate(BaseModel):
    trip_id: UUID | None = None
    trip_point_id: UUID | None = None
    name: str
    location: str
    composition: str | None = None
    best_time: str | None = None
    photo_score: float | None = None
    tips: str | None = None
    images: list[str] = Field(default_factory=list)


class PhotoSpotRecommendationUpdate(BaseModel):
    trip_point_id: UUID | None = None
    name: str | None = None
    location: str | None = None
    composition: str | None = None
    best_time: str | None = None
    photo_score: float | None = None
    tips: str | None = None
    images: list[str] | None = None


class PhotoSpotRecommendationRead(ORMModel):
    id: UUID
    trip_id: UUID
    trip_point_id: UUID | None
    name: str
    location: str
    composition: str | None
    best_time: str | None
    photo_score: float | None
    tips: str | None
    images: list[str]
    created_at: datetime
    updated_at: datetime
