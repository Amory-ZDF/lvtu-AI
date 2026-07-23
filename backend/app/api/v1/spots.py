from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.responses import paginated_response, success_response
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.middleware.auth import get_current_user_optional
from app.models.photo_spot_recommendation import PhotoSpotRecommendation
from app.models.trip import Trip
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.spot import (
    PhotoSpotRecommendationCreate,
    PhotoSpotRecommendationRead,
    PhotoSpotRecommendationUpdate,
)

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]


def _get_trip_or_404(db: Session, trip_id: UUID) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None or trip.deleted_at is not None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_NOT_FOUND,
            message="行程不存在",
        )
    return trip


def _get_spot_or_404(db: Session, spot_id: UUID) -> PhotoSpotRecommendation:
    spot = db.get(PhotoSpotRecommendation, spot_id)
    if spot is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.PHOTO_SPOT_NOT_FOUND,
            message="机位推荐不存在",
        )
    return spot


@router.get("/trips/{trip_id}/spots", tags=["spots"])
def list_spots(
    trip_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    _get_trip_or_404(db, trip_id)
    total = (
        db.scalar(
            select(func.count())
            .select_from(PhotoSpotRecommendation)
            .where(PhotoSpotRecommendation.trip_id == trip_id)
        )
        or 0
    )
    stmt = (
        select(PhotoSpotRecommendation)
        .where(PhotoSpotRecommendation.trip_id == trip_id)
        .order_by(
            PhotoSpotRecommendation.created_at.desc(),
            PhotoSpotRecommendation.id.desc(),
        )
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    spots = list(db.scalars(stmt))
    items = [PhotoSpotRecommendationRead.model_validate(s).model_dump(mode="json") for s in spots]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)


@router.post(
    "/trips/{trip_id}/spots",
    status_code=status.HTTP_201_CREATED,
    tags=["spots"],
)
def create_spot(
    trip_id: UUID,
    payload: PhotoSpotRecommendationCreate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _get_trip_or_404(db, trip_id)
    spot = PhotoSpotRecommendation(
        trip_id=trip_id,
        **payload.model_dump(exclude={"trip_id"}),
    )
    db.add(spot)
    db.commit()
    db.refresh(spot)
    return success_response(
        PhotoSpotRecommendationRead.model_validate(spot).model_dump(mode="json"),
        request,
    )


@router.get("/spots/{spot_id}", tags=["spots"])
def get_spot(
    spot_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    spot = _get_spot_or_404(db, spot_id)
    return success_response(
        PhotoSpotRecommendationRead.model_validate(spot).model_dump(mode="json"),
        request,
    )


@router.patch("/spots/{spot_id}", tags=["spots"])
def update_spot(
    spot_id: UUID,
    payload: PhotoSpotRecommendationUpdate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    spot = _get_spot_or_404(db, spot_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(spot, field, value)
    db.commit()
    db.refresh(spot)
    return success_response(
        PhotoSpotRecommendationRead.model_validate(spot).model_dump(mode="json"),
        request,
    )


@router.delete(
    "/spots/{spot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["spots"],
)
def delete_spot(
    spot_id: UUID,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> Response:
    spot = _get_spot_or_404(db, spot_id)
    db.delete(spot)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
