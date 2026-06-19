from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LikeResponse(BaseModel):
    post_id: UUID
    user_id: UUID
    like_count: int
    liked: bool


class CommentCreate(BaseModel):
    post_id: UUID
    user_id: UUID
    content: str


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    user_id: UUID
    content: str
    created_at: datetime


class FavoriteResponse(BaseModel):
    post_id: UUID
    user_id: UUID
    favorited: bool
