from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from diem10_api.models import Attempt, User
from diem10_api.repositories.exam_repository import ExamRepository
from diem10_api.schemas.student_exams import (
    CompletionStatus,
    StudentActiveAttempt,
    StudentExam,
    StudentExamDetail,
    StudentExamOption,
    StudentExamPage,
    StudentExamQuestion,
)


class StudentExamService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = ExamRepository(session)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _ensure_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    def _completion_status_for_versions(
        self,
        user: User,
        version_ids: list[object],
    ) -> dict[object, CompletionStatus]:
        if not version_ids:
            return {}

        now = self._now()
        attempts = self._session.execute(
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
                paused_at is not None or self._ensure_aware(expires_at) > now
            ):
                statuses[version_id] = "in_progress"
            elif (
                attempt_status in {"submitted", "expired_and_submitted"}
                and current is None
            ):
                statuses[version_id] = "completed"

        return statuses

    def _completion_status(self, user: User, version_id: object) -> CompletionStatus:
        return self._completion_status_for_versions(user, [version_id]).get(
            version_id, "not_started"
        )

    def _active_attempt_for_version(
        self,
        user: User,
        version_id: object,
    ) -> StudentActiveAttempt | None:
        attempt = self._session.scalar(
            select(Attempt)
            .where(Attempt.user_id == user.id)
            .where(Attempt.exam_version_id == version_id)
            .where(Attempt.status == "in_progress")
            .order_by(Attempt.started_at.desc())
        )
        if attempt is None:
            return None
        remaining_until = (
            self._ensure_aware(attempt.paused_at)
            if attempt.paused_at is not None
            else self._now()
        )
        remaining_seconds = int(
            (self._ensure_aware(attempt.expires_at) - remaining_until).total_seconds()
        )
        if remaining_seconds <= 0:
            return None
        return StudentActiveAttempt(
            id=str(attempt.id), remaining_seconds=remaining_seconds
        )

    def list_exams(
        self,
        user: User,
        *,
        page: int,
        page_size: int,
        search: str | None,
        topic: str | None,
        year: int | None,
        difficulty: str | None,
    ) -> StudentExamPage:
        rows, total = self._repo.list_published_exam_rows(
            search=search,
            topic=topic,
            year=year,
            difficulty=difficulty,
            page=page,
            page_size=page_size,
        )
        version_ids = [version.id for _, version, _, _ in rows]
        statuses = self._completion_status_for_versions(user, version_ids)

        return StudentExamPage(
            items=[
                StudentExam(
                    slug=exam.slug,
                    title=version.title,
                    summary=version.summary,
                    topic=topic_row.name,
                    year=version.year,
                    difficulty=version.difficulty,
                    duration_minutes=version.duration_minutes,
                    question_count=question_count,
                    completion_status=statuses.get(version.id, "not_started"),
                )
                for exam, version, topic_row, question_count in rows
            ],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_exam_detail(self, user: User, slug: str) -> StudentExamDetail:
        row = self._repo.get_published_exam_detail_row(slug)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        exam, version, primary_topic, question_count = row
        topic_names = self._repo.list_topic_names_for_version(version.id)
        questions = self._repo.list_questions_for_version(version.id)
        question_ids = [question.id for question in questions]
        options_by_question_id: dict[object, list[StudentExamOption]] = {
            question.id: [] for question in questions
        }
        statements_by_question_id: dict[object, list[StudentExamOption]] = {
            question.id: [] for question in questions
        }
        for option in self._repo.list_options_for_questions(question_ids):
            options_by_question_id[option.question_id].append(
                StudentExamOption(
                    id=str(option.id),
                    position=option.position,
                    body=option.body,
                )
            )
        for statement in self._repo.list_statements_for_questions(question_ids):
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
            topics=topic_names,
            primary_topic=primary_topic.name,
            year=version.year,
            difficulty=version.difficulty,
            duration_minutes=version.duration_minutes,
            question_count=question_count,
            completion_status=self._completion_status(user, version.id),
            active_attempt=self._active_attempt_for_version(user, version.id),
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
