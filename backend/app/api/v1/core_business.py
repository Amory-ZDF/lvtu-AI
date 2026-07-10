from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.responses import paginated_response, success_response
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.middleware.auth import get_current_user, get_current_user_optional
from app.models.packing_item import PackingItem
from app.models.trip import Trip
from app.models.trip_day import TripDay
from app.models.trip_point import TripPoint
from app.models.trip_version import TripVersion
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.common import ApiResponse
from app.schemas.domain import (
    PackingItemCheckUpdate,
    PackingItemCreate,
    PackingItemRead,
    PackingItemUpdate,
    SortOrderUpdate,
    TripCreate,
    TripDayCreate,
    TripDayRead,
    TripDayUpdate,
    TripPointCreate,
    TripPointRead,
    TripPointUpdate,
    TripRead,
    TripUpdate,
    UserProfileRead,
    UserProfileUpsert,
)

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
MAX_TRIP_VERSIONS = 3


def _enforce_owner(current_user: User | None, user_id: UUID) -> None:
    """When a user is authenticated, ensure they own the resource.

    In development mode (no token provided) access is allowed for backward
    compatibility with existing unauthenticated clients.
    """
    if current_user is not None and current_user.id != user_id:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message="无权操作该用户资源",
        )


def _commit_or_409(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message=detail,
        ) from exc


def _get_user_or_404(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.USER_NOT_FOUND,
            message="用户不存在",
        )
    return user


def _get_user_profile_or_404(db: Session, user_id: UUID) -> User:
    user = db.scalar(select(User).options(selectinload(User.preference)).where(User.id == user_id))
    if user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.USER_NOT_FOUND,
            message="用户不存在",
        )
    return user


def _get_trip_or_404(db: Session, user_id: UUID, trip_id: UUID) -> Trip:
    trip = db.scalar(
        select(Trip)
        .options(selectinload(Trip.days).selectinload(TripDay.points))
        .where(Trip.id == trip_id, Trip.user_id == user_id)
    )
    if trip is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_NOT_FOUND,
            message="行程不存在",
        )
    return trip


def _get_trip_by_id_or_404(db: Session, trip_id: UUID) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_NOT_FOUND,
            message="行程不存在",
        )
    return trip


def _list_trip_days(db: Session, trip_id: UUID) -> list[TripDay]:
    stmt = select(TripDay).where(TripDay.trip_id == trip_id).order_by(TripDay.day_index)
    return list(db.scalars(stmt))


def _get_trip_day_or_404(db: Session, trip_id: UUID, day_id: UUID) -> TripDay:
    trip_day = db.scalar(select(TripDay).where(TripDay.id == day_id, TripDay.trip_id == trip_id))
    if trip_day is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_DAY_NOT_FOUND,
            message="行程天不存在",
        )
    return trip_day


def _get_trip_day_by_id_or_404(db: Session, trip_day_id: UUID) -> TripDay:
    trip_day = db.get(TripDay, trip_day_id)
    if trip_day is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_DAY_NOT_FOUND,
            message="行程天不存在",
        )
    return trip_day


def _list_trip_points(db: Session, trip_day_id: UUID) -> list[TripPoint]:
    stmt = (
        select(TripPoint)
        .where(TripPoint.trip_day_id == trip_day_id)
        .order_by(TripPoint.sort_order)
    )
    return list(db.scalars(stmt))


def _get_trip_point_or_404(db: Session, trip_day_id: UUID, point_id: UUID) -> TripPoint:
    stmt = select(TripPoint).where(
        TripPoint.id == point_id,
        TripPoint.trip_day_id == trip_day_id,
    )
    point = db.scalar(stmt)
    if point is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_POINT_NOT_FOUND,
            message="行程点不存在",
        )
    return point


