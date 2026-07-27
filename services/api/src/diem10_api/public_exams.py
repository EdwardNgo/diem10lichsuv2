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
        .where(ExamVersion.status == "published")
        .where(ExamVersionTopic.is_primary.is_(True))
        .order_by(ExamVersion.published_at.desc(), ExamVersion.title.asc())
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
    query = _published_exam_query()
    if search:
        query = query.where(ExamVersion.title.ilike(f"%{search.strip()}%"))
    if topic:
        query = query.where(Topic.slug == topic)
    if year:
        query = query.where(ExamVersion.year == year)
    if difficulty:
        query = query.where(ExamVersion.difficulty == difficulty)

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
