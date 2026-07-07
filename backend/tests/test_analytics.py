from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import *  # noqa: F403
from app.db.session import get_db_session
from app.main import app
from app.models.base import Base


def _build_test_session_factory() -> sessionmaker[Session]:
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
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def _build_client() -> Generator[TestClient, None, None]:
    testing_session_local = _build_test_session_factory()

    def override_get_db_session() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _register_user(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "analytics@example.com",
            "username": "analytics",
            "password": "supersecret",
            "display_name": "Analytics Admin",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["token"]["access_token"]


def test_ingest_analytics_events_anonymously() -> None:
    with _build_client() as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "events": [
                    {
                        "visitor_id": "visitor-1",
                        "session_id": "session-1",
                        "event_name": "page_view",
                        "event_category": "page",
                        "page_path": "/",
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json()["data"]["accepted"] == 1


def test_dashboard_requires_login() -> None:
    with _build_client() as client:
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 401


def test_dashboard_aggregates_core_metrics() -> None:
    with _build_client() as client:
        token = _register_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        ingest = client.post(
            "/api/v1/analytics/events",
            headers=headers,
            json={
                "events": [
                    {
                        "visitor_id": "visitor-1",
                        "session_id": "session-1",
                        "event_name": "page_view",
                        "event_category": "page",
                        "page_path": "/",
                        "device_type": "desktop",
                    },
                    {
                        "visitor_id": "visitor-1",
                        "session_id": "session-1",
                        "event_name": "button_click",
                        "event_category": "click",
                        "page_path": "/",
                        "element_text": "开始你的行程",
                        "device_type": "desktop",
                    },
                    {
                        "visitor_id": "visitor-1",
                        "session_id": "session-1",
                        "event_name": "page_leave",
                        "event_category": "engagement",
                        "page_path": "/",
                        "duration_ms": 30000,
                        "device_type": "desktop",
                    },
                ]
            },
        )
        assert ingest.status_code == 200

        response = client.get("/api/v1/analytics/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        cards = {card["key"]: card["value"] for card in data["metric_cards"]}
        assert cards["unique_visitors"] == 1
        assert cards["page_views"] == 1
        assert cards["avg_stay_seconds"] == 30
        assert data["top_buttons"][0]["label"] == "开始你的行程"
        assert data["top_pages"][0]["page_path"] == "/"
