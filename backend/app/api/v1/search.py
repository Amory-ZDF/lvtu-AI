from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.db.session import get_db_session
from app.middleware.auth import get_current_user_optional
from app.models.trip import Trip
from app.models.trip_point import TripPoint
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.search import SearchResponse, SearchResultItem

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]

SearchType = Literal["destination", "spot", "all"]

_SNIPPET_MAX_LENGTH = 120


def _make_snippet(text: str | None, keyword: str) -> str | None:
    if not text:
        return None
    lower_text = text.lower()
    lower_keyword = keyword.lower()
    idx = lower_text.find(lower_keyword)
    if idx < 0:
        return text[:_SNIPPET_MAX_LENGTH] if len(text) > _SNIPPET_MAX_LENGTH else text
    start = max(0, idx - 40)
    end = min(len(text), idx + len(keyword) + 80)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def _search_destinations(db: Session, keyword: str) -> list[SearchResultItem]:
    pattern = f"%{keyword}%"
    stmt = select(Trip).where(
        or_(
            Trip.destination_name.ilike(pattern),
            Trip.title.ilike(pattern),
        )
    )
    trips = list(db.scalars(stmt))
    return [
        SearchResultItem(
            type="destination",
            id=trip.id,
            title=trip.title,
            snippet=_make_snippet(trip.destination_name, keyword),
            image_url=trip.cover_image_url,
        )
        for trip in trips
    ]


def _search_spots(db: Session, keyword: str) -> list[SearchResultItem]:
    pattern = f"%{keyword}%"
    stmt = select(TripPoint).where(
        or_(
            TripPoint.name.ilike(pattern),
            TripPoint.address.ilike(pattern),
        )
    )
    points = list(db.scalars(stmt))
    return [
        SearchResultItem(
            type="spot",
            id=point.id,
            title=point.name,
            snippet=_make_snippet(point.address, keyword),
            image_url=point.image_url,
        )
        for point in points
    ]


@router.get("/search", tags=["search"])
def search(
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    type: SearchType = Query(default="all"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    items: list[SearchResultItem] = []

    if type in ("destination", "all"):
        items.extend(_search_destinations(db, keyword))
    if type in ("spot", "all"):
        items.extend(_search_spots(db, keyword))

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    response = SearchResponse(
        items=page_items,
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_response(response.model_dump(mode="json"), request)
