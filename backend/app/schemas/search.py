from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    keyword: str = Field(min_length=1)
    type: Literal["destination", "spot", "all"] = "all"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResultItem(BaseModel):
    type: Literal["destination", "spot"]
    id: UUID
    title: str
    snippet: str | None = None
    image_url: str | None = None


class SearchResponse(BaseModel):
    items: list[SearchResultItem] = Field(default_factory=list)
    page: int
    page_size: int
    total: int
