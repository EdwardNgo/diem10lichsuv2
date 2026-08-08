import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from diem10_api import auth
from diem10_api.database import get_session
from diem10_api.main import app
from diem10_api.models import (
    Attempt,
    Base,
    Exam,
    ExamVersion,
    ExamVersionTopic,
    Question,
    QuestionOption,
    QuestionStatement,
    Topic,
    User,
    UserSession,
)


def session_override(tmp_path: Path) -> tuple[sessionmaker[Session], Engine]:
    database_path = tmp_path / "student-exams.db"
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine), engine


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


def create_user_with_session(
    session: Session,
    token: str,
    email: str = "student@example.com",
) -> User:
    user = User(
        google_subject=f"google-{email}",
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


def create_exam(
    session: Session,
    slug: str,
    title: str,
    topic: Topic,
    status: str = "published",
    year: int = 2026,
    difficulty: str = "Trung bình",
) -> ExamVersion:
    exam = Exam(slug=slug)
    session.add(exam)
    session.flush()
    version = ExamVersion(
        exam_id=exam.id,
        version_number=1,
        status=status,
        title=title,
        summary=f"Tóm tắt {title}",
        year=year,
        difficulty=difficulty,
        duration_minutes=50,
        published_at=datetime.now(UTC) if status == "published" else None,
    )
    session.add(version)
    session.flush()
    session.add(
        ExamVersionTopic(
            exam_version_id=version.id,
            topic_id=topic.id,
            is_primary=True,
        )
    )
    question = Question(
        exam_version_id=version.id,
        position=1,
        part_number=1,
        part_position=1,
        question_type="multiple_choice",
        body=f"Câu hỏi của {title}",
        source_text=None,
        explanation="Lời giải không được trả qua API chi tiết.",
    )
    session.add(question)
    session.flush()
    session.add_all(
        [
            QuestionOption(
                question_id=question.id,
                position=1,
                body="Đáp án đúng",
                is_correct=True,
            ),
            QuestionOption(
                question_id=question.id,
                position=2,
                body="Đáp án nhiễu",
                is_correct=False,
            ),
        ]
    )
    return version


def test_public_filters_and_list_filters_only_published(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    with Session(engine) as session:
        vietnam = Topic(slug="lich-su-viet-nam", name="Lịch sử Việt Nam")
        world = Topic(slug="lich-su-the-gioi", name="Lịch sử thế giới")
        session.add_all([vietnam, world])
        session.flush()
        create_exam(
            session,
            slug="viet-nam-1945-1975",
            title="Việt Nam 1945-1975",
            topic=vietnam,
            year=2026,
            difficulty="Trung bình",
        )
        create_exam(
            session,
            slug="chien-tranh-lanh",
            title="Chiến tranh lạnh",
            topic=world,
            year=2025,
            difficulty="Khó",
        )
        create_exam(
            session,
            slug="de-nhap",
            title="Đề nháp",
            topic=vietnam,
            status="draft",
            difficulty="Dễ",
        )
        session.commit()

    client = client_with_db(session_factory)
    response = client.get(
        "/v1/public/exams",
        params={
            "search": "Việt Nam",
            "topic": "lich-su-viet-nam",
            "year": 2026,
            "difficulty": "Trung bình",
        },
    )
    assert response.status_code == 200
    assert [item["slug"] for item in response.json()["items"]] == ["viet-nam-1945-1975"]

    filters_response = client.get("/v1/public/exams/filters")
    assert filters_response.status_code == 200
    filters = filters_response.json()
    assert filters["years"] == [2026, 2025]
    assert filters["difficulties"] == ["Khó", "Trung bình"]
    assert {topic["slug"] for topic in filters["topics"]} == {
        "lich-su-viet-nam",
        "lich-su-the-gioi",
    }
    app.dependency_overrides.clear()


def test_student_exams_include_completion_status_per_user(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "student-token"
    with Session(engine) as session:
        topic = Topic(slug="lich-su-viet-nam", name="Lịch sử Việt Nam")
        session.add(topic)
        session.flush()
        user = create_user_with_session(session, token)
        in_progress_version = create_exam(
            session,
            slug="dang-lam",
            title="Đề đang làm",
            topic=topic,
        )
        completed_version = create_exam(
            session,
            slug="da-xong",
            title="Đề đã xong",
            topic=topic,
            year=2025,
        )
        session.flush()
        now = datetime.now(UTC)
        session.add_all(
            [
                Attempt(
                    user_id=user.id,
                    exam_version_id=in_progress_version.id,
                    status="in_progress",
                    started_at=now,
                    expires_at=now + timedelta(minutes=50),
                    submitted_at=None,
                    attempt_number=1,
                ),
                Attempt(
                    user_id=user.id,
                    exam_version_id=completed_version.id,
                    status="submitted",
                    started_at=now - timedelta(days=1),
                    expires_at=now - timedelta(days=1, minutes=-50),
                    submitted_at=now - timedelta(days=1, minutes=-20),
                    attempt_number=1,
                ),
            ]
        )
        session.commit()

    anonymous_client = client_with_db(session_factory)
    assert anonymous_client.get("/v1/student/exams").status_code == 401
    app.dependency_overrides.clear()

    client = client_with_db(session_factory, token)
    response = client.get("/v1/student/exams?page_size=10")
    assert response.status_code == 200
    statuses = {
        item["slug"]: item["completion_status"] for item in response.json()["items"]
    }
    assert statuses["dang-lam"] == "in_progress"
    assert statuses["da-xong"] == "completed"
    app.dependency_overrides.clear()


def test_student_exam_detail_hides_answers_and_handles_archived(
    tmp_path: Path,
) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "student-token"
    with Session(engine) as session:
        topic = Topic(slug="lich-su-viet-nam", name="Lịch sử Việt Nam")
        session.add(topic)
        session.flush()
        create_user_with_session(session, token)
        version = create_exam(
            session,
            slug="chi-tiet-de",
            title="Chi tiết đề",
            topic=topic,
        )
        session.commit()
        version_id = version.id

    client = client_with_db(session_factory, token)
    response = client.get("/v1/student/exams/chi-tiet-de")
    assert response.status_code == 200
    detail = response.json()
    assert detail["slug"] == "chi-tiet-de"
    assert detail["question_count"] == 1
    assert detail["questions"][0]["options"][0]["body"] == "Đáp án đúng"
    assert "explanation" not in str(detail)
    assert "is_correct" not in str(detail)

    with Session(engine) as session:
        version = session.get(ExamVersion, version_id)
        assert version is not None
        version.status = "archived"
        session.commit()

    assert client.get("/v1/student/exams/chi-tiet-de").status_code == 404
    app.dependency_overrides.clear()


def load_seed_module() -> ModuleType:
    seed_path = Path(__file__).resolve().parents[1] / "scripts" / "seed_demo_exams.py"
    spec = importlib.util.spec_from_file_location("seed_demo_exams", seed_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_seed_demo_exams_is_idempotent(tmp_path: Path) -> None:
    _, engine = session_override(tmp_path)
    seed_module = load_seed_module()
    seed_module.SessionLocal = sessionmaker(bind=engine)

    seed_module.seed_demo_exams()
    seed_module.seed_demo_exams()

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Topic)) == 6
        assert session.scalar(select(func.count()).select_from(Exam)) == 5
        assert (
            session.scalar(
                select(func.count())
                .select_from(ExamVersion)
                .where(ExamVersion.status == "published")
            )
            == 4
        )
        assert session.scalar(select(func.count()).select_from(Question)) == 140
        assert session.scalar(select(func.count()).select_from(QuestionOption)) == 480
        assert (
            session.scalar(select(func.count()).select_from(QuestionStatement)) == 80
        )
        published_version = session.scalar(
            select(ExamVersion).where(ExamVersion.status == "published")
        )
        assert published_version is not None
        assert (
            session.scalar(
                select(func.count())
                .select_from(Question)
                .where(Question.exam_version_id == published_version.id)
                .where(Question.part_number == 1)
            )
            == 24
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(Question)
                .where(Question.exam_version_id == published_version.id)
                .where(Question.part_number == 2)
            )
            == 4
        )
