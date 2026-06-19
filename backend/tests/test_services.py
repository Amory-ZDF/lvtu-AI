from __future__ import annotations

import os
import uuid
from collections.abc import Generator

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.exceptions import AppException
from app.db.base import *  # noqa: F403
from app.models.base import Base
from app.models.user import User
from app.services import job_service, notification_service


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


def _create_user(db: Session) -> User:
    """创建并返回一个测试用户。"""
    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        username=f"test_{uuid.uuid4().hex[:8]}",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# -----------------------------
# job_service tests
# -----------------------------


def test_create_job(db_session: Session) -> None:
    user = _create_user(db_session)
    input_data = {"destination": "京都", "duration_days": 4}
    job = job_service.create_job(
        db_session, job_type="route", user_id=user.id, input_data=input_data
    )

    assert job.job_id.startswith("job_")
    assert job.job_type == "route"
    assert job.status == "pending"
    assert job.progress == 0
    assert job.user_id == user.id
    assert job.input_data == input_data
    assert job.started_at is None
    assert job.completed_at is None


def test_create_job_without_user(db_session: Session) -> None:
    job = job_service.create_job(
        db_session, job_type="destination", user_id=None, input_data=None
    )
    assert job.user_id is None
    assert job.input_data == {}


def test_get_job_success(db_session: Session) -> None:
    created = job_service.create_job(
        db_session, job_type="route", user_id=None, input_data={}
    )
    fetched = job_service.get_job(db_session, created.job_id)
    assert fetched.id == created.id
    assert fetched.job_id == created.job_id


def test_get_job_not_found(db_session: Session) -> None:
    with pytest.raises(AppException) as exc_info:
        job_service.get_job(db_session, "job_nonexistent")
    assert exc_info.value.status_code == 404


def test_update_job_progress(db_session: Session) -> None:
    job = job_service.create_job(
        db_session, job_type="route", user_id=None, input_data={}
    )
    updated = job_service.update_job_progress(db_session, job.job_id, 50)

    assert updated.progress == 50
    assert updated.started_at is not None
    assert updated.status == "pending"


def test_update_job_progress_clamps_value(db_session: Session) -> None:
    job = job_service.create_job(
        db_session, job_type="route", user_id=None, input_data={}
    )
    updated = job_service.update_job_progress(db_session, job.job_id, 150)
    assert updated.progress == 100

    updated = job_service.update_job_progress(db_session, job.job_id, -10)
    assert updated.progress == 0


def test_complete_job(db_session: Session) -> None:
    job = job_service.create_job(
        db_session, job_type="route", user_id=None, input_data={}
    )
    output_data = {"route": "京都-岚山-嵐山"}
    completed = job_service.complete_job(db_session, job.job_id, output_data)

    assert completed.status == "completed"
    assert completed.progress == 100
    assert completed.output_data == output_data
    assert completed.completed_at is not None
    assert completed.started_at is not None


def test_fail_job(db_session: Session) -> None:
    job = job_service.create_job(
        db_session, job_type="route", user_id=None, input_data={}
    )
    failed = job_service.fail_job(db_session, job.job_id, "AI 服务超时")

    assert failed.status == "failed"
    assert failed.error_message == "AI 服务超时"
    assert failed.completed_at is not None


def test_list_jobs(db_session: Session) -> None:
    user = _create_user(db_session)
    job_service.create_job(
        db_session, job_type="route", user_id=user.id, input_data={}
    )
    job_service.create_job(
        db_session, job_type="destination", user_id=user.id, input_data={}
    )
    job_service.create_job(
        db_session, job_type="route", user_id=None, input_data={}
    )

    jobs, total = job_service.list_jobs(db_session, user.id, page=1, page_size=10)
    assert total == 2
    assert len(jobs) == 2

    all_jobs, all_total = job_service.list_jobs(db_session, None, page=1, page_size=10)
    assert all_total == 3


# -----------------------------
# notification_service tests
# -----------------------------


def test_create_notification(db_session: Session) -> None:
    user = _create_user(db_session)
    notification = notification_service.create_notification(
        db_session,
        user_id=user.id,
        type="system",
        title="欢迎加入",
        content="感谢注册旅图",
        related_resource_type="trip",
        related_resource_id="abc-123",
    )

    assert notification.user_id == user.id
    assert notification.type == "system"
    assert notification.title == "欢迎加入"
    assert notification.content == "感谢注册旅图"
    assert notification.is_read is False
    assert notification.related_resource_type == "trip"
    assert notification.related_resource_id == "abc-123"


def test_list_notifications(db_session: Session) -> None:
    user = _create_user(db_session)
    other_user = _create_user(db_session)
    notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="通知1"
    )
    notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="通知2"
    )
    notification_service.create_notification(
        db_session, user_id=other_user.id, type="system", title="其他用户通知"
    )

    notifications, total = notification_service.list_notifications(
        db_session, user.id, page=1, page_size=10
    )
    assert total == 2
    assert len(notifications) == 2


def test_list_notifications_unread_only(db_session: Session) -> None:
    user = _create_user(db_session)
    n1 = notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="未读"
    )
    n2 = notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="已读"
    )
    notification_service.mark_as_read(db_session, n2.id, user.id)

    notifications, total = notification_service.list_notifications(
        db_session, user.id, page=1, page_size=10, unread_only=True
    )
    assert total == 1
    assert notifications[0].id == n1.id


def test_mark_as_read(db_session: Session) -> None:
    user = _create_user(db_session)
    notification = notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="测试"
    )

    marked = notification_service.mark_as_read(db_session, notification.id, user.id)
    assert marked.is_read is True


def test_mark_as_read_not_found(db_session: Session) -> None:
    user = _create_user(db_session)
    with pytest.raises(AppException) as exc_info:
        notification_service.mark_as_read(db_session, uuid.uuid4(), user.id)
    assert exc_info.value.status_code == 404


def test_mark_as_read_wrong_user(db_session: Session) -> None:
    user = _create_user(db_session)
    other_user = _create_user(db_session)
    notification = notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="测试"
    )

    with pytest.raises(AppException):
        notification_service.mark_as_read(db_session, notification.id, other_user.id)


def test_mark_all_as_read(db_session: Session) -> None:
    user = _create_user(db_session)
    notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="通知1"
    )
    notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="通知2"
    )
    notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="通知3"
    )

    count = notification_service.mark_all_as_read(db_session, user.id)
    assert count == 3

    unread_count = notification_service.get_unread_count(db_session, user.id)
    assert unread_count == 0


def test_get_unread_count(db_session: Session) -> None:
    user = _create_user(db_session)
    notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="通知1"
    )
    notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="通知2"
    )
    n3 = notification_service.create_notification(
        db_session, user_id=user.id, type="system", title="通知3"
    )
    notification_service.mark_as_read(db_session, n3.id, user.id)

    count = notification_service.get_unread_count(db_session, user.id)
    assert count == 2
