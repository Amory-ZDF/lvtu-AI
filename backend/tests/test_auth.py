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


def _register_user(
    client: TestClient,
    *,
    email: str = "alice@example.com",
    username: str = "alice",
    password: str = "supersecret",
    display_name: str = "Alice",
):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "display_name": display_name,
        },
    )


def _login_user(client: TestClient, *, email: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def test_register_success() -> None:
    with _build_client() as client:
        response = _register_user(client)
        assert response.status_code == 201
        payload = response.json()
        assert payload["success"] is True
        data = payload["data"]
        assert data["token"]["access_token"]
        assert data["token"]["refresh_token"]
        assert data["token"]["token_type"] == "bearer"
        assert data["token"]["expires_in"] > 0
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["username"] == "alice"
        assert "password" not in response.text


def test_register_duplicate_email_conflict() -> None:
    with _build_client() as client:
        first = _register_user(client)
        assert first.status_code == 201

        second = _register_user(
            client,
            username="alice2",
            email="alice@example.com",
        )
        assert second.status_code == 409
        payload = second.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "user_already_exists"


def test_register_duplicate_username_conflict() -> None:
    with _build_client() as client:
        first = _register_user(client)
        assert first.status_code == 201

        second = _register_user(
            client,
            email="alice2@example.com",
            username="alice",
        )
        assert second.status_code == 409


def test_register_password_too_short() -> None:
    with _build_client() as client:
        response = _register_user(client, password="short")
        assert response.status_code == 422
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "validation_error"


def test_register_invalid_email() -> None:
    with _build_client() as client:
        response = _register_user(client, email="not-an-email")
        assert response.status_code == 422


def test_login_success() -> None:
    with _build_client() as client:
        _register_user(client)

        response = _login_user(client, email="alice@example.com", password="supersecret")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        data = payload["data"]
        assert data["token"]["access_token"]
        assert data["token"]["refresh_token"]
        assert data["user"]["email"] == "alice@example.com"


def test_login_wrong_password() -> None:
    with _build_client() as client:
        _register_user(client)

        response = _login_user(client, email="alice@example.com", password="wrong-password")
        assert response.status_code == 401
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "invalid_credentials"


def test_login_nonexistent_user() -> None:
    with _build_client() as client:
        response = _login_user(client, email="ghost@example.com", password="supersecret")
        assert response.status_code == 401
        payload = response.json()
        assert payload["error"]["code"] == "invalid_credentials"


def test_refresh_success() -> None:
    with _build_client() as client:
        register = _register_user(client)
        refresh_token = register.json()["data"]["token"]["refresh_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["access_token"]
        assert payload["data"]["refresh_token"]


def test_refresh_invalid_token() -> None:
    with _build_client() as client:
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not-a-valid-token"},
        )
        assert response.status_code == 401
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "invalid_token"


def test_refresh_with_access_token_rejected() -> None:
    with _build_client() as client:
        register = _register_user(client)
        access_token = register.json()["data"]["token"]["access_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "invalid_token"


def test_me_with_token_success() -> None:
    with _build_client() as client:
        register = _register_user(client)
        access_token = register.json()["data"]["token"]["access_token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["email"] == "alice@example.com"
        assert payload["data"]["username"] == "alice"


def test_me_without_token_unauthorized() -> None:
    with _build_client() as client:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "unauthorized"


def test_me_with_invalid_token_unauthorized() -> None:
    with _build_client() as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"


def test_me_with_refresh_token_rejected() -> None:
    with _build_client() as client:
        register = _register_user(client)
        refresh_token = register.json()["data"]["token"]["refresh_token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"


def test_core_business_optional_auth_allows_anonymous() -> None:
    """Existing core_business routes must still work without a token (dev mode)."""
    with _build_client() as client:
        user_id = str(uuid.uuid4())
        profile_response = client.put(
            f"/api/v1/users/{user_id}/profile",
            json={
                "email": "carol@example.com",
                "username": "carol",
                "display_name": "Carol",
            },
        )
        assert profile_response.status_code == 200


def test_core_business_optional_auth_enforces_owner_mismatch() -> None:
    """When authenticated, a user cannot operate on another user's resources."""
    with _build_client() as client:
        alice = _register_user(client, email="alice@example.com", username="alice")
        alice_token = alice.json()["data"]["token"]["access_token"]
        alice_id = alice.json()["data"]["user"]["id"]

        bob = _register_user(
            client,
            email="bob@example.com",
            username="bob",
            display_name="Bob",
        )
        bob_id = bob.json()["data"]["user"]["id"]

        # Alice tries to read Bob's profile while authenticated as Alice.
        response = client.get(
            f"/api/v1/users/{bob_id}/profile",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert response.status_code == 403

        # Alice can still read her own profile while authenticated.
        own = client.get(
            f"/api/v1/users/{alice_id}/profile",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert own.status_code == 200
        assert own.json()["data"]["email"] == "alice@example.com"