def _get_packing_item_or_404(db: Session, trip_id: UUID, item_id: UUID) -> PackingItem:
    stmt = select(PackingItem).where(
        PackingItem.id == item_id,
        PackingItem.trip_id == trip_id,
    )
    item = db.scalar(stmt)
    if item is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.PACKING_ITEM_NOT_FOUND,
            message="打包清单项不存在",
        )
    return item


def _normalize_position(position: int | None, length: int) -> int:
    if length <= 0:
        return 1
    if position is None:
        return length
    return max(1, min(position, length))


def _reassign_order(items: list[TripDay], attr_name: str, db: Session) -> None:
    if not items:
        return

    temp_base = len(items) + 1000
    for index, item in enumerate(items, start=1):
        setattr(item, attr_name, temp_base + index)
    db.flush()

    for index, item in enumerate(items, start=1):
        setattr(item, attr_name, index)
    db.flush()


def _validate_reorder_ids(ordered_ids: list[UUID], existing_ids: list[UUID], detail: str) -> None:
    if len(ordered_ids) != len(existing_ids):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.VALIDATION_ERROR,
            message=detail,
        )
    if len(set(ordered_ids)) != len(ordered_ids):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.VALIDATION_ERROR,
            message="排序列表包含重复 ID",
        )
    if set(ordered_ids) != set(existing_ids):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.VALIDATION_ERROR,
            message=detail,
        )


def _serialize_trip_snapshot(db: Session, trip_id: UUID) -> dict:
    """Serialize current trip state (trip + days + points + packing_items) to a dict."""
    trip = db.get(Trip, trip_id)
    if trip is None:
        return {}

    trip_data = TripRead.model_validate(trip).model_dump(mode="json")

    days = _list_trip_days(db, trip_id)
    days_data = []
    for day in days:
        day_data = TripDayRead.model_validate(day).model_dump(mode="json")
        points = _list_trip_points(db, day.id)
        day_data["points"] = [
            TripPointRead.model_validate(p).model_dump(mode="json") for p in points
        ]
        days_data.append(day_data)

    packing_stmt = (
        select(PackingItem)
        .where(PackingItem.trip_id == trip_id)
        .order_by(PackingItem.created_at, PackingItem.id)
    )
    packing_items = list(db.scalars(packing_stmt))
    items_data = [
        PackingItemRead.model_validate(i).model_dump(mode="json") for i in packing_items
    ]

    return {
        "trip": trip_data,
        "days": days_data,
        "packing_items": items_data,
    }


def _snapshot_for_compare(value):
    if isinstance(value, dict):
        return {
            key: _snapshot_for_compare(item)
            for key, item in value.items()
            if key not in {"created_at", "updated_at"}
        }
    if isinstance(value, list):
        return [_snapshot_for_compare(item) for item in value]
    return value


def _prune_trip_versions(db: Session, trip_id: UUID) -> None:
    versions = list(
        db.scalars(
            select(TripVersion)
            .where(TripVersion.trip_id == trip_id)
            .order_by(TripVersion.version_number.desc())
        )
    )
    for version in versions[MAX_TRIP_VERSIONS:]:
        db.delete(version)
    if len(versions) > MAX_TRIP_VERSIONS:
        db.flush()


def _create_version_snapshot(
    db: Session,
    trip_id: UUID,
    note: str | None = None,
    created_by: UUID | None = None,
) -> TripVersion | None:
    """Create a version snapshot of the current trip state.

    Silent on failure: any exception is swallowed so that the calling
    operation is not interrupted. Returns the created TripVersion or None.
    """
    try:
        snapshot = _serialize_trip_snapshot(db, trip_id)
        if not snapshot:
            return None

        latest_version = db.scalar(
            select(TripVersion)
            .where(TripVersion.trip_id == trip_id)
            .order_by(TripVersion.version_number.desc())
            .limit(1)
        )
        if latest_version is not None and _snapshot_for_compare(
            latest_version.snapshot
        ) == _snapshot_for_compare(snapshot):
            _prune_trip_versions(db, trip_id)
            db.commit()
            db.refresh(latest_version)
            return latest_version

        max_version = db.scalar(
            select(func.max(TripVersion.version_number)).where(
                TripVersion.trip_id == trip_id
            )
        ) or 0

        version = TripVersion(
            trip_id=trip_id,
            version_number=max_version + 1,
            snapshot=snapshot,
            created_by=created_by,
            note=note,
        )
        db.add(version)
        db.flush()
        _prune_trip_versions(db, trip_id)
        db.commit()
        db.refresh(version)
        return version
    except Exception:
        db.rollback()
        return None


