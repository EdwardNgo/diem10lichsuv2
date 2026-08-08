from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from diem10_api.auth import get_current_user
from diem10_api.database import get_session
from diem10_api.models import (
    Attempt,
    Exam,
    ExamVersion,
    ExamVersionTopic,
    Question,
    QuestionOption,
    QuestionStatement,
    Topic,
    User,
)
from diem10_api.public_exams import apply_public_exam_filters

router = APIRouter(prefix="/v1/student/exams", tags=["student-exams"])

CompletionStatus = Literal["not_started", "in_progress", "completed"]


class StudentExam(BaseModel):
    slug: str
    title: str
    summary: str
    topic: str
    year: int | None
    difficulty: str
    duration_minutes: int
    question_count: int
    completion_status: CompletionStatus


class StudentExamPage(BaseModel):
    items: list[StudentExam]
    page: int
    page_size: int
    total: int


class StudentExamOption(BaseModel):
    id: str
    position: int
    body: str


class StudentExamQuestion(BaseModel):
    id: str
    position: int
    part_number: int
    part_position: int
    question_type: str
    body: str
    source_text: str | None
    options: list[StudentExamOption]
    statements: list[StudentExamOption]


class StudentActiveAttempt(BaseModel):
    id: str
    remaining_seconds: int


class StudentExamDetail(BaseModel):
    slug: str
    title: str
    summary: str
    topics: list[str]
    primary_topic: str
    year: int | None
    difficulty: str
    duration_minutes: int
    question_count: int
    completion_status: CompletionStatus
    active_attempt: StudentActiveAttempt | None
    questions: list[StudentExamQuestion]


def _published_exam_query() -> Select[tuple[Exam, ExamVersion, Topic, int]]:
    question_count = (
        select(func.count(Question.id))
        .where(Question.exam_version_id == ExamVersion.id)
        .correlate(ExamVersion)
        .scalar_subquery()
    )
    return (
        select(Exam, ExamVersion, Topic, question_count.label("question_count"))
        .join(ExamVersion, ExamVersion.exam_id == Exam.id)
        .join(ExamVersionTopic, ExamVersionTopic.exam_version_id == ExamVersion.id)
        .join(Topic, Topic.id == ExamVersionTopic.topic_id)
        .where(Exam.deleted_at.is_(None))
        .where(ExamVersion.status == "published")
        .where(ExamVersionTopic.is_primary.is_(True))
        .order_by(ExamVersion.published_at.desc(), ExamVersion.title.asc())
    )


def _completion_status_for_versions(
    session: Session,
    user: User,
    version_ids: list[object],
) -> dict[object, CompletionStatus]:
    if not version_ids:
        return {}

    now = _now()
    attempts = session.execute(
        select(
            Attempt.exam_version_id,
            Attempt.status,
            Attempt.started_at,
            Attempt.expires_at,
            Attempt.paused_at,
        )
        .where(Attempt.user_id == user.id)
        .where(Attempt.exam_version_id.in_(version_ids))
        .order_by(Attempt.started_at.desc())
    ).all()

    statuses: dict[object, CompletionStatus] = {}
    for version_id, attempt_status, _, expires_at, paused_at in attempts:
        current = statuses.get(version_id)
        if current == "in_progress":
            continue
        if attempt_status == "in_progress" and (
            paused_at is not None or _ensure_aware(expires_at) > now
        ):
            statuses[version_id] = "in_progress"
        elif (
            attempt_status in {"submitted", "expired_and_submitted"}
            and current is None
        ):
            statuses[version_id] = "completed"

    return statuses


def _completion_status(
    session: Session,
    user: User,
    version_id: object,
) -> CompletionStatus:
    return _completion_status_for_versions(session, user, [version_id]).get(
        version_id, "not_started"
    )


def _now() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _active_attempt_for_version(
    session: Session,
    user: User,
    version_id: object,
) -> StudentActiveAttempt | None:
    attempt = session.scalar(
        select(Attempt)
        .where(Attempt.user_id == user.id)
        .where(Attempt.exam_version_id == version_id)
        .where(Attempt.status == "in_progress")
        .order_by(Attempt.started_at.desc())
    )
    if attempt is None:
        return None
    remaining_until = (
        _ensure_aware(attempt.paused_at)
        if attempt.paused_at is not None
        else _now()
    )
    remaining_seconds = int(
        (_ensure_aware(attempt.expires_at) - remaining_until).total_seconds()
    )
    if remaining_seconds <= 0:
        return None
    return StudentActiveAttempt(id=str(attempt.id), remaining_seconds=remaining_seconds)


