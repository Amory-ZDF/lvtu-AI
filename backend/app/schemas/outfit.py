from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.domain import ORMModel


class OutfitRecommendationCreate(BaseModel):
    trip_id: UUID | None = None
    scene: str
    season: str
    style: str
    items: list[dict] = Field(default_factory=list)
    tips: str | None = None
    images: list[str] = Field(default_factory=list)


class OutfitRecommendationUpdate(BaseModel):
    scene: str | None = None
    season: str | None = None
    style: str | None = None
    items: list[dict] | None = None
    tips: str | None = None
    images: list[str] | None = None


class OutfitPreviewImageRequest(BaseModel):
    force: bool = False


class OutfitRecommendationRead(ORMModel):
    id: UUID
    trip_id: UUID
    scene: str
    season: str
    style: str
    items: list[dict]
    tips: str | None
    images: list[str]
    created_at: datetime
    updated_at: datetime


class OutfitPreviewImageRead(BaseModel):
    outfit: OutfitRecommendationRead
    image_url: str | None = None
    provider: str
    generated: bool
    message: str | None = None
