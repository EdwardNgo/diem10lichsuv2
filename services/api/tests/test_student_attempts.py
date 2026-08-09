import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from diem10_api import auth
from diem10_api.database import get_session
from diem10_api.main import app
from diem10_api.models import (
    Attempt,
    AttemptAnswer,
    AttemptResult,
    AttemptStatementAnswer,
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
    database_path = tmp_path / "student-attempts.db"
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


def create_user(session: Session, token: str, email: str) -> User:
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
    status: str = "published",
    slug: str = "de-thu",
    title: str = "Đề thử",
) -> dict[str, object]:
    topic = session.scalar(select(Topic).where(Topic.slug == "lich-su-viet-nam"))
    if topic is None:
        topic = Topic(slug="lich-su-viet-nam", name="Lịch sử Việt Nam")
        session.add(topic)
        session.flush()
    exam = Exam(slug=slug)
    session.add(exam)
    session.flush()
    version = ExamVersion(
        exam_id=exam.id,
        version_number=1,
        status=status,
        title=title,
        summary="Tóm tắt đề thử",
        year=2026,
        difficulty="Trung bình",
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
    question_one = Question(
        exam_version_id=version.id,
        position=1,
        part_number=1,
        part_position=1,
        question_type="multiple_choice",
        body="Câu hỏi 1",
        source_text=None,
        explanation="Không được lộ",
    )
    question_two = Question(
        exam_version_id=version.id,
        position=2,
        part_number=1,
        part_position=2,
        question_type="multiple_choice",
        body="Câu hỏi 2",
        source_text=None,
        explanation="Không được lộ",
    )
    session.add_all([question_one, question_two])
    session.flush()
    option_one = QuestionOption(
        question_id=question_one.id,
        position=1,
        body="Lựa chọn 1",
        is_correct=True,
    )
    option_two = QuestionOption(
        question_id=question_one.id,
        position=2,
        body="Lựa chọn 2",
        is_correct=False,
    )
    other_question_option = QuestionOption(
        question_id=question_two.id,
        position=1,
        body="Lựa chọn câu 2",
        is_correct=True,
    )
    session.add_all([option_one, option_two, other_question_option])
    session.flush()
    return {
        "exam": exam,
        "version": version,
        "question_one": question_one,
        "question_two": question_two,
        "option_one": option_one,
        "option_two": option_two,
        "other_question_option": other_question_option,
    }


def create_true_false_question(
    session: Session,
    version: ExamVersion,
) -> dict[str, object]:
    question = Question(
        exam_version_id=version.id,
        position=3,
        part_number=2,
        part_position=1,
        question_type="true_false_group",
        body="Đọc tư liệu và chọn đúng sai",
        source_text="Tư liệu kiểm thử",
        explanation="Giải thích câu đúng sai",
    )
    session.add(question)
    session.flush()
    statements = [
        QuestionStatement(
            question_id=question.id,
            position=1,
            body="Phát biểu 1",
            is_correct=True,
        ),
        QuestionStatement(
            question_id=question.id,
            position=2,
            body="Phát biểu 2",
            is_correct=False,
        ),
        QuestionStatement(
            question_id=question.id,
            position=3,
            body="Phát biểu 3",
            is_correct=True,
        ),
        QuestionStatement(
            question_id=question.id,
            position=4,
            body="Phát biểu 4",
            is_correct=False,
        ),
    ]
    session.add_all(statements)
    session.flush()
    return {"question": question, "statements": statements}


def create_second_published_version(
    session: Session,
    exam: Exam,
    topic: Topic,
) -> dict[str, object]:
    version = ExamVersion(
        exam_id=exam.id,
        version_number=2,
        status="published",
        title="Đề thử bản mới",
        summary="Tóm tắt đề thử mới",
        year=2026,
        difficulty="Trung bình",
        duration_minutes=45,
        published_at=datetime.now(UTC),
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
        body="Câu hỏi bản mới",
        source_text=None,
        explanation="Giải thích bản mới",
    )
    session.add(question)
    session.flush()
    option = QuestionOption(
        question_id=question.id,
        position=1,
        body="Lựa chọn bản mới",
        is_correct=True,
    )
    session.add(option)
    session.flush()
    return {"version": version, "question": question, "option": option}


def test_start_attempt_is_idempotent_and_updates_completion_status(
    tmp_path: Path,
) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "student-token"
    with Session(engine) as session:
        create_user(session, token, "student@example.com")
        create_exam(session)
        session.commit()

    client = client_with_db(session_factory, token)
    first_response = client.post("/v1/student/exams/de-thu/attempts")
    second_response = client.post("/v1/student/exams/de-thu/attempts")
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] == second_response.json()["id"]
    assert first_response.json()["question_count"] == 2
    assert "explanation" not in str(first_response.json())
    assert "is_correct" not in str(first_response.json())

    exams_response = client.get("/v1/student/exams")
    assert exams_response.status_code == 200
    assert exams_response.json()["items"][0]["completion_status"] == "in_progress"

    detail_response = client.get("/v1/student/exams/de-thu")
    assert detail_response.status_code == 200
    assert detail_response.json()["active_attempt"]["id"] == first_response.json()["id"]
    assert detail_response.json()["active_attempt"]["remaining_seconds"] > 0

    restart_now_response = client.post("/v1/student/exams/de-thu/attempts?restart=true")
    assert restart_now_response.status_code == 200
    assert restart_now_response.json()["id"] != first_response.json()["id"]
    assert restart_now_response.json()["status"] == "in_progress"

    with Session(engine) as session:
        attempts = session.scalars(
            select(Attempt).order_by(Attempt.started_at.asc())
        ).all()
        assert len(attempts) == 2
        assert attempts[0].status == "abandoned"
        assert attempts[1].status == "in_progress"

        attempts[1].started_at = datetime.now(UTC) - timedelta(hours=2)
        attempts[1].expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()

    restarted_response = client.post("/v1/student/exams/de-thu/attempts")
    assert restarted_response.status_code == 200
    assert restarted_response.json()["id"] != restart_now_response.json()["id"]
    assert restarted_response.json()["status"] == "in_progress"

    with Session(engine) as session:
        attempts = session.scalars(
            select(Attempt).order_by(Attempt.started_at.asc())
        ).all()
        assert len(attempts) == 3
        statuses = {attempt.status for attempt in attempts}
        assert statuses == {"abandoned", "expired_and_submitted", "in_progress"}

    app.dependency_overrides.clear()


