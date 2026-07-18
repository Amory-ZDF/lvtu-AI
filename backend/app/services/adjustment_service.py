from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from fastapi import status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppException
from app.integrations.amap.client import get_amap_client
from app.integrations.llm.json_client import OpenAICompatibleJsonClient
from app.integrations.prompts.adjustment import build_adjustment_prompt
from app.models.trip import Trip
from app.models.trip_day import TripDay
from app.models.trip_point import TripPoint
from app.schemas.adjustment import AdjustmentChange, AdjustmentPlan


def serialize_current_itinerary(db: Session, trip: Trip) -> dict:
    days = list(
        db.scalars(
            select(TripDay).where(TripDay.trip_id == trip.id).order_by(TripDay.day_index)
        )
    )
    return {
        "trip_id": str(trip.id),
        "destination": trip.destination_name,
        "title": trip.title,
        "days": [
            {
                "day_id": str(day.id),
                "day_index": day.day_index,
                "date": day.date.isoformat() if day.date else None,
                "title": day.title,
                "summary": day.summary,
                "points": [
                    {
                        "point_id": str(point.id),
                        "name": point.name,
                        "point_type": point.point_type,
                        "start_time": point.start_time.isoformat(timespec="minutes")
                        if point.start_time
                        else None,
                        "end_time": point.end_time.isoformat(timespec="minutes")
                        if point.end_time
                        else None,
                        "notes": point.notes,
                        "position": point.sort_order,
                    }
                    for point in _list_points(db, day.id)
                ],
            }
            for day in days
        ],
    }


def generate_adjustment_plan(
    settings: Settings,
    current_itinerary: dict,
    instruction: str,
    target_day_id: UUID | None,
) -> AdjustmentPlan:
    if not settings.ai_base_url or not settings.ai_api_key or not settings.ai_model_name:
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="ai_adjustment_not_configured",
            message="文本大模型尚未配置，暂时无法使用 AI 修改行程",
        )

    client = OpenAICompatibleJsonClient(
        settings.ai_base_url,
        settings.ai_api_key,
        settings.ai_model_name,
    )
    messages = build_adjustment_prompt(
        instruction,
        current_itinerary,
        str(target_day_id) if target_day_id else None,
    )
    data = client.complete_json(messages, temperature=0.2)
    try:
        return AdjustmentPlan.model_validate(data)
    except ValidationError as exc:
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="ai_response_invalid",
            message="AI 返回的行程调整方案无法安全执行",
        ) from exc


def validate_adjustment_plan(
    db: Session,
    trip: Trip,
    plan: AdjustmentPlan,
    target_day_id: UUID | None,
) -> None:
    days, points_by_day, point_map = _load_trip_state(db, trip.id)
    day_map = {day.id: day for day in days}
    used_point_ids: set[UUID] = set()
    pending_names: dict[UUID, set[str]] = {
        day.id: {_normalise_name(point.name) for point in points}
        for day, points in ((day, points_by_day[day.id]) for day in days)
    }
    has_effect = False

    for change in plan.changes:
        _validate_change_references(change, day_map, point_map)

        if change.point_id is not None:
            if change.point_id in used_point_ids:
                raise _invalid_plan("同一个行程点不能在一次调整中被多次修改")
            used_point_ids.add(change.point_id)

        affected_day_id = _affected_day_id(change, point_map)
        if target_day_id is not None and affected_day_id != target_day_id:
            raise _invalid_plan("AI 调整超出了用户指定的日期范围")

        if change.operation == "add":
            assert change.day_id is not None and change.name is not None
            _validate_name(change.name)
            normalised = _normalise_name(change.name)
            if normalised in pending_names[change.day_id]:
                raise _invalid_plan(f"行程中已经存在地点：{change.name}")
            pending_names[change.day_id].add(normalised)
            has_effect = True
        elif change.operation == "update":
            assert change.point_id is not None
            point = point_map[change.point_id]
            if "name" in change.model_fields_set and change.name is not None:
                _validate_name(change.name)
                normalised = _normalise_name(change.name)
                current_name = _normalise_name(point.name)
                if normalised != current_name and normalised in pending_names[point.trip_day_id]:
                    raise _invalid_plan(f"行程中已经存在地点：{change.name}")
                pending_names[point.trip_day_id].discard(current_name)
                pending_names[point.trip_day_id].add(normalised)
            has_effect = _update_has_effect(point, change) or has_effect
        elif change.operation == "delete":
            has_effect = True
        elif change.operation == "move":
            assert change.point_id is not None and change.target_day_id is not None
            point = point_map[change.point_id]
            current_points = points_by_day[point.trip_day_id]
            current_position = current_points.index(point) + 1
            is_same_day = point.trip_day_id == change.target_day_id
            requested_position = change.position or (
                len(points_by_day[change.target_day_id]) + (0 if is_same_day else 1)
            )
            if point.trip_day_id != change.target_day_id or requested_position != current_position:
                has_effect = True

    if not has_effect:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="adjustment_no_changes",
            message="AI 没有生成实际可执行的修改，请换一种更具体的说法",
        )