@router.get("/users/{user_id}/profile", tags=["users"])
def get_user_profile(
    user_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _enforce_owner(current_user, user_id)
    user = _get_user_profile_or_404(db, user_id)
    return success_response(UserProfileRead.model_validate(user).model_dump(mode="json"), request)


@router.put("/users/{user_id}/profile", tags=["users"])
def upsert_user_profile(
    user_id: UUID,
    payload: UserProfileUpsert,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _enforce_owner(current_user, user_id)
    user = db.get(User, user_id)
    if user is None:
        user = User(
            id=user_id,
            email=payload.email,
            username=payload.username,
            display_name=payload.display_name,
            avatar_url=payload.avatar_url,
            bio=payload.bio,
        )
        db.add(user)
    else:
        user.email = payload.email
        user.username = payload.username
        user.display_name = payload.display_name
        user.avatar_url = payload.avatar_url
        user.bio = payload.bio

    preference = db.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
    if preference is None:
        preference = UserPreference(user_id=user_id)
        db.add(preference)

    preference.departure_city = payload.departure_city
    preference.preferred_styles = payload.preferred_styles
    preference.budget_level = payload.budget_level
    preference.language = payload.language
    preference.timezone = payload.timezone

    _commit_or_409(db, "用户邮箱或用户名已存在")
    user = _get_user_profile_or_404(db, user_id)
    return success_response(UserProfileRead.model_validate(user).model_dump(mode="json"), request)


@router.get("/users/{user_id}/trips", tags=["trips"])
def list_trips(
    user_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    _enforce_owner(current_user, user_id)
    _get_user_or_404(db, user_id)
    total = db.scalar(select(func.count()).select_from(Trip).where(Trip.user_id == user_id)) or 0
    stmt = (
        select(Trip)
        .where(Trip.user_id == user_id)
        .order_by(Trip.updated_at.desc(), Trip.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    trips = list(db.scalars(stmt))
    items = [TripRead.model_validate(t).model_dump(mode="json") for t in trips]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)


@router.post(
    "/users/{user_id}/trips",
    status_code=status.HTTP_201_CREATED,
    tags=["trips"],
)
def create_trip(
    user_id: UUID,
    payload: TripCreate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _enforce_owner(current_user, user_id)
    _get_user_or_404(db, user_id)
    trip = Trip(user_id=user_id, **payload.model_dump())
    db.add(trip)
    _commit_or_409(db, "行程创建失败")
    db.refresh(trip)
    return success_response(TripRead.model_validate(trip).model_dump(mode="json"), request)


@router.get("/users/{user_id}/trips/{trip_id}", tags=["trips"])
def get_trip(
    user_id: UUID,
    trip_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _enforce_owner(current_user, user_id)
    trip = _get_trip_or_404(db, user_id, trip_id)
    return success_response(TripRead.model_validate(trip).model_dump(mode="json"), request)


@router.patch("/users/{user_id}/trips/{trip_id}", tags=["trips"])
def update_trip(
    user_id: UUID,
    trip_id: UUID,
    payload: TripUpdate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _enforce_owner(current_user, user_id)
    trip = _get_trip_or_404(db, user_id, trip_id)
    _create_version_snapshot(db, trip_id, note="行程更新前")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(trip, field, value)
    _commit_or_409(db, "行程更新失败")
    db.refresh(trip)
    return success_response(TripRead.model_validate(trip).model_dump(mode="json"), request)


@router.delete(
    "/users/{user_id}/trips/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["trips"],
)
def delete_trip(
    user_id: UUID,
    trip_id: UUID,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> Response:
    _enforce_owner(current_user, user_id)
    trip = _get_trip_or_404(db, user_id, trip_id)
    db.delete(trip)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/trips/{trip_id}/days", tags=["trip-days"])
def list_trip_days(
    trip_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
) -> ApiResponse:
    _get_trip_by_id_or_404(db, trip_id)
    total = (
        db.scalar(select(func.count()).select_from(TripDay).where(TripDay.trip_id == trip_id)) or 0
    )
    stmt = (
        select(TripDay)
        .options(selectinload(TripDay.points))
        .where(TripDay.trip_id == trip_id)
        .order_by(TripDay.day_index)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    days = list(db.scalars(stmt))
    items = [TripDayRead.model_validate(d).model_dump(mode="json") for d in days]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)


@router.post(
    "/trips/{trip_id}/days",
    status_code=status.HTTP_201_CREATED,
    tags=["trip-days"],
)
def create_trip_day(
    trip_id: UUID,
    payload: TripDayCreate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _get_trip_by_id_or_404(db, trip_id)
    existing_days = _list_trip_days(db, trip_id)
    trip_day = TripDay(
        trip_id=trip_id,
        day_index=len(existing_days) + 1001,
        date=payload.date,
        title=payload.title,
        summary=payload.summary,
    )
    db.add(trip_day)
    db.flush()

    target_index = _normalize_position(payload.day_index, len(existing_days) + 1)
    ordered_days = existing_days.copy()
    ordered_days.insert(target_index - 1, trip_day)
    _reassign_order(ordered_days, "day_index", db)

    _commit_or_409(db, "行程天排序冲突")
    db.refresh(trip_day)
    return success_response(TripDayRead.model_validate(trip_day).model_dump(mode="json"), request)


@router.patch("/trips/{trip_id}/days/reorder", tags=["trip-days"])
def reorder_trip_days(
    trip_id: UUID,
    payload: SortOrderUpdate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _get_trip_by_id_or_404(db, trip_id)
    existing_days = _list_trip_days(db, trip_id)
    existing_ids = [item.id for item in existing_days]
    _validate_reorder_ids(payload.ordered_ids, existing_ids, "行程天排序需包含该行程全部 day_id")
    day_map = {item.id: item for item in existing_days}
    ordered_days = [day_map[item_id] for item_id in payload.ordered_ids]
    _reassign_order(ordered_days, "day_index", db)
    _commit_or_409(db, "行程天重排失败")
    return success_response(
        [TripDayRead.model_validate(d).model_dump(mode="json") for d in ordered_days],
        request,
    )


@router.get("/trips/{trip_id}/days/{day_id}", tags=["trip-days"])
def get_trip_day(
    trip_id: UUID,
    day_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    trip_day = _get_trip_day_or_404(db, trip_id, day_id)
    return success_response(TripDayRead.model_validate(trip_day).model_dump(mode="json"), request)


@router.patch("/trips/{trip_id}/days/{day_id}", tags=["trip-days"])
def update_trip_day(
    trip_id: UUID,
    day_id: UUID,
    payload: TripDayUpdate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    trip_day = _get_trip_day_or_404(db, trip_id, day_id)
    _create_version_snapshot(db, trip_id, note="行程天更新前")
    update_data = payload.model_dump(exclude_unset=True)
    target_index = update_data.pop("day_index", None)

    for field, value in update_data.items():
        setattr(trip_day, field, value)

    if target_index is not None:
        existing_days = _list_trip_days(db, trip_id)
        ordered_days = [item for item in existing_days if item.id != trip_day.id]
        ordered_days.insert(_normalize_position(target_index, len(existing_days)) - 1, trip_day)
        _reassign_order(ordered_days, "day_index", db)

    _commit_or_409(db, "行程天更新失败")
    db.refresh(trip_day)
    return success_response(TripDayRead.model_validate(trip_day).model_dump(mode="json"), request)


@router.delete(
    "/trips/{trip_id}/days/{day_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["trip-days"],
)
def delete_trip_day(
    trip_id: UUID,
    day_id: UUID,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> Response:
    trip_day = _get_trip_day_or_404(db, trip_id, day_id)
    remaining_days = [item for item in _list_trip_days(db, trip_id) if item.id != trip_day.id]
    db.delete(trip_day)
    db.flush()
    _reassign_order(remaining_days, "day_index", db)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/trip-days/{trip_day_id}/points",
    tags=["trip-points"],
)
def list_trip_points(
    trip_day_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
) -> ApiResponse:
    _get_trip_day_by_id_or_404(db, trip_day_id)
    total = (
        db.scalar(
            select(func.count())
            .select_from(TripPoint)
            .where(TripPoint.trip_day_id == trip_day_id)
        )
        or 0
    )
    stmt = (
        select(TripPoint)
        .where(TripPoint.trip_day_id == trip_day_id)
        .order_by(TripPoint.sort_order)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    points = list(db.scalars(stmt))
    items = [TripPointRead.model_validate(p).model_dump(mode="json") for p in points]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)


@router.post(
    "/trip-days/{trip_day_id}/points",
    status_code=status.HTTP_201_CREATED,
    tags=["trip-points"],
)
def create_trip_point(
    trip_day_id: UUID,
    payload: TripPointCreate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _get_trip_day_by_id_or_404(db, trip_day_id)
    existing_points = _list_trip_points(db, trip_day_id)
    trip_point = TripPoint(
        trip_day_id=trip_day_id,
        sort_order=len(existing_points) + 1001,
        **payload.model_dump(exclude={"sort_order"}),
    )
    db.add(trip_point)
    db.flush()

    target_order = _normalize_position(payload.sort_order, len(existing_points) + 1)
    ordered_points = existing_points.copy()
    ordered_points.insert(target_order - 1, trip_point)
    _reassign_order(ordered_points, "sort_order", db)

    _commit_or_409(db, "行程点排序冲突")
    db.refresh(trip_point)
    return success_response(
        TripPointRead.model_validate(trip_point).model_dump(mode="json"),
        request,
    )


@router.patch(
    "/trip-days/{trip_day_id}/points/reorder",
    tags=["trip-points"],
)
def reorder_trip_points(
    trip_day_id: UUID,
    payload: SortOrderUpdate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    trip_day = _get_trip_day_by_id_or_404(db, trip_day_id)
    _create_version_snapshot(db, trip_day.trip_id, note="行程点重排前")
    existing_points = _list_trip_points(db, trip_day_id)
    existing_ids = [item.id for item in existing_points]
    _validate_reorder_ids(payload.ordered_ids, existing_ids, "行程点排序需包含该天全部 point_id")
    point_map = {item.id: item for item in existing_points}
    ordered_points = [point_map[item_id] for item_id in payload.ordered_ids]
    _reassign_order(ordered_points, "sort_order", db)
    _commit_or_409(db, "行程点重排失败")
    return success_response(
        [TripPointRead.model_validate(p).model_dump(mode="json") for p in ordered_points],
        request,
    )


@router.get(
    "/trip-days/{trip_day_id}/points/{point_id}",
    tags=["trip-points"],
)
def get_trip_point(
    trip_day_id: UUID,
    point_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    trip_point = _get_trip_point_or_404(db, trip_day_id, point_id)
    return success_response(
        TripPointRead.model_validate(trip_point).model_dump(mode="json"),
        request,
    )


@router.patch(
    "/trip-days/{trip_day_id}/points/{point_id}",
    tags=["trip-points"],
)
def update_trip_point(
    trip_day_id: UUID,
    point_id: UUID,
    payload: TripPointUpdate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    trip_point = _get_trip_point_or_404(db, trip_day_id, point_id)
    update_data = payload.model_dump(exclude_unset=True)
    target_order = update_data.pop("sort_order", None)

    for field, value in update_data.items():
        setattr(trip_point, field, value)

    if target_order is not None:
        existing_points = _list_trip_points(db, trip_day_id)
        ordered_points = [item for item in existing_points if item.id != trip_point.id]
        ordered_points.insert(
            _normalize_position(target_order, len(existing_points)) - 1,
            trip_point,
        )
        _reassign_order(ordered_points, "sort_order", db)

    _commit_or_409(db, "行程点更新失败")
    db.refresh(trip_point)
    return success_response(
        TripPointRead.model_validate(trip_point).model_dump(mode="json"),
        request,
    )


@router.delete(
    "/trip-days/{trip_day_id}/points/{point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["trip-points"],
)
def delete_trip_point(
    trip_day_id: UUID,
    point_id: UUID,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> Response:
    trip_point = _get_trip_point_or_404(db, trip_day_id, point_id)
    remaining_points = [
        item for item in _list_trip_points(db, trip_day_id) if item.id != trip_point.id
    ]
    db.delete(trip_point)
    db.flush()
    _reassign_order(remaining_points, "sort_order", db)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/trips/{trip_id}/packing-items",
    tags=["packing-items"],
)
def list_packing_items(
    trip_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
) -> ApiResponse:
    _get_trip_by_id_or_404(db, trip_id)
    total = (
        db.scalar(
            select(func.count())
            .select_from(PackingItem)
            .where(PackingItem.trip_id == trip_id)
        )
        or 0
    )
    stmt = (
        select(PackingItem)
        .where(PackingItem.trip_id == trip_id)
        .order_by(PackingItem.created_at, PackingItem.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items_orm = list(db.scalars(stmt))
    items = [PackingItemRead.model_validate(i).model_dump(mode="json") for i in items_orm]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)


@router.post(
    "/trips/{trip_id}/packing-items",
    status_code=status.HTTP_201_CREATED,
    tags=["packing-items"],
)
def create_packing_item(
    trip_id: UUID,
    payload: PackingItemCreate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    _get_trip_by_id_or_404(db, trip_id)
    item = PackingItem(trip_id=trip_id, **payload.model_dump())
    db.add(item)
    _commit_or_409(db, "打包清单项创建失败")
    db.refresh(item)
    return success_response(PackingItemRead.model_validate(item).model_dump(mode="json"), request)


@router.get(
    "/trips/{trip_id}/packing-items/{item_id}",
    tags=["packing-items"],
)
def get_packing_item(
    trip_id: UUID,
    item_id: UUID,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    item = _get_packing_item_or_404(db, trip_id, item_id)
    return success_response(PackingItemRead.model_validate(item).model_dump(mode="json"), request)


@router.patch(
    "/trips/{trip_id}/packing-items/{item_id}",
    tags=["packing-items"],
)
def update_packing_item(
    trip_id: UUID,
    item_id: UUID,
    payload: PackingItemUpdate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    item = _get_packing_item_or_404(db, trip_id, item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return success_response(PackingItemRead.model_validate(item).model_dump(mode="json"), request)


@router.patch(
    "/trips/{trip_id}/packing-items/{item_id}/checked",
    tags=["packing-items"],
)
def update_packing_item_checked(
    trip_id: UUID,
    item_id: UUID,
    payload: PackingItemCheckUpdate,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    item = _get_packing_item_or_404(db, trip_id, item_id)
    item.is_checked = payload.is_checked
    db.commit()
    db.refresh(item)
    return success_response(PackingItemRead.model_validate(item).model_dump(mode="json"), request)


@router.delete(
    "/trips/{trip_id}/packing-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["packing-items"],
)
def delete_packing_item(
    trip_id: UUID,
    item_id: UUID,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> Response:
    item = _get_packing_item_or_404(db, trip_id, item_id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
