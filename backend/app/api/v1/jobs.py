from __future__ import annotations

import asyncio
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.responses import paginated_response, success_response
from app.db.session import get_db_session
from app.middleware.auth import get_current_user_optional
from app.models.generation_job import GenerationJob
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.job import JobRead
from app.services.job_service import get_job, list_jobs

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]


@router.get("/{job_id}", tags=["jobs"])
def get_job_detail(
    job_id: str,
    request: Request,
    db: SessionDep,
) -> ApiResponse:
    job = get_job(db, job_id)
    return success_response(JobRead.model_validate(job).model_dump(mode="json"), request)


@router.get("/{job_id}/stream", tags=["jobs"])
async def stream_job(
    job_id: str,
    db: SessionDep,
) -> StreamingResponse:
    """SSE 流式推送任务进度。

    每 1 秒推送一次 `event: progress`，任务完成或失败时推送 `event: complete` 并关闭连接。
    """
    # 先校验任务存在，不存在直接抛 AppException(404)
    get_job(db, job_id)

    async def event_generator():
        while True:
            # 刷新会话缓存以读取最新状态
            db.expire_all()
            job = db.scalar(select(GenerationJob).where(GenerationJob.job_id == job_id))
            if job is None:
                break

            payload = {
                "job_id": job.job_id,
                "status": job.status,
                "progress": job.progress,
            }
            yield f"event: progress\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

            if job.status in ("completed", "failed"):
                final = {
                    "job_id": job.job_id,
                    "status": job.status,
                    "progress": job.progress,
                    "output_data": job.output_data,
                    "error_message": job.error_message,
                }
                yield f"event: complete\ndata: {json.dumps(final, ensure_ascii=False)}\n\n"
                return

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("", tags=["jobs"])
def list_jobs_endpoint(
    request: Request,
    db: SessionDep,
    current_user: CurrentUserOptional,
    user_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    target_user_id = user_id
    if target_user_id is None and current_user is not None:
        target_user_id = current_user.id

    jobs, total = list_jobs(db, target_user_id, page, page_size)
    items = [JobRead.model_validate(job).model_dump(mode="json") for job in jobs]
    return paginated_response(items, request, page=page, page_size=page_size, total=total)
