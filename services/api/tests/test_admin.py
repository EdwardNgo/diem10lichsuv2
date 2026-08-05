from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from diem10_api import auth
from diem10_api.database import get_session
from diem10_api.main import app
from diem10_api.models import AdminAllowlist, AuditLog, Base, User, UserSession


def session_override(tmp_path: Path) -> tuple[sessionmaker[Session], Engine]:
    database_path = tmp_path / "admin.db"
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine), engine


def create_user_session(
    session: Session,
    email: str,
    token: str,
    google_subject: str,
) -> User:
    user = User(
        google_subject=google_subject,
        email=email,
        display_name=email,
        avatar_url=None,
    )
    session.add(user)
    session.flush()
    session.add(
        UserSession(
            user_id=user.id,
            token_hash=auth._hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    return user


def client_with_db(
    session_factory: sessionmaker[Session],
    token: str | None = None,
) -> TestClient:
    def override_session() -> Session:
        return session_factory()

    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)
    if token is not None:
        client.cookies.set("diem10_session", token)
    return client


def test_admin_role_is_dynamic_and_non_admin_gets_403(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "student-token"

    with Session(engine) as session:
        user = create_user_session(
            session=session,
            email="student@example.com",
            token=token,
            google_subject="student-sub",
        )
        session.commit()
        user_id = user.id

    client = client_with_db(session_factory, token)
    assert client.get("/v1/auth/me").json()["user"]["role"] == "student"
    assert client.get("/v1/admin/probe").status_code == 403

    with Session(engine) as session:
        session.add(
            AdminAllowlist(email="student@example.com", added_by_user_id=user_id)
        )
        session.commit()

    assert client.get("/v1/auth/me").json()["user"]["role"] == "admin"
    assert client.get("/v1/admin/probe").json() == {"ok": True}

    app.dependency_overrides.clear()


def test_admin_allowlist_grant_revoke_reactivate_and_audit(
    tmp_path: Path,
) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "admin-token"

    with Session(engine) as session:
        admin = create_user_session(
            session=session,
            email="owner@example.com",
            token=token,
            google_subject="owner-sub",
        )
        session.flush()
        session.add(
            AdminAllowlist(email="owner@example.com", added_by_user_id=admin.id)
        )
        session.commit()

    client = client_with_db(session_factory, token)
    grant_response = client.post(
        "/v1/admin/allowlist",
        json={"email": "New.Admin@Example.COM"},
    )
    assert grant_response.status_code == 201
    granted = grant_response.json()
    assert granted["email"] == "new.admin@example.com"
    assert granted["revoked_at"] is None

    revoke_response = client.delete(f"/v1/admin/allowlist/{granted['id']}")
    assert revoke_response.status_code == 200
    assert revoke_response.json()["revoked_at"] is not None

    reactivate_response = client.post(
        "/v1/admin/allowlist",
        json={"email": "new.admin@example.com"},
    )
    assert reactivate_response.status_code == 201
    assert reactivate_response.json()["revoked_at"] is None

    with Session(engine) as session:
        actions = session.scalars(
            select(AuditLog.action).order_by(AuditLog.action)
        ).all()
        assert actions == [
            "admin_allowlist.grant",
            "admin_allowlist.reactivate",
            "admin_allowlist.revoke",
        ]

    app.dependency_overrides.clear()


def test_admin_endpoints_require_login_and_block_student(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "student-token"

    with Session(engine) as session:
        create_user_session(
            session=session,
            email="student@example.com",
            token=token,
            google_subject="student-sub",
        )
        session.commit()

    anonymous_client = client_with_db(session_factory)
    assert anonymous_client.get("/v1/admin/allowlist").status_code == 401
    app.dependency_overrides.clear()

    student_client = client_with_db(session_factory, token)
    assert student_client.get("/v1/admin/allowlist").status_code == 403
    app.dependency_overrides.clear()


def test_cannot_revoke_last_active_admin(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "owner-token"

    with Session(engine) as session:
        owner = create_user_session(
            session=session,
            email="owner@example.com",
            token=token,
            google_subject="owner-sub",
        )
        session.flush()
        entry = AdminAllowlist(email="owner@example.com", added_by_user_id=owner.id)
        session.add(entry)
        session.commit()
        entry_id = entry.id

    client = client_with_db(session_factory, token)
    response = client.delete(f"/v1/admin/allowlist/{entry_id}")
    assert response.status_code == 409

    with Session(engine) as session:
        entry = session.get(AdminAllowlist, entry_id)
        assert entry is not None
        assert entry.revoked_at is None
        assert session.scalar(select(AuditLog)) is None

    app.dependency_overrides.clear()


def test_revoked_admin_loses_access_immediately(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "revoked-admin-token"

    with Session(engine) as session:
        admin = create_user_session(
            session=session,
            email="admin@example.com",
            token=token,
            google_subject="admin-sub",
        )
        session.flush()
        entry = AdminAllowlist(email="admin@example.com", added_by_user_id=admin.id)
        session.add(entry)
        session.commit()
        entry_id = entry.id

    client = client_with_db(session_factory, token)
    assert client.get("/v1/admin/probe").status_code == 200

    with Session(engine) as session:
        entry = session.get(AdminAllowlist, entry_id)
        assert entry is not None
        entry.revoked_at = datetime.now(UTC)
        session.commit()

    assert client.get("/v1/admin/probe").status_code == 403

    app.dependency_overrides.clear()
