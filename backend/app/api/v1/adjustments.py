from __future__ import annotations

import re
from datetime import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.integrations.amap.client import get_amap_client
from app.middleware.auth import get_current_user_optional
from app.models.trip import Trip
from app.models.trip_day import TripDay
from app.models.trip_point import TripPoint
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.job import AdjustmentRequest
from app.services.job_service import complete_job, create_job

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]

_DAY_NUMBERS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}

_PLACE_PATTERNS = [
    r"(?:我要去|我想去|想去|去一下|加上|加入|新增|增加|添加|安排|打卡|途经|顺路去)(?P<place>[^，。,.!！?？；;\n]{2,30})",
    r"(?:改成|改为|换成|替换为)(?P<place>[^，。,.!！?？；;\n]{2,30})",
]


def _get_trip_or_404(db: Session, trip_id: UUID) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_NOT_FOUND,
            message="行程不存在",
        )
    return trip


def _parse_day_number(raw: str) -> int | None:
    if raw.isdigit():
        return int(raw)
    if raw in _DAY_NUMBERS:
        return _DAY_NUMBERS[raw]
    if raw.startswith("十") and len(raw) == 2:
        return 10 + (_DAY_NUMBERS.get(raw[1]) or 0)
    if raw.endswith("十") and len(raw) == 2:
        return (_DAY_NUMBERS.get(raw[0]) or 0) * 10
    if "十" in raw and len(raw) == 3:
        return (_DAY_NUMBERS.get(raw[0]) or 0) * 10 + (_DAY_NUMBERS.get(raw[2]) or 0)
    return None


def _target_day_index(instruction: str) -> int | None:
    match = re.search(r"第?([一二两三四五六七八九十\d]{1,3})天", instruction)
    if not match:
        return None
    return _parse_day_number(match.group(1))


def _clean_place_name(value: str) -> str:
    place = value.strip(" ，。,.!！?？；;、")
    place = re.sub(r"(附近|周边|看看|逛逛|玩一下|玩|拍照|打卡|这个地方|一下|吧)$", "", place)
    return place.strip(" ，。,.!！?？；;、")


def _extract_place_name(instruction: str) -> str | None:
    for pattern in _PLACE_PATTERNS:
        match = re.search(pattern, instruction)
        if match:
            place = _clean_place_name(match.group("place"))
            if len(place) >= 2:
                return place
    return None


def _time_from_instruction(instruction: str, point_count: int) -> time:
    instruction_lower = instruction.lower()
    if "早上" in instruction or "上午" in instruction or "morning" in instruction_lower:
        return time(9, 30)
    if "下午" in instruction or "afternoon" in instruction_lower:
        return time(14, 30)
    if "晚上" in instruction or "夜间" in instruction or "evening" in instruction_lower:
        return time(19, 0)
    slots = [time(9, 30), time(11, 0), time(14, 30), time(16, 30), time(19, 0)]
    return slots[min(point_count, len(slots) - 1)]


def _resolve_day(
    days: list[TripDay],
    target_day_id: UUID | None,
    instruction: str,
) -> TripDay | None:
    if target_day_id is not None:
        return next((day for day in days if day.id == target_day_id), None)
    day_index = _target_day_index(instruction)
    if day_index is not None:
        return next((day for day in days if day.day_index == day_index), None)
    return days[0] if days else None


def _lookup_place(place_name: str) -> dict:
    """Best-effort POI lookup. Failure should not block user-requested edits."""
    try:
        client = get_amap_client()
        if not client.available:
            return {}
        pois = client.search_pois(place_name, page_size=1)
        if pois:
            poi = pois[0]
            lng, lat = _parse_location(poi.get("location"))
            return {
                "address": poi.get("address") or None,
                "latitude": lat,
                "longitude": lng,
            }
        geocode = client.geocode(place_name)
        if geocode:
            lng, lat = _parse_location(geocode.get("location"))
            return {
                "address": geocode.get("formatted_address") or None,
                "latitude": lat,
                "longitude": lng,
            }
    except Exception:
        return {}
    return {}


def _parse_location(value: object) -> tuple[float | None, float | None]:
    if not isinstance(value, str) or "," not in value:
        return None, None
    lng_text, lat_text = value.split(",", 1)
    try:
        return float(lng_text), float(lat_text)
    except ValueError:
        return None, None


def _add_requested_place(
    db: Session,
    day: TripDay,
    place_name: str,
    instruction: str,
    day_idx: int,
) -> dict:
    points = list(
        db.scalars(
            select(TripPoint)
            .where(TripPoint.trip_day_id == day.id)
            .order_by(TripPoint.sort_order)
        )
    )
    place_info = _lookup_place(place_name)
    next_order = (points[-1].sort_order + 1) if points else 1
    new_point = TripPoint(
        trip_day_id=day.id,
        name=place_name,
        point_type="spot",
        address=place_info.get("address"),
        latitude=place_info.get("latitude"),
        longitude=place_info.get("longitude"),
        start_time=_time_from_instruction(instruction, len(points)),
        sort_order=next_order,
        notes=f"根据你的调整需求新增：{place_name}。出发前建议复核开放时间、门票和实时交通。",
    )
    db.add(new_point)
    db.flush()
    return {
        "op": "add",
        "path": f"/days/{day_idx}/points/{len(points)}",
        "value": place_name,
        "old_value": None,
    }


