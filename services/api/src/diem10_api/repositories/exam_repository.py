from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from diem10_api.models import (
    Exam,
    ExamVersion,
    ExamVersionTopic,
    Question,
    QuestionOption,
    QuestionStatement,
    Topic,
)


def published_exam_query() -> Select[tuple[Exam, ExamVersion, Topic, int]]:
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


def apply_public_exam_filters(
    query: Select[tuple[Exam, ExamVersion, Topic, int]],
    search: str | None,
    topic: str | None,
    year: int | None,
    difficulty: str | None,
) -> Select[tuple[Exam, ExamVersion, Topic, int]]:
    search_value = search.strip() if search is not None else ""
    if search_value:
        query = query.where(ExamVersion.title.ilike(f"%{search_value}%"))
    if topic:
        version_ids_for_topic = (
            select(ExamVersionTopic.exam_version_id)
            .join(Topic, Topic.id == ExamVersionTopic.topic_id)
            .where(Topic.slug == topic)
            .where(Topic.is_active.is_(True))
        )
        query = query.where(ExamVersion.id.in_(version_ids_for_topic))
    if year:
        query = query.where(ExamVersion.year == year)
    if difficulty:
        query = query.where(ExamVersion.difficulty == difficulty)
    return query


class ExamRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_published_exam_rows(
        self,
        *,
        search: str | None,
        topic: str | None,
        year: int | None,
        difficulty: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[Exam, ExamVersion, Topic, int]], int]:
        query = apply_public_exam_filters(
            published_exam_query(),
            search=search,
            topic=topic,
            year=year,
            difficulty=difficulty,
        )
        total = (
            self._session.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )
        rows = list(
            self._session.execute(
                query.offset((page - 1) * page_size).limit(page_size)
            ).all()
        )
        return rows, total

    def list_filter_topics(self) -> list[tuple[str, str]]:
        published_version_query = select(ExamVersion.id).where(
            ExamVersion.status == "published"
        )
        return list(
            self._session.execute(
                select(Topic.slug, Topic.name)
                .join(ExamVersionTopic, ExamVersionTopic.topic_id == Topic.id)
                .where(ExamVersionTopic.exam_version_id.in_(published_version_query))
                .where(Topic.is_active.is_(True))
                .distinct()
                .order_by(Topic.name.asc())
            ).all()
        )

    def list_filter_years(self) -> list[int]:
        years = self._session.scalars(
            select(ExamVersion.year)
            .where(ExamVersion.status == "published")
            .where(ExamVersion.year.is_not(None))
            .distinct()
            .order_by(ExamVersion.year.desc())
        ).all()
        return [year for year in years if year is not None]

    def list_filter_difficulties(self) -> list[str]:
        return list(
            self._session.scalars(
                select(ExamVersion.difficulty)
                .where(ExamVersion.status == "published")
                .distinct()
                .order_by(ExamVersion.difficulty.asc())
            ).all()
        )

    def get_published_exam_detail_row(
        self,
        slug: str,
    ) -> tuple[Exam, ExamVersion, Topic, int] | None:
        question_count = (
            select(func.count(Question.id))
            .where(Question.exam_version_id == ExamVersion.id)
            .correlate(ExamVersion)
            .scalar_subquery()
        )
        row = self._session.execute(
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
            return None
        return row._tuple()

    def list_topic_names_for_version(self, version_id: object) -> list[str]:
        return list(
            self._session.scalars(
                select(Topic.name)
                .join(ExamVersionTopic, ExamVersionTopic.topic_id == Topic.id)
                .where(ExamVersionTopic.exam_version_id == version_id)
                .order_by(ExamVersionTopic.is_primary.desc(), Topic.name.asc())
            ).all()
        )

    def list_questions_for_version(self, version_id: object) -> list[Question]:
        return list(
            self._session.scalars(
                select(Question)
                .where(Question.exam_version_id == version_id)
                .order_by(
                    Question.part_number.asc(),
                    Question.part_position.asc(),
                    Question.position.asc(),
                )
            ).all()
        )

    def list_options_for_questions(
        self,
        question_ids: list[object],
    ) -> list[QuestionOption]:
        if not question_ids:
            return []

        return list(
            self._session.scalars(
                select(QuestionOption)
                .where(QuestionOption.question_id.in_(question_ids))
                .order_by(
                    QuestionOption.question_id.asc(), QuestionOption.position.asc()
                )
            ).all()
        )

    def list_statements_for_questions(
        self,
        question_ids: list[object],
    ) -> list[QuestionStatement]:
        if not question_ids:
            return []

        return list(
            self._session.scalars(
                select(QuestionStatement)
                .where(QuestionStatement.question_id.in_(question_ids))
                .order_by(
                    QuestionStatement.question_id.asc(),
                    QuestionStatement.position.asc(),
                )
            ).all()
        )