@router.get("", response_model=StudentExamPage)
def list_student_exams(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    search: str | None = Query(default=None, max_length=120),
    topic: str | None = Query(default=None, max_length=255),
    year: int | None = Query(default=None, ge=1900, le=2100),
    difficulty: str | None = Query(default=None, max_length=50),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> StudentExamPage:
    query = apply_public_exam_filters(
        _published_exam_query(),
        search=search,
        topic=topic,
        year=year,
        difficulty=difficulty,
    )
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.execute(query.offset((page - 1) * page_size).limit(page_size)).all()
    version_ids = [version.id for _, version, _, _ in rows]
    statuses = _completion_status_for_versions(session, current_user, version_ids)

    return StudentExamPage(
        items=[
            StudentExam(
                slug=exam.slug,
                title=version.title,
                summary=version.summary,
                topic=topic.name,
                year=version.year,
                difficulty=version.difficulty,
                duration_minutes=version.duration_minutes,
                question_count=question_count,
                completion_status=statuses.get(version.id, "not_started"),
            )
            for exam, version, topic, question_count in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{slug}", response_model=StudentExamDetail)
def get_student_exam_detail(
    slug: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> StudentExamDetail:
    question_count = (
        select(func.count(Question.id))
        .where(Question.exam_version_id == ExamVersion.id)
        .correlate(ExamVersion)
        .scalar_subquery()
    )
    row = session.execute(
        select(Exam, ExamVersion, Topic, question_count.label("question_count"))
        .join(ExamVersion, ExamVersion.exam_id == Exam.id)
        .join(ExamVersionTopic, ExamVersionTopic.exam_version_id == ExamVersion.id)
        .join(Topic, Topic.id == ExamVersionTopic.topic_id)
        .where(Exam.slug == slug)
        .where(Exam.deleted_at.is_(None))
        .where(ExamVersion.status == "published")
        .where(ExamVersionTopic.is_primary.is_(True))
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    exam, version, primary_topic, question_count = row
    topic_names = session.scalars(
        select(Topic.name)
        .join(ExamVersionTopic, ExamVersionTopic.topic_id == Topic.id)
        .where(ExamVersionTopic.exam_version_id == version.id)
        .order_by(ExamVersionTopic.is_primary.desc(), Topic.name.asc())
    ).all()
    questions = session.scalars(
        select(Question)
        .where(Question.exam_version_id == version.id)
        .order_by(
            Question.part_number.asc(),
            Question.part_position.asc(),
            Question.position.asc(),
        )
    ).all()
    options_by_question_id: dict[object, list[StudentExamOption]] = {
        question.id: [] for question in questions
    }
    statements_by_question_id: dict[object, list[StudentExamOption]] = {
        question.id: [] for question in questions
    }
    if options_by_question_id:
        option_rows = session.scalars(
            select(QuestionOption)
            .where(QuestionOption.question_id.in_(options_by_question_id.keys()))
            .order_by(QuestionOption.question_id.asc(), QuestionOption.position.asc())
        ).all()
        for option in option_rows:
            options_by_question_id[option.question_id].append(
                StudentExamOption(
                    id=str(option.id),
                    position=option.position,
                    body=option.body,
                )
            )
        statement_rows = session.scalars(
            select(QuestionStatement)
            .where(QuestionStatement.question_id.in_(statements_by_question_id.keys()))
            .order_by(
                QuestionStatement.question_id.asc(),
                QuestionStatement.position.asc(),
            )
        ).all()
        for statement in statement_rows:
            statements_by_question_id[statement.question_id].append(
                StudentExamOption(
                    id=str(statement.id),
                    position=statement.position,
                    body=statement.body,
                )
            )

    return StudentExamDetail(
        slug=exam.slug,
        title=version.title,
        summary=version.summary,
        topics=list(topic_names),
        primary_topic=primary_topic.name,
        year=version.year,
        difficulty=version.difficulty,
        duration_minutes=version.duration_minutes,
        question_count=question_count,
        completion_status=_completion_status(session, current_user, version.id),
        active_attempt=_active_attempt_for_version(session, current_user, version.id),
        questions=[
            StudentExamQuestion(
                id=str(question.id),
                position=question.position,
                part_number=question.part_number,
                part_position=question.part_position,
                question_type=question.question_type,
                body=question.body,
                source_text=question.source_text,
                options=options_by_question_id[question.id],
                statements=statements_by_question_id[question.id],
            )
            for question in questions
        ],
    )
