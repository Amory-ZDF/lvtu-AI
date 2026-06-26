from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from datetime import time as time_type
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserPreferenceRead(ORMModel):
    id: UUID
    user_id: UUID
    departure_city: str | None
    preferred_styles: list[str] = Field(default_factory=list)
    budget_level: str | None
    language: str | None
    timezone: str | None
    created_at: datetime
    updated_at: datetime


class UserProfileUpsert(BaseModel):
    email: str
    username: str
    display_name: str
    avatar_url: str | None = None
    bio: str | None = None
    departure_city: str | None = None
    preferred_styles: list[str] = Field(default_factory=list)
    budget_level: str | None = None
    language: str | None = None
    timezone: str | None = None


class UserProfileRead(ORMModel):
    id: UUID
    email: str
    username: str
    display_name: str
    avatar_url: str | None
    bio: str | None
    created_at: datetime
    updated_at: datetime
    preference: UserPreferenceRead | None = None


class TripCreate(BaseModel):
    title: str
    destination_name: str
    start_date: date_type | None = None
    end_date: date_type | None = None
    status: str = "draft"
    cover_image_url: str | None = None
    notes: str | None = None


class TripUpdate(BaseModel):
    title: str | None = None
    destination_name: str | None = None
    start_date: date_type | None = None
    end_date: date_type | None = None
    status: str | None = None
    cover_image_url: str | None = None
    notes: str | None = None


class TripRead(ORMModel):
    id: UUID
    user_id: UUID
    title: str
    destination_name: str
    start_date: date_type | None
    end_date: date_type | None
    status: str
    cover_image_url: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class TripDayCreate(BaseModel):
    day_index: int | None = None
    date: date_type | None = None
    title: str | None = None
    summary: str | None = None


class TripDayUpdate(BaseModel):
    day_index: int | None = None
    date: date_type | None = None
    title: str | None = None
    summary: str | None = None


class TripDayRead(ORMModel):
    id: UUID
    trip_id: UUID
    day_index: int
    date: date_type | None
    title: str | None
    summary: str | None
    created_at: datetime
    updated_at: datetime


class TripPointCreate(BaseModel):
    name: str
    point_type: str = "spot"
    address: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    start_time: time_type | None = None
    end_time: time_type | None = None
    sort_order: int | None = None
    notes: str | None = None
    image_url: str | None = None


class TripPointUpdate(BaseModel):
    name: str | None = None
    point_type: str | None = None
    address: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    start_time: time_type | None = None
    end_time: time_type | None = None
    sort_order: int | None = None
    notes: str | None = None
    image_url: str | None = None


class TripPointRead(ORMModel):
    id: UUID
    trip_day_id: UUID
    name: str
    point_type: str
    address: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    start_time: time_type | None
    end_time: time_type | None
    sort_order: int
    notes: str | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime


class SortOrderUpdate(BaseModel):
    ordered_ids: list[UUID] = Field(default_factory=list)


class PackingItemCreate(BaseModel):
    name: str
    category: str | None = None
    quantity: int = 1
    is_checked: bool = False
    note: str | None = None


class PackingItemUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    quantity: int | None = None
    is_checked: bool | None = None
    note: str | None = None


class PackingItemCheckUpdate(BaseModel):
    is_checked: bool


class PackingItemRead(ORMModel):
    id: UUID
    trip_id: UUID
    name: str
    category: str | None
    quantity: int
    is_checked: bool
    note: str | None
    created_at: datetime
    updated_at: datetime

