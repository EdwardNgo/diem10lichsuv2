import uuid
from pathlib import Path

from pytest import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from diem10_api.main import app
from diem10_api.models import AuditLog, ExamVersion, Topic
from tests.parsers.test_manual_exam import MANUAL_EXAM_FIXTURE
from tests.test_admin import (
    client_with_db,
    configure_r2,
    create_admin,
    session_override,
)
from tests.test_admin_import import create_source_asset


def _ensure_topic(session: Session) -> Topic:
    topic = session.scalar(select(Topic).where(Topic.slug == "lich-su-viet-nam"))
    if topic is not None:
        return topic
    topic = Topic(slug="lich-su-viet-nam", name="Lịch sử Việt Nam", sort_order=1)
    session.add(topic)
    session.flush()
    return topic


def _import_draft(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    token: str = "admin-token",
) -> tuple[sessionmaker[Session], Engine, uuid.UUID]:
    session_factory, engine = session_override(tmp_path)
    configure_r2(monkeypatch)
    monkeypatch.setattr(
        "diem10_api.services.import_service.download_object",
        lambda *args, **kwargs: MANUAL_EXAM_FIXTURE.read_bytes(),
    )
    with Session(engine) as session:
        admin = create_admin(session, token=token)
        _ensure_topic(session)
        asset = create_source_asset(session, admin_id=admin.id)
        session.commit()
        asset_id = asset.id

    client = client_with_db(session_factory, token)
    response = client.post(f"/v1/admin/extractions/{asset_id}", json={})
    assert response.status_code == 200
    version_id = uuid.UUID(response.json()["exam_version_id"])
    return session_factory, engine, version_id


def _prepare_draft_for_publish(client: object, engine: Engine, version_id: uuid.UUID) -> dict:
    with Session(engine) as session:
        topic = _ensure_topic(session)
        session.commit()
        topic_id = str(topic.id)

    detail = client.get(f"/v1/admin/publishing/drafts/{version_id}").json()  # type: ignore[attr-defined]
    updated = client.patch(  # type: ignore[attr-defined]
        f"/v1/admin/publishing/drafts/{version_id}",
        json={
            "expected_updated_at": detail["updated_at"],
            "summary": "Đề luyện tập từ tài liệu nguồn",
            "year": 2026,
            "difficulty": "Trung bình",
            "primary_topic_id": topic_id,
        },
    )
    assert updated.status_code == 200
    return updated.json()


def test_admin_can_list_and_get_imported_draft(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, _engine, version_id = _import_draft(tmp_path, monkeypatch)
    client = client_with_db(session_factory, "admin-token")

    listed = client.get("/v1/admin/publishing/drafts")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == str(version_id)

    detail = client.get(f"/v1/admin/publishing/drafts/{version_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "ĐỀ SỐ 1"
    assert len(detail.json()["questions"]) == 28
    assert detail.json()["import_context"] is not None

    app.dependency_overrides.clear()


def test_update_metadata_and_validate_draft(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, engine, version_id = _import_draft(tmp_path, monkeypatch)
    client = client_with_db(session_factory, "admin-token")
    _prepare_draft_for_publish(client, engine, version_id)

    validation = client.post(f"/v1/admin/publishing/drafts/{version_id}/validate")
    assert validation.status_code == 200
    body = validation.json()
    assert body["valid"] is True
    assert len(body["errors"]) == 0

    app.dependency_overrides.clear()


def test_publish_draft_makes_exam_public(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, engine, version_id = _import_draft(tmp_path, monkeypatch)
    client = client_with_db(session_factory, "admin-token")
    detail = _prepare_draft_for_publish(client, engine, version_id)

    published = client.post(
        f"/v1/admin/publishing/drafts/{version_id}/publish",
        json={
            "expected_updated_at": detail["updated_at"],
            "acknowledge_warnings": True,
        },
    )
    assert published.status_code == 200
    slug = published.json()["exam_slug"]

    public = client.get("/v1/public/exams")
    assert public.status_code == 200
    assert any(item["slug"] == slug for item in public.json()["items"])

    with Session(engine) as session:
        version = session.get(ExamVersion, version_id)
        assert version is not None
        assert version.status == "published"
        assert session.scalar(
            select(AuditLog).where(AuditLog.action == "exam.publish")
        ) is not None

    app.dependency_overrides.clear()


def test_student_cannot_access_admin_drafts(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    from tests.test_admin import create_user_session

    with Session(engine) as session:
        create_user_session(
            session=session,
            email="student@example.com",
            token="student-token",
            google_subject="student-sub",
        )
        session.commit()

    client = client_with_db(session_factory, "student-token")
    assert client.get("/v1/admin/publishing/drafts").status_code == 403
    app.dependency_overrides.clear()


def test_stale_update_returns_conflict(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, _engine, version_id = _import_draft(tmp_path, monkeypatch)
    client = client_with_db(session_factory, "admin-token")
    detail = client.get(f"/v1/admin/publishing/drafts/{version_id}").json()

    stale = client.patch(
        f"/v1/admin/publishing/drafts/{version_id}",
        json={
            "expected_updated_at": "2020-01-01T00:00:00+00:00",
            "summary": "Cập nhật cũ",
        },
    )
    assert stale.status_code == 409
    assert detail["summary"] != "Cập nhật cũ"
    app.dependency_overrides.clear()


def test_publish_without_acknowledge_warnings_fails_when_warnings_exist(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, engine, version_id = _import_draft(tmp_path, monkeypatch)
    client = client_with_db(session_factory, "admin-token")
    detail = _prepare_draft_for_publish(client, engine, version_id)

    response = client.post(
        f"/v1/admin/publishing/drafts/{version_id}/publish",
        json={
            "expected_updated_at": detail["updated_at"],
            "acknowledge_warnings": False,
        },
    )
    assert response.status_code == 422
    app.dependency_overrides.clear()