def apply_adjustment_plan(db: Session, trip: Trip, plan: AdjustmentPlan) -> list[dict[str, Any]]:
    days, points_by_day, point_map = _load_trip_state(db, trip.id)

    # Move all persisted positions out of the final range before inserts/moves.
    for points in points_by_day.values():
        for index, point in enumerate(points, start=1):
            point.sort_order = 1000 + index
    db.flush()

    changes: list[dict[str, Any]] = []
    for change in plan.changes:
        if change.operation == "add":
            assert change.day_id is not None and change.name is not None
            place_info = _lookup_place(change.name, trip.destination_name)
            point = TripPoint(
                id=uuid.uuid4(),
                trip_day_id=change.day_id,
                name=change.name.strip(),
                point_type=change.point_type or "spot",
                address=place_info.get("address"),
                latitude=place_info.get("latitude"),
                longitude=place_info.get("longitude"),
                start_time=change.start_time,
                end_time=change.end_time,
                notes=change.notes,
                sort_order=1000 + len(points_by_day[change.day_id]) + 1,
            )
            db.add(point)
            target_points = points_by_day[change.day_id]
            target_points.insert(_insert_index(change.position, len(target_points)), point)
            changes.append(
                {
                    "op": "add",
                    "day_id": str(change.day_id),
                    "point_id": str(point.id),
                    "value": _point_value(point),
                    "old_value": None,
                }
            )
        elif change.operation == "update":
            assert change.point_id is not None
            point = point_map[change.point_id]
            old_value = _point_value(point)
            for field in ("name", "point_type", "start_time", "end_time", "notes"):
                if field in change.model_fields_set:
                    value = getattr(change, field)
                    if field == "name" and isinstance(value, str):
                        value = value.strip()
                    setattr(point, field, value)
            name_changed = (
                "name" in change.model_fields_set
                and change.name
                and change.name != old_value["name"]
            )
            if name_changed:
                place_info = _lookup_place(change.name, trip.destination_name)
                point.address = place_info.get("address")
                point.latitude = place_info.get("latitude")
                point.longitude = place_info.get("longitude")
            new_value = _point_value(point)
            if new_value != old_value:
                changes.append(
                    {
                        "op": "update",
                        "day_id": str(point.trip_day_id),
                        "point_id": str(point.id),
                        "value": new_value,
                        "old_value": old_value,
                    }
                )
        elif change.operation == "delete":
            assert change.point_id is not None
            point = point_map[change.point_id]
            old_value = _point_value(point)
            points_by_day[point.trip_day_id].remove(point)
            db.delete(point)
            changes.append(
                {
                    "op": "delete",
                    "day_id": str(point.trip_day_id),
                    "point_id": str(point.id),
                    "value": None,
                    "old_value": old_value,
                }
            )
        elif change.operation == "move":
            assert change.point_id is not None and change.target_day_id is not None
            point = point_map[change.point_id]
            old_day_id = point.trip_day_id
            source_points = points_by_day[old_day_id]
            old_position = source_points.index(point) + 1
            source_points.remove(point)
            target_points = points_by_day[change.target_day_id]
            new_index = _insert_index(change.position, len(target_points))
            target_points.insert(new_index, point)
            point.trip_day_id = change.target_day_id
            if old_day_id != change.target_day_id or old_position != new_index + 1:
                changes.append(
                    {
                        "op": "move",
                        "day_id": str(old_day_id),
                        "point_id": str(point.id),
                        "value": {
                            "target_day_id": str(change.target_day_id),
                            "position": new_index + 1,
                        },
                        "old_value": {"day_id": str(old_day_id), "position": old_position},
                    }
                )

    if not changes:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="adjustment_no_changes",
            message="AI 没有生成实际可执行的修改，请换一种更具体的说法",
        )

    for day_id, points in points_by_day.items():
        for index, point in enumerate(points, start=1):
            point.trip_day_id = day_id
            point.sort_order = index
    db.flush()
    return changes


