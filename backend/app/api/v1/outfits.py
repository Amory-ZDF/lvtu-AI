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
from app.models.outfit_recommendation import OutfitRecommendation
from app.models.trip import Trip
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.outfit import (
    OutfitRecommendationCreate,
    OutfitRecommendationRead,
    OutfitRecommendationUpdate,
)

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]


def _get_trip_or_404(db: Session, trip_id: UUID) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_NOT_FOUND,
            message="行程不存在",
        )
    return trip


def _get_outfit_or_404(db: Session, outfit_id: UUID) -> OutfitRecommendation:
    outfit = db.get(OutfitRecommendation, outfit_id)
    if outfit is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.OUTFIT_NOT_FOUND,
            message="穿搭推荐不存在",
        )
    return outfit


@router.get("/trips/{trip_id}/outfits", tags=["outfits"])
def list_outfits(
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
            .select_from(OutfitRecommendation)
            .where(OutfitRecommendation.trip_id == trip_id)
        )
        or 0
    )
    stmt = (
        select(OutfitRecommendation)
        .where(OutfitRecommendation.trip_id == trip_id)
        .order_by(OutfitRecommendation.created_at.desc(), OutfitRecommendation.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    outfits = list(db.scalars(stmt))
    items = [OutfitRecommendationRead.model_validate(o).model_dump(mode="json") for o in outfits]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)


@router.post(
    "/trips/{trip_id}/outfits",
    status_code=status.HTTP_201_CREATED,
    tags=["outfits"],
)
def create_outfit(
    trip_id: UUID,
    payload: OutfitRecommendationCreate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _get_trip_or_404(db, trip_id)
    outfit = OutfitRecommendation(
        trip_id=trip_id,
        **payload.model_dump(exclude={"trip_id"}),
    )
    db.add(outfit)
    db.commit()
    db.refresh(outfit)
    return success_response(
        OutfitRecommendationRead.model_validate(outfit).model_dump(mode="json"),
        request,
    )


@router.get("/outfits/{outfit_id}", tags=["outfits"])
def get_outfit(
    outfit_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    outfit = _get_outfit_or_404(db, outfit_id)
    return success_response(
        OutfitRecommendationRead.model_validate(outfit).model_dump(mode="json"),
        request,
    )


@router.patch("/outfits/{outfit_id}", tags=["outfits"])
def update_outfit(
    outfit_id: UUID,
    payload: OutfitRecommendationUpdate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    outfit = _get_outfit_or_404(db, outfit_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(outfit, field, value)
    db.commit()
    db.refresh(outfit)
    return success_response(
        OutfitRecommendationRead.model_validate(outfit).model_dump(mode="json"),
        request,
    )


@router.delete(
    "/outfits/{outfit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["outfits"],
)
def delete_outfit(
    outfit_id: UUID,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> Response:
    outfit = _get_outfit_or_404(db, outfit_id)
    db.delete(outfit)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
