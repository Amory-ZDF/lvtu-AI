from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
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


def test_dashboard_rejects_non_whitelisted_user(monkeypatch) -> None:
    monkeypatch.setenv("ANALYTICS_ADMIN_EMAILS", "other@example.com")
    get_settings.cache_clear()
    try:
        with _build_client() as client:
            token = _register_user(client)
            response = client.get(
                "/api/v1/analytics/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 403
            assert response.json()["error"]["code"] == "analytics_forbidden"
    finally:
        get_settings.cache_clear()


def test_dashboard_returns_standard_product_analytics(monkeypatch) -> None:
    monkeypatch.setenv("ANALYTICS_ADMIN_EMAILS", "analytics@example.com")
    get_settings.cache_clear()
    try:
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
                            "event_name": "destination_recommendation_success",
                            "event_category": "conversion",
                            "page_path": "/start",
                            "metadata": {
                                "interests": ["自然", "拍照"],
                            },
                            "device_type": "desktop",
                        },
                        {
                            "visitor_id": "visitor-1",
                            "session_id": "session-1",
                            "event_name": "destination_selected",
                            "event_category": "selection",
                            "page_path": "/destinations",
                            "metadata": {
                                "destination_name": "大理",
                                "selection_label": "大理",
                            },
                            "device_type": "desktop",
                        },
                        {
                            "visitor_id": "visitor-1",
                            "session_id": "session-1",
                            "event_name": "route_option_selected",
                            "event_category": "selection",
                            "page_path": "/comparison",
                            "metadata": {
                                "option_id": "A",
                                "route_title": "经典路线",
                            },
                            "device_type": "desktop",
                        },
                        {
                            "visitor_id": "visitor-1",
                            "session_id": "session-1",
                            "event_name": "route_option_confirmed",
                            "event_category": "selection",
                            "page_path": "/comparison",
                            "metadata": {
                                "option_id": "A",
                                "route_title": "经典路线",
                            },
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
            assert "metric_cards" not in data
            assert "device_breakdown" not in data
            assert "recent_events" not in data

            assert data["funnel"][0]["key"] == "home_view"
            assert data["funnel"][0]["users"] == 1
            assert data["funnel"][2]["key"] == "destination_success"
            assert data["funnel"][2]["users"] == 1

            page = data["page_stays"][0]
            assert page["page_path"] == "/"
            assert page["views"] == 1
            assert page["avg_stay_seconds"] == 30
            assert page["p50_stay_seconds"] == 30

            button = data["page_buttons"][0]
            assert button["button_label"] == "开始你的行程"
            assert button["clicks"] == 1
            assert button["page_views"] == 1
            assert button["click_rate"] == 1

            groups = {group["key"]: group for group in data["selection_groups"]}
            assert groups["destination_selected"]["options"][0]["label"] == "大理"
            assert groups["route_option_selected"]["options"][0]["label"] == "经典路线"
            assert groups["route_option_confirmed"]["options"][0]["label"] == "经典路线"
            assert groups["interest_selected"]["options"][0]["count"] == 1
    finally:
        get_settings.cache_clear()
