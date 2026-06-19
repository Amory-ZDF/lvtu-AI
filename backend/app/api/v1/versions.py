from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.responses import paginated_response, success_response
from app.api.v1.core_business import _create_version_snapshot
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.middleware.auth import get_current_user_optional
from app.models.packing_item import PackingItem
from app.models.trip import Trip
from app.models.trip_day import TripDay
from app.models.trip_point import TripPoint
from app.models.trip_version import TripVersion
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.version import TripVersionRead, TripVersionRestoreResponse

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


def _get_version_or_404(db: Session, trip_id: UUID, version_id: UUID) -> TripVersion:
    version = db.scalar(
        select(TripVersion).where(
            TripVersion.id == version_id,
            TripVersion.trip_id == trip_id,
        )
    )
    if version is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message="行程版本不存在",
        )
    return version


def _restore_snapshot(db: Session, trip: Trip, snapshot: dict) -> None:
    """Restore trip + days + points + packing_items from a snapshot dict."""
    trip_data = snapshot.get("trip", {})

    trip.title = trip_data.get("title", trip.title)
    trip.destination_name = trip_data.get("destination_name", trip.destination_name)
    start_date_raw = trip_data.get("start_date")
    trip.start_date = date.fromisoformat(start_date_raw) if start_date_raw else None
    end_date_raw = trip_data.get("end_date")
    trip.end_date = date.fromisoformat(end_date_raw) if end_date_raw else None
    trip.status = trip_data.get("status", trip.status)
    trip.cover_image_url = trip_data.get("cover_image_url")
    trip.notes = trip_data.get("notes")

    # Delete existing days (cascade deletes points via DB) and packing items
    existing_days = list(
        db.scalars(select(TripDay).where(TripDay.trip_id == trip.id))
    )
    for day in existing_days:
        db.delete(day)
    existing_items = list(
        db.scalars(select(PackingItem).where(PackingItem.trip_id == trip.id))
    )
    for item in existing_items:
        db.delete(item)
    db.flush()

    # Recreate days and points
    for day_data in snapshot.get("days", []):
        day_date_raw = day_data.get("date")
        day = TripDay(
            trip_id=trip.id,
            day_index=day_data.get("day_index", 1),
            date=date.fromisoformat(day_date_raw) if day_date_raw else None,
            title=day_data.get("title"),
            summary=day_data.get("summary"),
        )
        db.add(day)
        db.flush()

        for point_data in day_data.get("points", []):
            lat_raw = point_data.get("latitude")
            lng_raw = point_data.get("longitude")
            start_raw = point_data.get("start_time")
            end_raw = point_data.get("end_time")
            point = TripPoint(
                trip_day_id=day.id,
                name=point_data.get("name", ""),
                point_type=point_data.get("point_type", "spot"),
                address=point_data.get("address"),
                latitude=Decimal(str(lat_raw)) if lat_raw is not None else None,
                longitude=Decimal(str(lng_raw)) if lng_raw is not None else None,
                start_time=time.fromisoformat(start_raw) if start_raw else None,
                end_time=time.fromisoformat(end_raw) if end_raw else None,
                sort_order=point_data.get("sort_order", 0),
                notes=point_data.get("notes"),
                image_url=point_data.get("image_url"),
            )
            db.add(point)

    # Recreate packing items
    for item_data in snapshot.get("packing_items", []):
        item = PackingItem(
            trip_id=trip.id,
            name=item_data.get("name", ""),
            category=item_data.get("category"),
            quantity=item_data.get("quantity", 1),
            is_checked=item_data.get("is_checked", False),
            note=item_data.get("note"),
        )
        db.add(item)


@router.get("/trips/{trip_id}/versions", tags=["trip-versions"])
def list_trip_versions(
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
            .select_from(TripVersion)
            .where(TripVersion.trip_id == trip_id)
        )
        or 0
    )
    stmt = (
        select(TripVersion)
        .where(TripVersion.trip_id == trip_id)
        .order_by(TripVersion.version_number.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    versions = list(db.scalars(stmt))
    items = [TripVersionRead.model_validate(v).model_dump(mode="json") for v in versions]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)


@router.post(
    "/trips/{trip_id}/versions",
    status_code=status.HTTP_201_CREATED,
    tags=["trip-versions"],
)
def create_trip_version(
    trip_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    note: str | None = None,
) -> ApiResponse:
    _get_trip_or_404(db, trip_id)
    created_by = current_user.id if current_user is not None else None
    version = _create_version_snapshot(db, trip_id, note=note, created_by=created_by)
    if version is None:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCode.INTERNAL_ERROR,
            message="版本快照创建失败",
        )
    return success_response(
        TripVersionRead.model_validate(version).model_dump(mode="json"),
        request,
    )


@router.post(
    "/trips/{trip_id}/versions/{version_id}/restore",
    tags=["trip-versions"],
)
def restore_trip_version(
    trip_id: UUID,
    version_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    trip = _get_trip_or_404(db, trip_id)
    version = _get_version_or_404(db, trip_id, version_id)

    # Auto-create a snapshot of current state before restoring
    created_by = current_user.id if current_user is not None else None
    _create_version_snapshot(
        db,
        trip_id,
        note="恢复前自动快照",
        created_by=created_by,
    )

    _restore_snapshot(db, trip, version.snapshot)
    db.commit()
    db.refresh(trip)

    return success_response(
        TripVersionRestoreResponse(
            trip_id=trip_id,
            version_number=version.version_number,
            restored_at=trip.updated_at,
        ).model_dump(mode="json"),
        request,
    )
