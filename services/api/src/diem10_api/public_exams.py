from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from diem10_api.database import get_session
from diem10_api.models import Exam, ExamVersion, ExamVersionTopic, Question, Topic

router = APIRouter(prefix="/v1/public/exams", tags=["public-exams"])


class PublicExam(BaseModel):
    slug: str
    title: str
    summary: str
    topic: str
    year: int | None
    difficulty: str
    duration_minutes: int
    question_count: int


class PublicExamPage(BaseModel):
    items: list[PublicExam]
    page: int
    page_size: int
    total: int


class PublicExamTopicFilter(BaseModel):
    slug: str
    name: str


class PublicExamFilters(BaseModel):
    topics: list[PublicExamTopicFilter]
    years: list[int]
    difficulties: list[str]


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


@router.get("/filters", response_model=PublicExamFilters)
def list_public_exam_filters(
    session: Session = Depends(get_session),
) -> PublicExamFilters:
    published_version_query = select(ExamVersion.id).where(
        ExamVersion.status == "published"
    )
    topic_rows = session.execute(
        select(Topic.slug, Topic.name)
        .join(ExamVersionTopic, ExamVersionTopic.topic_id == Topic.id)
        .where(ExamVersionTopic.exam_version_id.in_(published_version_query))
        .where(Topic.is_active.is_(True))
        .distinct()
        .order_by(Topic.name.asc())
    ).all()
    years = session.scalars(
        select(ExamVersion.year)
        .where(ExamVersion.status == "published")
        .where(ExamVersion.year.is_not(None))
        .distinct()
        .order_by(ExamVersion.year.desc())
    ).all()
    difficulties = session.scalars(
        select(ExamVersion.difficulty)
        .where(ExamVersion.status == "published")
        .distinct()
        .order_by(ExamVersion.difficulty.asc())
    ).all()

    return PublicExamFilters(
        topics=[
            PublicExamTopicFilter(slug=slug, name=name) for slug, name in topic_rows
        ],
        years=[year for year in years if year is not None],
        difficulties=list(difficulties),
    )


@router.get("", response_model=PublicExamPage)
def list_public_exams(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    search: str | None = Query(default=None, max_length=120),
    topic: str | None = Query(default=None, max_length=255),
    year: int | None = Query(default=None, ge=1900, le=2100),
    difficulty: str | None = Query(default=None, max_length=50),
    session: Session = Depends(get_session),
) -> PublicExamPage:
    query = apply_public_exam_filters(
        _published_exam_query(),
        search=search,
        topic=topic,
        year=year,
        difficulty=difficulty,
    )

    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.execute(query.offset((page - 1) * page_size).limit(page_size)).all()
    return PublicExamPage(
        items=[
            PublicExam(
                slug=exam.slug,
                title=version.title,
                summary=version.summary,
                topic=topic.name,
                year=version.year,
                difficulty=version.difficulty,
                duration_minutes=version.duration_minutes,
                question_count=question_count,
            )
            for exam, version, topic, question_count in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )
