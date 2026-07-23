from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.models.audit_log import AuditAction, AuditTask
from app.models.user import User
from app.services.audit_service import record_admin_access

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def require_ops_service(
    settings: SettingsDep,
    x_ops_service_token: Annotated[str | None, Header()] = None,
    x_ops_admin: Annotated[str | None, Header()] = None,
) -> str:
    expected = settings.ops_service_token
    if (
        not expected
        or not x_ops_service_token
        or not secrets.compare_digest(expected, x_ops_service_token)
    ):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="ops_unauthorized",
            message="运维服务凭据无效",
        )
    return (x_ops_admin or "lv-ops-console")[:255]


OpsIdentity = Annotated[str, Depends(require_ops_service)]


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _task_dict(task: AuditTask) -> dict:
    return {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "title": task.title,
        "destination": task.destination_summary,
        "status": task.status,
        "user_id": str(task.user_id) if task.user_id else None,
        "username": task.username_snapshot,
        "email": task.email_snapshot,
        "display_name": task.display_name_snapshot,
        "trip_id": str(task.trip_id) if task.trip_id else None,
        "query_count": task.query_count,
        "generation_count": task.generation_count,
        "error_count": task.error_count,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "last_action_at": task.last_action_at,
        "deleted_at": task.deleted_at,
        "deleted_by": str(task.deleted_by) if task.deleted_by else None,
        "deletion_reason": task.deletion_reason,
        "delete_snapshot": task.delete_snapshot,
    }


@router.get("/overview")
def overview(request: Request, db: SessionDep, admin: OpsIdentity):
    statuses = dict(
        db.execute(select(AuditTask.status, func.count()).group_by(AuditTask.status)).all()
    )
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    total_tasks = sum(statuses.values())
    total_actions = db.scalar(select(func.count()).select_from(AuditAction)) or 0
    failed_actions = (
        db.scalar(
            select(func.count()).select_from(AuditAction).where(AuditAction.status == "failed")
        )
        or 0
    )
    record_admin_access(
        db, admin_identity=admin, action_type="overview_viewed", request_id=_request_id(request)
    )
    db.commit()
    return success_response(
        {
            "users": total_users,
            "tasks": total_tasks,
            "actions": total_actions,
            "failed_actions": failed_actions,
            "task_statuses": statuses,
            "calculated_at": datetime.now(UTC),
        },
        request,
    )


@router.get("/accounts")
def search_accounts(
    request: Request,
    db: SessionDep,
    admin: OpsIdentity,
    q: str = Query(min_length=1, max_length=255),
    limit: int = Query(default=20, ge=1, le=100),
):
    pattern = f"%{q.strip()}%"
    users = list(
        db.scalars(
            select(User)
            .where(
                or_(
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                    User.display_name.ilike(pattern),
                )
            )
            .limit(limit)
        )
    )
    historical = list(
        db.scalars(
            select(AuditTask)
            .where(
                or_(
                    AuditTask.username_snapshot.ilike(pattern),
                    AuditTask.email_snapshot.ilike(pattern),
                    AuditTask.display_name_snapshot.ilike(pattern),
                )
            )
            .order_by(AuditTask.created_at.desc())
            .limit(limit * 2)
        )
    )
    items: dict[str, dict] = {}
    for user in users:
        items[str(user.id)] = {
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "account_status": "active",
        }
    for task in historical:
        key = str(task.user_id) if task.user_id else f"historical:{task.email_snapshot}"
        items.setdefault(
            key,
            {
                "user_id": str(task.user_id) if task.user_id else None,
                "username": task.username_snapshot,
                "email": task.email_snapshot,
                "display_name": task.display_name_snapshot,
                "account_status": "historical",
            },
        )
    for _key, item in items.items():
        predicates = (
            [AuditTask.user_id == UUID(item["user_id"])]
            if item["user_id"]
            else [AuditTask.email_snapshot == item["email"]]
        )
        counts = dict(
            db.execute(
                select(AuditTask.status, func.count()).where(*predicates).group_by(AuditTask.status)
            ).all()
        )
        item["task_count"] = sum(counts.values())
        item["deleted_task_count"] = counts.get("deleted", 0)
        item["failed_task_count"] = counts.get("failed", 0)
    record_admin_access(
        db,
        admin_identity=admin,
        action_type="account_searched",
        request_id=_request_id(request),
        search_term=q,
    )
    db.commit()
    return success_response({"items": list(items.values())[:limit]}, request)


@router.get("/accounts/{account_key}/tasks")
def account_tasks(
    account_key: str,
    request: Request,
    db: SessionDep,
    admin: OpsIdentity,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    try:
        predicate = AuditTask.user_id == UUID(account_key)
    except ValueError:
        predicate = AuditTask.email_snapshot == account_key
    filters = [predicate]
    if status_filter:
        filters.append(AuditTask.status == status_filter)
    total = db.scalar(select(func.count()).select_from(AuditTask).where(*filters)) or 0
    tasks = list(
        db.scalars(
            select(AuditTask)
            .where(*filters)
            .order_by(AuditTask.last_action_at.desc(), AuditTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    record_admin_access(
        db,
        admin_identity=admin,
        action_type="account_tasks_viewed",
        request_id=_request_id(request),
        search_term=account_key,
    )
    db.commit()
    return success_response(
        {
            "items": [_task_dict(item) for item in tasks],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        request,
    )


@router.get("/tasks/{task_id}")
def task_detail(task_id: str, request: Request, db: SessionDep, admin: OpsIdentity):
    task = db.scalar(select(AuditTask).where(AuditTask.task_id == task_id))
    if not task:
        raise AppException(status_code=404, code="task_not_found", message="审计任务不存在")
    actions = list(
        db.scalars(
            select(AuditAction)
            .where(AuditAction.task_id == task_id)
            .order_by(AuditAction.occurred_at)
        )
    )
    timeline = [
        {
            "action_id": item.action_id,
            "action_type": item.action_type,
            "status": item.status,
            "actor_type": item.actor_type,
            "target_type": item.target_type,
            "target_id": item.target_id,
            "before_summary": item.before_summary,
            "after_summary": item.after_summary,
            "error_code": item.error_code,
            "error_message": item.error_message_safe,
            "query_id": item.query_id,
            "request_id": item.request_id,
            "job_id": item.job_id,
            "trace_id": item.trace_id,
            "duration_ms": item.duration_ms,
            "occurred_at": item.occurred_at,
        }
        for item in actions
    ]
    record_admin_access(
        db,
        admin_identity=admin,
        action_type="task_detail_viewed",
        request_id=_request_id(request),
        target_task_id=task_id,
    )
    db.commit()
    return success_response({"task": _task_dict(task), "timeline": timeline}, request)