def _adjustment_summary(changes: list[dict]) -> str:
    if not changes:
        return "未识别到可调整的内容。"
    added_places = [
        str(change.get("value"))
        for change in changes
        if change.get("op") == "add" and change.get("value")
    ]
    if added_places:
        return f"已新增行程点：{'、'.join(added_places)}。"
    return "已根据指令对行程进行调整。"


def _apply_instruction(
    db: Session,
    trip_id: UUID,
    instruction: str,
    target_day_id: UUID | None,
) -> list[dict]:
    """根据指令简单修改行程数据，返回变更描述列表。"""
    day_stmt = select(TripDay).where(TripDay.trip_id == trip_id)
    if target_day_id is not None:
        day_stmt = day_stmt.where(TripDay.id == target_day_id)
    day_stmt = day_stmt.order_by(TripDay.day_index)
    days = list(db.scalars(day_stmt))

    changes: list[dict] = []
    instruction_lower = instruction.lower()
    requested_place = _extract_place_name(instruction)
    target_day = _resolve_day(days, target_day_id, instruction)
    if requested_place and target_day is not None:
        day_idx = target_day.day_index - 1 if target_day.day_index >= 1 else 0
        return [_add_requested_place(db, target_day, requested_place, instruction, day_idx)]

    for day in days:
        if target_day is not None and day.id != target_day.id:
            continue
        point_stmt = (
            select(TripPoint)
            .where(TripPoint.trip_day_id == day.id)
            .order_by(TripPoint.sort_order)
        )
        points = list(db.scalars(point_stmt))
        if not points:
            continue

        first_point = points[0]
        day_idx = day.day_index - 1 if day.day_index >= 1 else 0

        if "早上" in instruction or "上午" in instruction or "morning" in instruction_lower:
            new_time = time(8, 0)
            old_time = first_point.start_time
            first_point.start_time = new_time
            changes.append(
                {
                    "op": "replace",
                    "path": f"/days/{day_idx}/points/0/start_time",
                    "value": new_time.isoformat(),
                    "old_value": old_time.isoformat() if old_time else None,
                }
            )
        elif "下午" in instruction or "afternoon" in instruction_lower:
            new_time = time(14, 0)
            old_time = first_point.start_time
            first_point.start_time = new_time
            changes.append(
                {
                    "op": "replace",
                    "path": f"/days/{day_idx}/points/0/start_time",
                    "value": new_time.isoformat(),
                    "old_value": old_time.isoformat() if old_time else None,
                }
            )
        elif "晚上" in instruction or "夜间" in instruction or "evening" in instruction_lower:
            new_time = time(19, 0)
            old_time = first_point.start_time
            first_point.start_time = new_time
            changes.append(
                {
                    "op": "replace",
                    "path": f"/days/{day_idx}/points/0/start_time",
                    "value": new_time.isoformat(),
                    "old_value": old_time.isoformat() if old_time else None,
                }
            )
        else:
            old_name = first_point.name
            new_name = f"[AI调整] {old_name}"
            first_point.name = new_name
            changes.append(
                {
                    "op": "replace",
                    "path": f"/days/{day_idx}/points/0/name",
                    "value": new_name,
                    "old_value": old_name,
                }
            )

    return changes


@router.post(
    "/trips/{trip_id}/adjustments",
    status_code=status.HTTP_201_CREATED,
    tags=["adjustments"],
)
def create_adjustment(
    trip_id: UUID,
    payload: AdjustmentRequest,
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
) -> ApiResponse:
    """自然语言改写行程接口。

    创建 adjustment 类型的生成任务，根据指令简单修改行程数据并返回 diff。
    """
    _get_trip_or_404(db, trip_id)

    input_data = {
        "trip_id": str(trip_id),
        "instruction": payload.instruction,
        "target_day_id": str(payload.target_day_id) if payload.target_day_id else None,
    }
    job = create_job(db, "adjustment", None, input_data)

    # 根据指令实际修改行程数据
    changes = _apply_instruction(db, trip_id, payload.instruction, payload.target_day_id)
    db.commit()

    mock_diff = {
        "trip_id": str(trip_id),
        "instruction": payload.instruction,
        "target_day_id": str(payload.target_day_id) if payload.target_day_id else None,
        "changes": changes,
        "summary": _adjustment_summary(changes),
    }
    job = complete_job(db, job.job_id, mock_diff)

    return success_response(
        {"job_id": job.job_id, "status": job.status, "output_data": job.output_data},
        request,
    )
