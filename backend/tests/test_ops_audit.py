from contextlib import contextmanager
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.main import app
from app.models.base import Base


def _factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(
        engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON")
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def client() -> Generator[TestClient, None, None]:
    factory = _factory()

    def db_override():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = db_override
    app.dependency_overrides[get_settings] = lambda: Settings(
        OPS_SERVICE_TOKEN="test-service-token-1234", RATE_LIMIT_ENABLED=False
    )
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.clear()


def test_account_task_remains_visible_after_trip_delete():
    with client() as value:
        registration = value.post(
            "/api/v1/auth/register",
            json={
                "email": "audit@example.com",
                "username": "audit-user",
                "display_name": "审计用户",
                "password": "password123",
            },
        )
        assert registration.status_code == 201
        user_id = registration.json()["data"]["user"]["id"]
        token = registration.json()["data"]["token"]["access_token"]
        auth = {"Authorization": f"Bearer {token}"}
        trip = value.post(
            f"/api/v1/users/{user_id}/trips",
            headers=auth,
            json={"title": "删除后仍可查", "destination_name": "杭州", "status": "upcoming"},
        )
        assert trip.status_code == 201
        trip_id = trip.json()["data"]["id"]
        assert (
            value.delete(f"/api/v1/users/{user_id}/trips/{trip_id}", headers=auth).status_code
            == 204
        )

        # Soft-deleted trips must disappear from every normal read path while
        # remaining available through the separately authenticated audit API.
        trip_list = value.get(f"/api/v1/users/{user_id}/trips", headers=auth)
        assert trip_list.status_code == 200
        assert trip_list.json()["data"]["items"] == []
        assert trip_list.json()["data"]["meta"]["total"] == 0
        assert (
            value.get(
                f"/api/v1/users/{user_id}/trips/{trip_id}", headers=auth
            ).status_code
            == 404
        )
        assert value.get(f"/api/v1/trips/{trip_id}/outfits", headers=auth).status_code == 404
        assert value.get(f"/api/v1/trips/{trip_id}/versions", headers=auth).status_code == 404
        assert value.get(f"/api/v1/trips/{trip_id}/spots", headers=auth).status_code == 404
        search = value.get("/api/v1/search?keyword=删除后仍可查&type=destination", headers=auth)
        assert search.status_code == 200
        assert search.json()["data"]["total"] == 0

        service = {"X-Ops-Service-Token": "test-service-token-1234", "X-Ops-Admin": "tester"}
        assert value.get("/api/v1/ops/audit/accounts?q=audit@example.com").status_code == 401
        assert (
            value.get(
                "/api/v1/ops/audit/accounts?q=audit@example.com",
                headers={"X-Ops-Service-Token": "wrong-token"},
            ).status_code
            == 401
        )
        accounts = value.get("/api/v1/ops/audit/accounts?q=audit@example.com", headers=service)
        assert accounts.status_code == 200
        assert accounts.json()["data"]["items"][0]["deleted_task_count"] == 1
        tasks = value.get(
            f"/api/v1/ops/audit/accounts/{user_id}/tasks?status=deleted", headers=service
        )
        task = tasks.json()["data"]["items"][0]
        assert task["status"] == "deleted"
        detail = value.get(f"/api/v1/ops/audit/tasks/{task['task_id']}", headers=service)
        actions = [item["action_type"] for item in detail.json()["data"]["timeline"]]
        assert actions == ["trip_created", "task_deleted"]
