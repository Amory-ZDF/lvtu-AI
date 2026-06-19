from __future__ import annotations

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


def _get_trip_or_404(db: Session, trip_id: UUID) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_NOT_FOUND,
            message="行程不存在",
        )
    return trip


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

    for day in days:
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
        "summary": "已根据指令对行程进行调整。" if changes else "未识别到可调整的内容。",
    }
    job = complete_job(db, job.job_id, mock_diff)

    return success_response(
        {"job_id": job.job_id, "status": job.status, "output_data": job.output_data},
        request,
    )
