from __future__ import annotations

import os
import uuid
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


def _create_user_and_trip(client: TestClient) -> tuple[str, str]:
    """创建用户和行程，返回 (user_id, trip_id)。"""
    user_id = str(uuid.uuid4())
    client.put(
        f"/api/v1/users/{user_id}/profile",
        json={
            "email": f"user_{user_id}@example.com",
            "username": f"user_{user_id}",
            "display_name": "Test User",
        },
    )
    trip_response = client.post(
        f"/api/v1/users/{user_id}/trips",
        json={
            "title": "测试行程",
            "destination_name": "京都",
            "status": "draft",
        },
    )
    trip_id = trip_response.json()["data"]["id"]
    return user_id, trip_id


def test_get_job_not_found() -> None:
    with _build_client() as client:
        response = client.get("/api/v1/jobs/job_nonexistent")
        assert response.status_code == 404
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "job_not_found"


def test_list_outfits_empty() -> None:
    with _build_client() as client:
        _, trip_id = _create_user_and_trip(client)
        response = client.get(f"/api/v1/trips/{trip_id}/outfits")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["items"] == []
        assert payload["meta"]["total"] == 0


def test_create_outfit() -> None:
    with _build_client() as client:
        _, trip_id = _create_user_and_trip(client)
        response = client.post(
            f"/api/v1/trips/{trip_id}/outfits",
            json={
                "scene": "citywalk",
                "season": "spring",
                "style": "casual",
                "items": [{"name": "白衬衫"}],
                "tips": "建议穿舒适鞋子",
                "images": ["https://example.com/img1.png"],
            },
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["success"] is True
        data = payload["data"]
        assert data["scene"] == "citywalk"
        assert data["season"] == "spring"
        assert data["style"] == "casual"
        assert data["items"] == [{"name": "白衬衫"}]
        assert data["tips"] == "建议穿舒适鞋子"
        assert data["images"] == ["https://example.com/img1.png"]


def test_adjustment_adds_requested_place() -> None:
    from app.api.v1 import adjustments

    class DisabledAmapClient:
        available = False

    original_get_amap_client = adjustments.get_amap_client
    adjustments.get_amap_client = lambda: DisabledAmapClient()  # type: ignore[assignment]
    with _build_client() as client:
        try:
            _, trip_id = _create_user_and_trip(client)
            day_response = client.post(
                f"/api/v1/trips/{trip_id}/days",
                json={"day_index": 1, "title": "第一天"},
            )
            day_id = day_response.json()["data"]["id"]
            client.post(
                f"/api/v1/trip-days/{day_id}/points",
                json={"name": "原有景点", "point_type": "spot", "sort_order": 1},
            )

            response = client.post(
                f"/api/v1/trips/{trip_id}/adjustments",
                json={"instruction": "我要去广州塔"},
            )

            assert response.status_code == 201
            payload = response.json()
            assert payload["success"] is True
            assert payload["data"]["output_data"]["summary"] == "已新增行程点：广州塔。"
            changes = payload["data"]["output_data"]["changes"]
            assert changes[0]["op"] == "add"
            assert changes[0]["value"] == "广州塔"

            points_response = client.get(f"/api/v1/trip-days/{day_id}/points")
            points = points_response.json()["data"]["items"]
            assert [point["name"] for point in points] == ["原有景点", "广州塔"]
        finally:
            adjustments.get_amap_client = original_get_amap_client


def test_list_spots_empty() -> None:
    with _build_client() as client:
        _, trip_id = _create_user_and_trip(client)
        response = client.get(f"/api/v1/trips/{trip_id}/spots")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["items"] == []
        assert payload["meta"]["total"] == 0


def test_search_with_keyword() -> None:
    with _build_client() as client:
        _, trip_id = _create_user_and_trip(client)
        response = client.get("/api/v1/search", params={"keyword": "京都"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        data = payload["data"]
        assert "items" in data
        assert data["total"] >= 1
        # 搜索结果应包含刚创建的行程（destination_name=京都）
        destinations = [item for item in data["items"] if item["type"] == "destination"]
        assert any(item["title"] == "测试行程" for item in destinations)


def test_search_empty_keyword_validation() -> None:
    with _build_client() as client:
        response = client.get("/api/v1/search", params={"keyword": ""})
        assert response.status_code == 422


def test_list_notifications_empty() -> None:
    with _build_client() as client:
        user_id = str(uuid.uuid4())
        response = client.get("/api/v1/notifications", params={"user_id": user_id})
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["items"] == []
        assert payload["meta"]["total"] == 0


def test_list_trip_versions_empty() -> None:
    with _build_client() as client:
        _, trip_id = _create_user_and_trip(client)
        response = client.get(f"/api/v1/trips/{trip_id}/versions")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["items"] == []
        assert payload["meta"]["total"] == 0


def test_response_structure_success() -> None:
    """验证成功响应结构为 {success, data, meta}。"""
    with _build_client() as client:
        _, trip_id = _create_user_and_trip(client)
        response = client.get(f"/api/v1/trips/{trip_id}/outfits")
        payload = response.json()
        assert set(payload.keys()) >= {"success", "data", "meta"}
        assert payload["success"] is True
        assert "items" in payload["data"]
        assert "request_id" in payload["meta"]


def test_response_structure_error() -> None:
    """验证错误响应结构为 {success, error, meta}。"""
    with _build_client() as client:
        response = client.get("/api/v1/jobs/job_nonexistent")
        payload = response.json()
        assert set(payload.keys()) >= {"success", "error", "meta"}
        assert payload["success"] is False
        assert "code" in payload["error"]
        assert "message" in payload["error"]
        assert "request_id" in payload["meta"]
