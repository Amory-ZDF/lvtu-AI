from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AdminAuditLog, AuditAction, AuditTask
from app.models.trip import Trip
from app.models.user import User


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def trip_summary(trip: Trip) -> dict[str, Any]:
    return {
        "title": trip.title,
        "destination": trip.destination_name,
        "status": trip.status,
        "start_date": trip.start_date.isoformat() if trip.start_date else None,
        "end_date": trip.end_date.isoformat() if trip.end_date else None,
    }


def find_task_for_trip(db: Session, trip_id: uuid.UUID) -> AuditTask | None:
    return db.scalar(select(AuditTask).where(AuditTask.trip_id == trip_id))


def ensure_trip_task(db: Session, trip: Trip, user: User) -> AuditTask:
    task = find_task_for_trip(db, trip.id)
    if task:
        return task
    now = datetime.now(UTC)
    task = AuditTask(
        task_id=_id("tsk"),
        task_type="trip_planning",
        title=trip.title,
        destination_summary=trip.destination_name,
        status="completed",
        user_id=user.id,
        username_snapshot=user.username,
        email_snapshot=user.email,
        display_name_snapshot=user.display_name,
        trip_id=trip.id,
        last_action_at=now,
    )
    db.add(task)
    db.flush()
    return task


def ensure_query_task(
    db: Session,
    user: User,
    *,
    requested_task_id: str | None,
    title: str,
    destination: str | None,
) -> AuditTask:
    task = None
    if requested_task_id:
        task = db.scalar(
            select(AuditTask).where(
                AuditTask.task_id == requested_task_id,
                AuditTask.user_id == user.id,
            )
        )
    if task:
        if destination and not task.destination_summary:
            task.destination_summary = destination
        return task
    now = datetime.now(UTC)
    task = AuditTask(
        task_id=_id("tsk"),
        task_type="trip_planning",
        title=title[:255],
        destination_summary=destination[:255] if destination else None,
        status="planning",
        user_id=user.id,
        username_snapshot=user.username,
        email_snapshot=user.email,
        display_name_snapshot=user.display_name,
        last_action_at=now,
    )
    db.add(task)
    db.flush()
    return task


def new_query_id() -> str:
    return _id("qry")


def append_action(
    db: Session,
    task: AuditTask,
    *,
    action_type: str,
    request_id: str | None,
    user: User | None = None,
    target_type: str = "trip",
    target_id: str | None = None,
    status: str = "success",
    before_summary: dict[str, Any] | None = None,
    after_summary: dict[str, Any] | None = None,
    query_id: str | None = None,
    job_id: str | None = None,
    error_code: str | None = None,
    error_message_safe: str | None = None,
) -> AuditAction:
    now = datetime.now(UTC)
    action = AuditAction(
        action_id=_id("act"),
        task_id=task.task_id,
        user_id=user.id if user else task.user_id,
        username_snapshot=user.username if user else task.username_snapshot,
        email_snapshot=user.email if user else task.email_snapshot,
        actor_type="user" if user else "system",
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        status=status,
        before_summary=before_summary or {},
        after_summary=after_summary or {},
        error_code=error_code,
        error_message_safe=error_message_safe,
        query_id=query_id,
        request_id=request_id,
        job_id=job_id,
        occurred_at=now,
    )
    task.last_action_at = now
    if status == "failed":
        task.error_count += 1
    if query_id:
        task.query_count += 1
    if job_id:
        task.generation_count += 1
    db.add(action)
    return action


def soft_delete_trip(
    db: Session,
    trip: Trip,
    user: User,
    *,
    request_id: str | None,
    reason: str = "用户删除",
) -> AuditTask:
    task = ensure_trip_task(db, trip, user)
    now = datetime.now(UTC)
    snapshot = trip_summary(trip)
    append_action(
        db,
        task,
        action_type="task_deleted",
        request_id=request_id,
        user=user,
        target_id=str(trip.id),
        before_summary=snapshot,
        after_summary={"status": "deleted"},
    )
    trip.deleted_at = now
    trip.deleted_by = user.id
    trip.deletion_reason = reason[:255]
    task.status = "deleted"
    task.deleted_at = now
    task.deleted_by = user.id
    task.deletion_reason = reason[:255]
    task.delete_snapshot = snapshot
    return task


def record_admin_access(
    db: Session,
    *,
    admin_identity: str,
    action_type: str,
    request_id: str | None,
    search_term: str | None = None,
    target_task_id: str | None = None,
) -> None:
    masked = None
    if search_term:
        masked = search_term[:2] + "***" if len(search_term) > 2 else "***"
    db.add(
        AdminAuditLog(
            admin_identity=admin_identity[:255],
            action_type=action_type,
            search_term_masked=masked,
            target_task_id=target_task_id,
            request_id=request_id,
            occurred_at=datetime.now(UTC),
        )
    )
