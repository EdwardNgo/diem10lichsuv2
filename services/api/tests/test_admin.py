from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from diem10_api import auth
from diem10_api.database import get_session
from diem10_api.main import app
from diem10_api.models import (
    AdminAllowlist,
    Asset,
    AuditLog,
    Base,
    ExamVersion,
    User,
    UserSession,
)


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


def configure_r2(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("R2_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("R2_BUCKET_NAME", "test-bucket")


def create_admin(
    session: Session,
    token: str = "admin-token",
    email: str = "owner@example.com",
) -> User:
    admin = create_user_session(
        session=session,
        email=email,
        token=token,
        google_subject=f"{email}-sub",
    )
    session.flush()
    session.add(AdminAllowlist(email=email, added_by_user_id=admin.id))
    return admin


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


def test_admin_can_create_source_document_upload_url(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, engine = session_override(tmp_path)
    configure_r2(monkeypatch)
    token = "admin-token"

    def fake_presigned_source_upload(
        *,
        object_key: str,
        mime_type: str,
        checksum_sha256: str,
        settings: object,
    ) -> tuple[str, dict[str, str]]:
        assert object_key == "source-documents/de-thi.pdf"
        assert mime_type == "application/pdf"
        assert checksum_sha256 == "a" * 64
        return "https://storage.example/upload", {"Content-Type": mime_type}

    monkeypatch.setattr(
        "diem10_api.services.admin_service.create_presigned_source_upload",
        fake_presigned_source_upload,
    )

    with Session(engine) as session:
        create_admin(session, token=token)
        session.commit()

    client = client_with_db(session_factory, token)
    response = client.post(
        "/v1/admin/assets/source-documents/upload-url",
        json={
            "filename": "de-thi.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 1024,
            "checksum_sha256": "A" * 64,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["bucket"] == "test-bucket"
    assert data["method"] == "PUT"
    assert data["upload_url"] == "https://storage.example/upload"
    assert data["expires_in_seconds"] == 900
    assert data["object_key"] == "source-documents/de-thi.pdf"

    with Session(engine) as session:
        assert session.scalar(select(Asset)) is None

    app.dependency_overrides.clear()


def test_source_document_confirm_stores_asset_without_draft(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, engine = session_override(tmp_path)
    configure_r2(monkeypatch)
    token = "admin-token"

    with Session(engine) as session:
        admin = create_admin(session, token=token)
        session.commit()
        admin_id = admin.id

    client = client_with_db(session_factory, token)
    payload = {
        "object_key": "source-documents/source.pdf",
        "bucket": "test-bucket",
        "filename": "source.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 2048,
        "checksum_sha256": "b" * 64,
    }
    response = client.post("/v1/admin/assets/source-documents", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["asset_kind"] == "source_document"
    assert data["object_key"] == "source-documents/source.pdf"
    assert data["uploaded_by_user_id"] == str(admin_id)

    with Session(engine) as session:
        asset = session.scalar(select(Asset))
        assert asset is not None
        assert asset.bucket == "test-bucket"
        assert asset.checksum_sha256 == "b" * 64
        assert session.scalar(select(ExamVersion)) is None

    duplicate_response = client.post("/v1/admin/assets/source-documents", json=payload)
    assert duplicate_response.status_code == 409

    app.dependency_overrides.clear()


def test_source_document_upload_rejects_student_and_invalid_metadata(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, engine = session_override(tmp_path)
    configure_r2(monkeypatch)
    student_token = "student-token"
    admin_token = "admin-token"

    with Session(engine) as session:
        create_user_session(
            session=session,
            email="student@example.com",
            token=student_token,
            google_subject="student-sub",
        )
        create_admin(session, token=admin_token)
        session.commit()

    student_client = client_with_db(session_factory, student_token)
    forbidden_response = student_client.post(
        "/v1/admin/assets/source-documents/upload-url",
        json={
            "filename": "source.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 1024,
            "checksum_sha256": "c" * 64,
        },
    )
    assert forbidden_response.status_code == 403
    app.dependency_overrides.clear()

    admin_client = client_with_db(session_factory, admin_token)
    invalid_response = admin_client.post(
        "/v1/admin/assets/source-documents/upload-url",
        json={
            "filename": "source.exe",
            "mime_type": "application/octet-stream",
            "size_bytes": 1024,
            "checksum_sha256": "c" * 64,
        },
    )
    assert invalid_response.status_code == 422

    too_large_response = admin_client.post(
        "/v1/admin/assets/source-documents",
        json={
            "object_key": "source-documents/source.pdf",
            "bucket": "test-bucket",
            "filename": "source.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 20 * 1024 * 1024 + 1,
            "checksum_sha256": "c" * 64,
        },
    )
    assert too_large_response.status_code == 422

    with Session(engine) as session:
        assert session.scalar(select(Asset)) is None

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
