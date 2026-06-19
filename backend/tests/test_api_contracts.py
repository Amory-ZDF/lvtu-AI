from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_response_contract() -> None:
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["service"] == "Lv Backend"
    assert payload["meta"]["request_id"]


def test_destination_placeholder_contract() -> None:
    response = client.post(
        "/api/v1/planning/destinations",
        json={
            "departure_city": "上海",
            "duration_days": 4,
            "season": "11月",
            "travel_style": ["慢游", "出片"],
            "interests": ["寺院", "咖啡"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["provider"] == "mock"
    assert len(payload["data"]["destinations"]) == 3
    assert payload["data"]["destinations"][0]["hero_image"]["placeholder"] is True


def test_route_placeholder_contract() -> None:
    response = client.post(
        "/api/v1/planning/routes",
        json={
            "destination_name": "京都",
            "duration_days": 4,
            "pace": "balanced",
            "travelers": 2,
            "interests": ["摄影", "咖啡"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["destination_name"] == "京都"
    assert len(payload["data"]["options"]) >= 1
    assert payload["data"]["options"][0]["days"][0]["spots"][0]["images"]


def test_media_placeholder_contract() -> None:
    response = client.post(
        "/api/v1/planning/media/placeholders",
        json={
            "destination_name": "京都",
            "categories": ["destination", "viewpoint", "outfit"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]["assets"]) == 3
    assert payload["data"]["assets"][0]["items"][0]["url"].startswith("https://coresg-normal.trae.ai/")


def test_validation_error_contract() -> None:
    response = client.post(
        "/api/v1/planning/routes",
        json={
            "destination_name": "京都",
            "duration_days": 0,
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "validation_error"
    assert payload["meta"]["request_id"]
