from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import status as http_status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.generation_job import GenerationJob


def _generate_job_id() -> str:
    return f"job_{uuid.uuid4().hex}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_job(
    db: Session,
    job_type: str,
    user_id: UUID | None,
    input_data: dict[str, Any] | None,
) -> GenerationJob:
    """创建 pending 状态的生成任务。"""
    job = GenerationJob(
        job_id=_generate_job_id(),
        job_type=job_type,
        status="pending",
        user_id=user_id,
        input_data=input_data or {},
        progress=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> GenerationJob:
    """查询任务，不存在抛 AppException(404)。"""
    job = db.scalar(select(GenerationJob).where(GenerationJob.job_id == job_id))
    if job is None:
        raise AppException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            code=ErrorCode.JOB_NOT_FOUND,
            message="任务不存在",
        )
    return job


def update_job_progress(db: Session, job_id: str, progress: int) -> GenerationJob:
    """更新任务进度。"""
    job = get_job(db, job_id)
    if job.started_at is None:
        job.started_at = _now()
    job.progress = max(0, min(100, progress))
    db.commit()
    db.refresh(job)
    return job


def complete_job(db: Session, job_id: str, output_data: dict[str, Any]) -> GenerationJob:
    """标记任务为已完成并写入输出数据。"""
    job = get_job(db, job_id)
    if job.started_at is None:
        job.started_at = _now()
    job.status = "completed"
    job.progress = 100
    job.output_data = output_data
    job.completed_at = _now()
    db.commit()
    db.refresh(job)
    return job


def fail_job(db: Session, job_id: str, error_message: str) -> GenerationJob:
    """标记任务为失败并写入错误信息。"""
    job = get_job(db, job_id)
    if job.started_at is None:
        job.started_at = _now()
    job.status = "failed"
    job.error_message = error_message
    job.completed_at = _now()
    db.commit()
    db.refresh(job)
    return job


def list_jobs(
    db: Session,
    user_id: UUID | None,
    page: int,
    page_size: int,
) -> tuple[list[GenerationJob], int]:
    """分页查询任务列表，返回 (jobs, total)。"""
    stmt = select(GenerationJob)
    count_stmt = select(func.count()).select_from(GenerationJob)
    if user_id is not None:
        stmt = stmt.where(GenerationJob.user_id == user_id)
        count_stmt = count_stmt.where(GenerationJob.user_id == user_id)
    total = db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(GenerationJob.created_at.desc(), GenerationJob.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    jobs = list(db.scalars(stmt))
    return jobs, total