def _load_trip_state(
    db: Session,
    trip_id: UUID,
) -> tuple[list[TripDay], dict[UUID, list[TripPoint]], dict[UUID, TripPoint]]:
    days = list(
        db.scalars(select(TripDay).where(TripDay.trip_id == trip_id).order_by(TripDay.day_index))
    )
    if not days:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="adjustment_no_itinerary",
            message="当前行程还没有可调整的内容",
        )
    points_by_day = {day.id: _list_points(db, day.id) for day in days}
    point_map = {point.id: point for points in points_by_day.values() for point in points}
    return days, points_by_day, point_map


def _list_points(db: Session, day_id: UUID) -> list[TripPoint]:
    return list(
        db.scalars(
            select(TripPoint)
            .where(TripPoint.trip_day_id == day_id)
            .order_by(TripPoint.sort_order)
        )
    )


def _validate_change_references(
    change: AdjustmentChange,
    day_map: dict[UUID, TripDay],
    point_map: dict[UUID, TripPoint],
) -> None:
    if change.day_id is not None and change.day_id not in day_map:
        raise _invalid_plan("AI 返回了不存在的日期 ID")
    if change.target_day_id is not None and change.target_day_id not in day_map:
        raise _invalid_plan("AI 返回了不存在的目标日期 ID")
    if change.point_id is not None and change.point_id not in point_map:
        raise _invalid_plan("AI 返回了不存在的行程点 ID")


def _affected_day_id(change: AdjustmentChange, point_map: dict[UUID, TripPoint]) -> UUID:
    if change.operation == "add":
        assert change.day_id is not None
        return change.day_id
    assert change.point_id is not None
    return point_map[change.point_id].trip_day_id


def _update_has_effect(point: TripPoint, change: AdjustmentChange) -> bool:
    for field in ("name", "point_type", "start_time", "end_time", "notes"):
        if field in change.model_fields_set:
            value = getattr(change, field)
            if field == "name" and isinstance(value, str):
                value = value.strip()
            if getattr(point, field) != value:
                return True
    return False


def _validate_name(name: str) -> None:
    value = name.strip()
    if not value or value.startswith("[AI调整]"):
        raise _invalid_plan("AI 返回了无效地点名称")


def _normalise_name(name: str) -> str:
    return "".join(name.lower().split())


def _insert_index(position: int | None, length: int) -> int:
    if position is None:
        return length
    return max(0, min(position - 1, length))


def _point_value(point: TripPoint) -> dict[str, Any]:
    return {
        "name": point.name,
        "point_type": point.point_type,
        "start_time": point.start_time.isoformat(timespec="minutes") if point.start_time else None,
        "end_time": point.end_time.isoformat(timespec="minutes") if point.end_time else None,
        "notes": point.notes,
    }


def _lookup_place(place_name: str, city: str) -> dict[str, Any]:
    try:
        client = get_amap_client()
        if not client.available:
            return {}
        pois = client.search_pois(place_name, city=city, page_size=1)
        if pois:
            poi = pois[0]
            longitude, latitude = _parse_location(poi.get("location"))
            return {
                "address": poi.get("address") or None,
                "latitude": latitude,
                "longitude": longitude,
            }
        geocode = client.geocode(place_name, city=city)
        if geocode:
            longitude, latitude = _parse_location(geocode.get("location"))
            return {
                "address": geocode.get("formatted_address") or None,
                "latitude": latitude,
                "longitude": longitude,
            }
    except Exception:
        return {}
    return {}


def _parse_location(value: object) -> tuple[float | None, float | None]:
    if not isinstance(value, str) or "," not in value:
        return None, None
    longitude, latitude = value.split(",", 1)
    try:
        return float(longitude), float(latitude)
    except ValueError:
        return None, None


def _invalid_plan(message: str) -> AppException:
    return AppException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="adjustment_plan_invalid",
        message=message,
    )
