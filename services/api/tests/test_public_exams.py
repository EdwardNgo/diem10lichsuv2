from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from diem10_api.database import get_session
from diem10_api.main import app
from diem10_api.models import Base, Exam, ExamVersion, ExamVersionTopic, Question, Topic


def test_public_exams_excludes_unpublished_content(tmp_path: Path) -> None:
    database_path = tmp_path / "public-exams.db"
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with Session(engine) as session:
        published_exam = Exam(slug="viet-nam-1945-1975")
        draft_exam = Exam(slug="draft-exam")
        topic = Topic(slug="lich-su-viet-nam", name="Lịch sử Việt Nam")
        session.add_all([published_exam, draft_exam, topic])
        session.flush()
        published_version = ExamVersion(
            exam_id=published_exam.id,
            version_number=1,
            status="published",
            title="Việt Nam 1945–1975",
            summary="Ôn tập giai đoạn lịch sử Việt Nam.",
            year=2026,
            difficulty="Trung bình",
            duration_minutes=50,
            published_at=datetime.now(UTC),
        )
        draft_version = ExamVersion(
            exam_id=draft_exam.id,
            version_number=1,
            status="draft",
            title="Không được công khai",
            summary="Nội dung nháp.",
            year=2026,
            difficulty="Dễ",
            duration_minutes=30,
            published_at=None,
        )
        session.add_all([published_version, draft_version])
        session.flush()
        session.add(
            ExamVersionTopic(
                exam_version_id=published_version.id,
                topic_id=topic.id,
                is_primary=True,
            )
        )
        session.add(
            Question(
                exam_version_id=published_version.id,
                position=1,
                body="Câu hỏi công khai chỉ dùng để đếm số lượng.",
                explanation="Không được trả qua API công khai.",
            )
        )
        session.commit()

    def override_session() -> Session:
        return session_factory()

    app.dependency_overrides[get_session] = override_session
    response = TestClient(app).get("/v1/public/exams")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "slug": "viet-nam-1945-1975",
                "title": "Việt Nam 1945–1975",
                "summary": "Ôn tập giai đoạn lịch sử Việt Nam.",
                "topic": "Lịch sử Việt Nam",
                "year": 2026,
                "difficulty": "Trung bình",
                "duration_minutes": 50,
                "question_count": 1,
            }
        ],
        "page": 1,
        "page_size": 12,
        "total": 1,
    }