def test_start_attempt_requires_auth_and_published_exam(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    with Session(engine) as session:
        create_exam(session, status="draft")
        session.commit()

    anonymous_client = client_with_db(session_factory)
    assert anonymous_client.post("/v1/student/exams/de-thu/attempts").status_code == 401
    app.dependency_overrides.clear()

    token = "student-token"
    with Session(engine) as session:
        create_user(session, token, "student@example.com")
        session.commit()

    client = client_with_db(session_factory, token)
    assert client.post("/v1/student/exams/de-thu/attempts").status_code == 404
    app.dependency_overrides.clear()


def test_pause_attempt_preserves_remaining_time_until_resume(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "student-token"
    with Session(engine) as session:
        create_user(session, token, "student@example.com")
        create_exam(session)
        session.commit()

    client = client_with_db(session_factory, token)
    attempt = client.post("/v1/student/exams/de-thu/attempts").json()
    attempt_id = attempt["id"]

    pause_response = client.post(f"/v1/student/attempts/{attempt_id}/pause")
    assert pause_response.status_code == 204

    with Session(engine) as session:
        attempt_model = session.get(Attempt, uuid.UUID(attempt_id))
        assert attempt_model is not None
        assert attempt_model.paused_at is not None
        paused_at = attempt_model.paused_at
        if paused_at.tzinfo is None:
            paused_at = paused_at.replace(tzinfo=UTC)
        expires_at = attempt_model.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        remaining_seconds = int((expires_at - paused_at).total_seconds())
        simulated_now = datetime.now(UTC)
        attempt_model.paused_at = simulated_now - timedelta(minutes=5)
        attempt_model.expires_at = attempt_model.paused_at + timedelta(
            seconds=remaining_seconds
        )
        session.commit()

    paused_detail = client.get("/v1/student/exams/de-thu")
    assert paused_detail.status_code == 200
    assert paused_detail.json()["completion_status"] == "in_progress"
    assert (
        abs(
            paused_detail.json()["active_attempt"]["remaining_seconds"]
            - remaining_seconds
        )
        <= 1
    )

    resume_response = client.post(f"/v1/student/attempts/{attempt_id}/resume")
    assert resume_response.status_code == 200
    resumed = resume_response.json()
    resumed_expires_at = datetime.fromisoformat(resumed["expires_at"])
    if resumed_expires_at.tzinfo is None:
        resumed_expires_at = resumed_expires_at.replace(tzinfo=UTC)
    resumed_server_now = datetime.fromisoformat(resumed["server_now"])
    if resumed_server_now.tzinfo is None:
        resumed_server_now = resumed_server_now.replace(tzinfo=UTC)
    resumed_remaining = int(
        (resumed_expires_at - resumed_server_now).total_seconds()
    )
    assert abs(resumed_remaining - remaining_seconds) <= 1

    with Session(engine) as session:
        attempt_model = session.get(Attempt, uuid.UUID(attempt_id))
        assert attempt_model is not None
        assert attempt_model.paused_at is None

    app.dependency_overrides.clear()


def test_save_answer_validates_snapshot_owner_and_expiry(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "student-token"
    other_token = "other-token"
    with Session(engine) as session:
        create_user(session, token, "student@example.com")
        create_user(session, other_token, "other@example.com")
        exam_data = create_exam(session)
        session.commit()
        question_id = exam_data["question_one"].id
        option_id = exam_data["option_one"].id
        other_question_option_id = exam_data["other_question_option"].id

    client = client_with_db(session_factory, token)
    attempt = client.post("/v1/student/exams/de-thu/attempts").json()
    attempt_id = attempt["id"]

    save_response = client.put(
        f"/v1/student/attempts/{attempt_id}/answers/{question_id}",
        json={
            "selected_option_id": str(option_id),
            "is_marked_for_review": True,
        },
    )
    assert save_response.status_code == 200
    assert save_response.json()["selected_option_id"] == str(option_id)
    assert save_response.json()["is_marked_for_review"] is True

    reload_response = client.get(f"/v1/student/attempts/{attempt_id}")
    assert reload_response.status_code == 200
    assert reload_response.json()["answered_count"] == 1
    assert reload_response.json()["answers"][0]["question_id"] == str(question_id)

    invalid_option_response = client.put(
        f"/v1/student/attempts/{attempt_id}/answers/{question_id}",
        json={
            "selected_option_id": str(other_question_option_id),
            "is_marked_for_review": False,
        },
    )
    assert invalid_option_response.status_code == 400

    client.close()
    app.dependency_overrides.clear()
    other_client = client_with_db(session_factory, other_token)
    assert other_client.get(f"/v1/student/attempts/{attempt_id}").status_code == 404
    other_client.close()
    app.dependency_overrides.clear()

    with Session(engine) as session:
        attempt_uuid = uuid.UUID(attempt_id)
        attempt_model = session.get(Attempt, attempt_uuid)
        assert attempt_model is not None
        attempt_model.started_at = datetime.now(UTC) - timedelta(hours=2)
        attempt_model.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()

    expired_client = client_with_db(session_factory, token)
    expired_response = expired_client.put(
        f"/v1/student/attempts/{attempt_id}/answers/{question_id}",
        json={"selected_option_id": str(option_id), "is_marked_for_review": False},
    )
    assert expired_response.status_code == 409
    expired_client.close()

    with Session(engine) as session:
        saved_answer = session.get(
            AttemptAnswer,
            {"attempt_id": attempt_uuid, "question_id": question_id},
        )
        assert saved_answer is not None
        assert saved_answer.selected_option_id == option_id
        assert saved_answer.is_marked_for_review is True

    app.dependency_overrides.clear()


def test_true_false_answers_submit_and_result_are_idempotent(tmp_path: Path) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "student-token"
    with Session(engine) as session:
        create_user(session, token, "student@example.com")
        exam_data = create_exam(session)
        true_false_data = create_true_false_question(
            session,
            exam_data["version"],
        )
        session.commit()
        mcq_question_id = exam_data["question_one"].id
        mcq_option_id = exam_data["option_one"].id
        true_false_question_id = true_false_data["question"].id
        statement_ids = [
            statement.id for statement in true_false_data["statements"]
        ]

    client = client_with_db(session_factory, token)
    attempt = client.post("/v1/student/exams/de-thu/attempts").json()
    attempt_id = attempt["id"]
    true_false_question = next(
        question
        for question in attempt["questions"]
        if question["question_type"] == "true_false_group"
    )
    assert true_false_question["source_text"] == "Tư liệu kiểm thử"
    assert "is_correct" not in str(attempt)
    assert "Giải thích" not in str(attempt)

    assert (
        client.put(
            f"/v1/student/attempts/{attempt_id}/answers/{mcq_question_id}",
            json={
                "selected_option_id": str(mcq_option_id),
                "is_marked_for_review": False,
            },
        ).status_code
        == 200
    )
    save_tf_response = client.put(
        f"/v1/student/attempts/{attempt_id}/answers/{true_false_question_id}",
        json={
            "statement_answers": [
                {"statement_id": str(statement_ids[0]), "selected_value": True},
                {"statement_id": str(statement_ids[1]), "selected_value": False},
                {"statement_id": str(statement_ids[2]), "selected_value": False},
                {"statement_id": str(statement_ids[3]), "selected_value": True},
            ],
            "is_marked_for_review": True,
        },
    )
    assert save_tf_response.status_code == 200
    assert len(save_tf_response.json()["statement_answers"]) == 4

    reload_response = client.get(f"/v1/student/attempts/{attempt_id}")
    assert reload_response.status_code == 200
    assert reload_response.json()["answered_count"] == 2

    first_submit = client.post(f"/v1/student/attempts/{attempt_id}/submit")
    second_submit = client.post(f"/v1/student/attempts/{attempt_id}/submit")
    assert first_submit.status_code == 200
    assert second_submit.status_code == 200
    result = first_submit.json()
    assert result["status"] == "submitted"
    assert result["part1_score"] == 0.25
    assert result["part2_score"] == 0.25
    assert result["score"] == 0.5
    assert result["questions"][-1]["correct_count"] == 2
    assert result["questions"][-1]["earned_score"] == 0.25
    assert "correct_value" in str(result)
    assert second_submit.json()["score"] == result["score"]

    closed_save = client.put(
        f"/v1/student/attempts/{attempt_id}/answers/{mcq_question_id}",
        json={
            "selected_option_id": str(mcq_option_id),
            "is_marked_for_review": False,
        },
    )
    assert closed_save.status_code == 409

    with Session(engine) as session:
        attempt_uuid = uuid.UUID(attempt_id)
        assert session.get(AttemptResult, attempt_uuid) is not None
        assert (
            session.scalar(
                select(func.count())
                .select_from(AttemptStatementAnswer)
                .where(AttemptStatementAnswer.attempt_id == attempt_uuid)
            )
            == 4
        )

    app.dependency_overrides.clear()


def test_attempt_history_is_owned_completed_and_retries_current_version(
    tmp_path: Path,
) -> None:
    session_factory, engine = session_override(tmp_path)
    token = "student-token"
    other_token = "other-token"
    with Session(engine) as session:
        create_user(session, token, "student@example.com")
        create_user(session, other_token, "other@example.com")
        exam_data = create_exam(session)
        second_exam_data = create_exam(
            session,
            slug="de-thu-hai",
            title="Đề thử hai",
        )
        session.commit()
        exam_id = exam_data["exam"].id
        version_id = exam_data["version"].id
        question_id = exam_data["question_one"].id
        option_id = exam_data["option_one"].id
        second_question_id = second_exam_data["question_one"].id
        second_option_id = second_exam_data["option_one"].id

    client = client_with_db(session_factory, token)
    first_attempt = client.post("/v1/student/exams/de-thu/attempts").json()
    first_attempt_id = first_attempt["id"]
    assert (
        client.put(
            f"/v1/student/attempts/{first_attempt_id}/answers/{question_id}",
            json={
                "selected_option_id": str(option_id),
                "is_marked_for_review": False,
            },
        ).status_code
        == 200
    )
    first_result = client.post(
        f"/v1/student/attempts/{first_attempt_id}/submit"
    ).json()
    assert first_result["title"] == "Đề thử"
    assert first_result["attempt_number"] == 1
    assert first_result["can_retry"] is True

    second_attempt = client.post("/v1/student/exams/de-thu/attempts").json()
    second_attempt_id = second_attempt["id"]
    second_result = client.post(
        f"/v1/student/attempts/{second_attempt_id}/submit"
    ).json()
    assert second_result["attempt_number"] == 2

    newest_exam_attempt = client.post("/v1/student/exams/de-thu-hai/attempts").json()
    assert (
        client.put(
            f"/v1/student/attempts/{newest_exam_attempt['id']}/answers/{second_question_id}",
            json={
                "selected_option_id": str(second_option_id),
                "is_marked_for_review": False,
            },
        ).status_code
        == 200
    )
    newest_exam_result = client.post(
        f"/v1/student/attempts/{newest_exam_attempt['id']}/submit"
    ).json()
    assert newest_exam_result["title"] == "Đề thử hai"

    open_attempt = client.post("/v1/student/exams/de-thu/attempts").json()
    history_response = client.get("/v1/student/attempts")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["total"] == 2
    assert history["items"][0]["slug"] == "de-thu-hai"
    exam_history = next(item for item in history["items"] if item["slug"] == "de-thu")
    assert exam_history["attempt_count"] == 2
    assert exam_history["best_score"] == first_result["score"]
    assert exam_history["latest_score"] == second_result["score"]
    assert exam_history["attempts"][0]["attempt_id"] == second_attempt_id
    assert exam_history["attempts"][1]["attempt_id"] == first_attempt_id
    assert open_attempt["id"] not in {
        attempt["attempt_id"] for attempt in exam_history["attempts"]
    }

    other_client = client_with_db(session_factory, other_token)
    assert (
        other_client.get(
            f"/v1/student/attempts/{first_attempt_id}/result"
        ).status_code
        == 404
    )
    other_history = other_client.get("/v1/student/attempts")
    assert other_history.status_code == 200
    assert other_history.json()["total"] == 0
    other_client.close()
    app.dependency_overrides.clear()

    with Session(engine) as session:
        attempt_model = session.get(Attempt, uuid.UUID(open_attempt["id"]))
        assert attempt_model is not None
        attempt_model.status = "abandoned"
        version = session.get(ExamVersion, version_id)
        assert version is not None
        version.status = "archived"
        session.commit()

    archived_client = client_with_db(session_factory, token)
    archived_history = archived_client.get("/v1/student/attempts").json()
    archived_exam_history = next(
        item for item in archived_history["items"] if item["slug"] == "de-thu"
    )
    assert archived_exam_history["can_retry"] is False
    archived_result = archived_client.get(
        f"/v1/student/attempts/{first_attempt_id}/result"
    ).json()
    assert archived_result["title"] == "Đề thử"
    assert archived_result["can_retry"] is False
    assert archived_client.post("/v1/student/exams/de-thu/attempts").status_code == 404
    archived_client.close()
    app.dependency_overrides.clear()

    with Session(engine) as session:
        exam = session.get(Exam, exam_id)
        topic = session.scalar(select(Topic).where(Topic.slug == "lich-su-viet-nam"))
        assert exam is not None
        assert topic is not None
        create_second_published_version(session, exam, topic)
        session.commit()

    retry_client = client_with_db(session_factory, token)
    retry_attempt = retry_client.post("/v1/student/exams/de-thu/attempts")
    assert retry_attempt.status_code == 200
    assert retry_attempt.json()["title"] == "Đề thử bản mới"
    assert retry_attempt.json()["id"] != first_attempt_id
    retry_client.close()

    app.dependency_overrides.clear()
