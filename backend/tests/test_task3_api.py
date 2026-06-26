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


def test_user_profile_trip_domain_and_packing_items() -> None:
    with _build_client() as client:
        user_id = str(uuid.uuid4())

        profile_payload = {
            "email": "alice@example.com",
            "username": "alice",
            "display_name": "Alice",
            "avatar_url": "https://example.com/avatar.png",
            "bio": "爱旅行",
            "departure_city": "上海",
            "preferred_styles": ["citywalk", "museum"],
            "budget_level": "medium",
            "language": "zh-CN",
            "timezone": "Asia/Shanghai",
        }
        profile_response = client.put(f"/api/v1/users/{user_id}/profile", json=profile_payload)
        assert profile_response.status_code == 200
        assert profile_response.json()["data"]["preference"]["departure_city"] == "上海"

        trip_response = client.post(
            f"/api/v1/users/{user_id}/trips",
            json={
                "title": "东京五日",
                "destination_name": "东京",
                "status": "draft",
                "notes": "先排热门点位",
            },
        )
        assert trip_response.status_code == 201
        trip_id = trip_response.json()["data"]["id"]

        day_1 = client.post(
            f"/api/v1/trips/{trip_id}/days",
            json={"day_index": 1, "title": "Day 1", "summary": "浅草和上野"},
        )
        assert day_1.status_code == 201
        day_1_id = day_1.json()["data"]["id"]

        day_2 = client.post(
            f"/api/v1/trips/{trip_id}/days",
            json={"day_index": 1, "title": "Day 0", "summary": "先去机场周边"},
        )
        assert day_2.status_code == 201
        day_2_id = day_2.json()["data"]["id"]

        days_response = client.get(f"/api/v1/trips/{trip_id}/days")
        assert days_response.status_code == 200
        days_items = days_response.json()["data"]["items"]
        assert [item["day_index"] for item in days_items] == [1, 2]
        assert [item["id"] for item in days_items] == [day_2_id, day_1_id]

        reordered_days = client.patch(
            f"/api/v1/trips/{trip_id}/days/reorder",
            json={"ordered_ids": [day_1_id, day_2_id]},
        )
        assert reordered_days.status_code == 200
        assert [item["id"] for item in reordered_days.json()["data"]] == [day_1_id, day_2_id]

        point_a = client.post(
            f"/api/v1/trip-days/{day_1_id}/points",
            json={"name": "浅草寺", "point_type": "spot", "sort_order": 1},
        )
        assert point_a.status_code == 201
        point_a_id = point_a.json()["data"]["id"]

        point_b = client.post(
            f"/api/v1/trip-days/{day_1_id}/points",
            json={"name": "东京晴空塔", "point_type": "spot", "sort_order": 1},
        )
        assert point_b.status_code == 201
        point_b_id = point_b.json()["data"]["id"]

        points_response = client.get(f"/api/v1/trip-days/{day_1_id}/points")
        assert points_response.status_code == 200
        points_items = points_response.json()["data"]["items"]
        assert [item["id"] for item in points_items] == [point_b_id, point_a_id]
        assert [item["sort_order"] for item in points_items] == [1, 2]

        reordered_points = client.patch(
            f"/api/v1/trip-days/{day_1_id}/points/reorder",
            json={"ordered_ids": [point_a_id, point_b_id]},
        )
        assert reordered_points.status_code == 200
        assert [item["id"] for item in reordered_points.json()["data"]] == [point_a_id, point_b_id]

        packing_item = client.post(
            f"/api/v1/trips/{trip_id}/packing-items",
            json={"name": "护照", "category": "证件", "quantity": 1},
        )
        assert packing_item.status_code == 201
        item_id = packing_item.json()["data"]["id"]

        checked_item = client.patch(
            f"/api/v1/trips/{trip_id}/packing-items/{item_id}/checked",
            json={"is_checked": True},
        )
        assert checked_item.status_code == 200
        assert checked_item.json()["data"]["is_checked"] is True

        delete_item = client.delete(f"/api/v1/trips/{trip_id}/packing-items/{item_id}")
        assert delete_item.status_code == 204

