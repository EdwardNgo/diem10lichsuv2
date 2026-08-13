from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from diem10_api import auth
from diem10_api.database import get_session
from diem10_api.main import app
from diem10_api.models import Base, User, UserSession


def session_override(tmp_path: Path) -> tuple[sessionmaker[Session], str]:
    database_path = tmp_path / "auth.db"
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine), str(database_path)


def configure_google_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("APP_BASE_URL", "http://testserver")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("GOOGLE_AUTHORIZATION_URL", "https://accounts.test/auth")
    monkeypatch.setenv("GOOGLE_TOKEN_URL", "https://accounts.test/token")
    monkeypatch.setenv("GOOGLE_JWKS_URL", "https://accounts.test/certs")


def test_safe_return_path_rejects_external_targets() -> None:
    assert auth.safe_return_path("/exams/viet-nam") == "/exams/viet-nam"
    assert auth.safe_return_path("https://evil.test") == "/exams"
    assert auth.safe_return_path("//evil.test/path") == "/exams"
    assert auth.safe_return_path(r"/\evil") == "/exams"


def test_google_callback_creates_user_session_and_logout(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    configure_google_env(monkeypatch)
    session_factory, _ = session_override(tmp_path)

    def override_session() -> Session:
        return session_factory()

    def fake_exchange(
        settings: auth.AuthSettings,
        code: str,
        code_verifier: str,
    ) -> dict[str, Any]:
        assert settings.google_client_id == "client-id"
        assert code == "valid-code"
        assert code_verifier
        return {"id_token": "mock-id-token"}

    def fake_verify(
        settings: auth.AuthSettings,
        id_token: str,
    ) -> dict[str, Any]:
        assert settings.google_client_id == "client-id"
        assert id_token == "mock-id-token"
        return {
            "sub": "google-sub-1",
            "email": "Student@Example.COM",
            "name": "Student Example",
            "picture": "https://example.com/avatar.png",
            "iss": "https://accounts.google.com",
            "email_verified": True,
        }

    monkeypatch.setattr(
        "diem10_api.services.auth_service.exchange_google_code",
        fake_exchange,
    )
    monkeypatch.setattr(
        "diem10_api.services.auth_service.verify_google_id_token",
        fake_verify,
    )
    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)

    start_response = client.get(
        "/v1/auth/google?return_to=/exams/viet-nam-1945-1975",
        follow_redirects=False,
    )
    assert start_response.status_code == 307
    location = start_response.headers["location"]
    state = parse_qs(urlsplit(location).query)["state"][0]

    callback_response = client.get(
        f"/v1/auth/google/callback?state={state}&code=valid-code",
        follow_redirects=False,
    )
    assert callback_response.status_code == 303
    assert callback_response.headers["location"] == "/exams/viet-nam-1945-1975"
    assert "diem10_session=" in callback_response.headers["set-cookie"]

    me_response = client.get("/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["email"] == "student@example.com"

    logout_response = client.post("/v1/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"ok": True}
    assert "diem10_session=" in logout_response.headers["set-cookie"]
    assert "httponly" in logout_response.headers["set-cookie"].lower()
    assert client.get("/v1/auth/me").status_code == 401

    with Session(session_factory.kw["bind"]) as session:
        user = session.scalar(select(User).where(User.google_subject == "google-sub-1"))
        assert user is not None
        assert user.last_login_at is not None
        assert session.scalar(select(UserSession)) is not None

    app.dependency_overrides.clear()


def test_google_callback_invalid_state_does_not_create_user(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    configure_google_env(monkeypatch)
    session_factory, _ = session_override(tmp_path)

    def override_session() -> Session:
        return session_factory()

    app.dependency_overrides[get_session] = override_session
    response = TestClient(app).get(
        "/v1/auth/google/callback?state=missing&code=valid-code",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/exams?auth_error=invalid_state"

    with Session(session_factory.kw["bind"]) as session:
        assert session.scalar(select(User)) is None
        assert session.scalar(select(UserSession)) is None

    app.dependency_overrides.clear()


def test_google_callback_requires_verified_email(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    configure_google_env(monkeypatch)
    session_factory, _ = session_override(tmp_path)

    def override_session() -> Session:
        return session_factory()

    def fake_exchange(
        settings: auth.AuthSettings,
        code: str,
        code_verifier: str,
    ) -> dict[str, Any]:
        return {"id_token": "mock-id-token"}

    def fake_verify(
        settings: auth.AuthSettings,
        id_token: str,
    ) -> dict[str, Any]:
        return {
            "sub": "google-sub-unverified",
            "email": "unverified@example.com",
            "email_verified": False,
            "iss": "https://accounts.google.com",
        }

    monkeypatch.setattr(
        "diem10_api.services.auth_service.exchange_google_code",
        fake_exchange,
    )
    monkeypatch.setattr(
        "diem10_api.services.auth_service.verify_google_id_token",
        fake_verify,
    )
    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)

    start_response = client.get(
        "/v1/auth/google?return_to=/history",
        follow_redirects=False,
    )
    state = parse_qs(urlsplit(start_response.headers["location"]).query)["state"][0]
    response = client.get(
        f"/v1/auth/google/callback?state={state}&code=valid-code",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/history?auth_error=invalid_profile"
    with Session(session_factory.kw["bind"]) as session:
        assert session.scalar(select(User)) is None
        assert session.scalar(select(UserSession)) is None

    app.dependency_overrides.clear()


def test_expired_session_cannot_access_protected_api(tmp_path: Path) -> None:
    session_factory, _ = session_override(tmp_path)
    raw_token = "expired-session-token"

    with Session(session_factory.kw["bind"]) as session:
        user = User(
            google_subject="google-sub-2",
            email="expired@example.com",
            display_name="Expired User",
            avatar_url=None,
        )
        session.add(user)
        session.flush()
        session.add(
            UserSession(
                user_id=user.id,
                token_hash=auth._hash_token(raw_token),
                expires_at=datetime.now(UTC) - timedelta(seconds=1),
            )
        )
        session.commit()

    def override_session() -> Session:
        return session_factory()

    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)
    client.cookies.set("diem10_session", raw_token)

    assert client.get("/v1/auth/me").status_code == 401

    app.dependency_overrides.clear()
