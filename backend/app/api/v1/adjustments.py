from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.api.v1.core_business import _create_version_snapshot
from app.core.config import Settings, get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.middleware.auth import get_current_user_optional
from app.models.trip import Trip
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.job import AdjustmentRequest
from app.services.adjustment_service import (
    apply_adjustment_plan,
    generate_adjustment_plan,
    serialize_current_itinerary,
    validate_adjustment_plan,
)
from app.services.job_service import create_job, fail_job, update_job_progress

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _get_trip_or_404(db: Session, trip_id: UUID) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None or trip.deleted_at is not None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.TRIP_NOT_FOUND,
            message="行程不存在",
        )
    return trip


def _enforce_trip_owner(current_user: User | None, trip: Trip) -> None:
    if current_user is not None and current_user.id != trip.user_id:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message="无权修改该行程",
        )


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
    settings: SettingsDep,
) -> ApiResponse:
    """Use an LLM to plan validated itinerary changes and apply them atomically."""
    trip = _get_trip_or_404(db, trip_id)
    _enforce_trip_owner(current_user, trip)
    instruction = payload.instruction.strip()
    if not instruction:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ErrorCode.VALIDATION_ERROR,
            message="请输入需要修改的内容",
        )

    input_data = {
        "trip_id": str(trip_id),
        "instruction": instruction,
        "target_day_id": str(payload.target_day_id) if payload.target_day_id else None,
    }
    job = create_job(db, "trip_adjustment", trip.user_id, input_data)
    update_job_progress(db, job.job_id, 10)

    try:
        current_itinerary = serialize_current_itinerary(db, trip)
        plan = generate_adjustment_plan(
            settings,
            current_itinerary,
            instruction,
            payload.target_day_id,
        )
        validate_adjustment_plan(db, trip, plan, payload.target_day_id)
        update_job_progress(db, job.job_id, 65)

        snapshot = _create_version_snapshot(
            db,
            trip_id,
            note="AI 调整行程前",
            created_by=current_user.id if current_user else None,
        )
        if snapshot is None:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="trip_version_failed",
                message="无法创建修改前版本，行程未发生变化",
            )

        changes = apply_adjustment_plan(db, trip, plan)
        output_data = {
            "trip_id": str(trip_id),
            "instruction": instruction,
            "changes": changes,
            "summary": plan.summary,
        }
        now = datetime.now(timezone.utc)
        job.status = "completed"
        job.progress = 100
        job.output_data = output_data
        job.error_message = None
        job.completed_at = now
        if job.started_at is None:
            job.started_at = now
        db.commit()
        db.refresh(job)
    except AppException as exc:
        db.rollback()
        fail_job(db, job.job_id, exc.message)
        raise
    except Exception as exc:
        db.rollback()
        fail_job(db, job.job_id, "AI 调整行程失败")
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 调整行程失败，原行程未发生变化",
        ) from exc

    return success_response(
        {
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "output_data": job.output_data,
        },
        request,
    )
