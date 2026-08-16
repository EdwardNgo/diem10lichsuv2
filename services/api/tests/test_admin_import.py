import uuid
from pathlib import Path

import pytest
from pytest import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.orm import Session

from diem10_api.main import app
from diem10_api.models import (
    Asset,
    AssetLink,
    ExamVersion,
    ImportJob,
    Question,
    QuestionOption,
)
from tests.parsers.test_manual_exam import (
    MANUAL_EXAM_FIXTURE,
    MANUAL_EXAM_FIXTURE_MISSING_REASON,
)
from tests.test_admin import (
    client_with_db,
    configure_r2,
    create_admin,
    create_user_session,
    session_override,
)

pytestmark = pytest.mark.skipif(
    not MANUAL_EXAM_FIXTURE.exists(),
    reason=MANUAL_EXAM_FIXTURE_MISSING_REASON,
)


def create_source_asset(
    session: Session,
    *,
    admin_id: object,
    object_key: str = "source-documents/de-so-1.docx",
    checksum: str = "d" * 64,
) -> Asset:
    asset = Asset(
        object_key=object_key,
        bucket="test-bucket",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=MANUAL_EXAM_FIXTURE.stat().st_size,
        checksum_sha256=checksum,
        asset_kind="source_document",
        uploaded_by_user_id=admin_id,  # type: ignore[arg-type]
    )
    session.add(asset)
    session.flush()
    return asset


def test_admin_import_manual_exam_creates_draft(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, engine = session_override(tmp_path)
    configure_r2(monkeypatch)
    token = "admin-token"

    def fake_download_object(
        object_key: str,
        bucket: str,
        settings: object,
    ) -> bytes:
        return MANUAL_EXAM_FIXTURE.read_bytes()

    monkeypatch.setattr(
        "diem10_api.services.import_service.download_object",
        fake_download_object,
    )

    with Session(engine) as session:
        admin = create_admin(session, token=token)
        asset = create_source_asset(session, admin_id=admin.id)
        session.commit()
        asset_id = asset.id

    client = client_with_db(session_factory, token)
    response = client.post(f"/v1/admin/extractions/{asset_id}", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "succeeded"
    assert data["exam_version_id"] is not None
    assert data["summary"]["part1_count"] == 24
    assert data["summary"]["part2_count"] == 4
    assert data["summary"]["warnings"] > 0

    with Session(engine) as session:
        version = session.get(ExamVersion, uuid.UUID(data["exam_version_id"]))
        assert version is not None
        assert version.status == "draft"
        assert version.title == "ĐỀ SỐ 1"
        questions = session.scalars(select(Question)).all()
        assert len(questions) == 28
        mc_question = next(
            question
            for question in questions
            if question.part_number == 1 and question.part_position == 1
        )
        options = session.scalars(
            select(QuestionOption)
            .where(QuestionOption.question_id == mc_question.id)
            .order_by(QuestionOption.position.asc())
        ).all()
        assert [option.position for option in options] == [1, 2, 3, 4]
        assert session.scalar(select(AssetLink)) is not None
        assert session.scalar(select(ImportJob)).status == "succeeded"

    app.dependency_overrides.clear()


def test_import_is_idempotent_for_same_asset(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, engine = session_override(tmp_path)
    configure_r2(monkeypatch)
    token = "admin-token"

    monkeypatch.setattr(
        "diem10_api.services.import_service.download_object",
        lambda *args, **kwargs: MANUAL_EXAM_FIXTURE.read_bytes(),
    )

    with Session(engine) as session:
        admin = create_admin(session, token=token)
        asset = create_source_asset(session, admin_id=admin.id)
        session.commit()
        asset_id = asset.id

    client = client_with_db(session_factory, token)
    first = client.post(f"/v1/admin/extractions/{asset_id}", json={})
    second = client.post(f"/v1/admin/extractions/{asset_id}", json={})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["exam_version_id"] == second.json()["exam_version_id"]

    with Session(engine) as session:
        assert len(session.scalars(select(ExamVersion)).all()) == 1

    app.dependency_overrides.clear()


def test_student_cannot_import_source_document(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    student_token = "student-token"

    with Session(engine) as session:
        create_user_session(
            session=session,
            email="student@example.com",
            token=student_token,
            google_subject="student-sub",
        )
        session.commit()

    client = client_with_db(session_factory, student_token)
    response = client.post(
        "/v1/admin/extractions/00000000-0000-0000-0000-000000000001",
        json={},
    )
    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_import_ocr_pdf_is_rejected(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    session_factory, engine = session_override(tmp_path)
    configure_r2(monkeypatch)
    token = "admin-token"

    monkeypatch.setattr(
        "diem10_api.services.import_service.download_object",
        lambda *args, **kwargs: b"%PDF-1.4 minimal",
    )

    def fake_parse_source(*args: object, **kwargs: object) -> object:
        from diem10_api.parsers.pdf_reader import OcrNotSupportedError

        raise OcrNotSupportedError("PDF appears to be scan-only or image-only")

    monkeypatch.setattr(
        "diem10_api.services.import_service.parse_source",
        fake_parse_source,
    )

    with Session(engine) as session:
        admin = create_admin(session, token=token)
        asset = create_source_asset(
            session,
            admin_id=admin.id,
            object_key="source-documents/scan.pdf",
            checksum="e" * 64,
        )
        asset.mime_type = "application/pdf"
        session.commit()
        asset_id = asset.id

    client = client_with_db(session_factory, token)
    response = client.post(f"/v1/admin/extractions/{asset_id}", json={})

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_code"] == "ocr_not_supported"

    with Session(engine) as session:
        assert session.scalar(select(ExamVersion)) is None

    app.dependency_overrides.clear()
