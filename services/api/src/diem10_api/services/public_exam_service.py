from sqlalchemy.orm import Session

from diem10_api.repositories.exam_repository import ExamRepository
from diem10_api.schemas.public_exams import (
    PublicExam,
    PublicExamFilters,
    PublicExamPage,
    PublicExamTopicFilter,
)


class PublicExamService:
    def __init__(self, session: Session) -> None:
        self._repo = ExamRepository(session)

    def list_filters(self) -> PublicExamFilters:
        topic_rows = self._repo.list_filter_topics()
        return PublicExamFilters(
            topics=[
                PublicExamTopicFilter(slug=slug, name=name) for slug, name in topic_rows
            ],
            years=self._repo.list_filter_years(),
            difficulties=self._repo.list_filter_difficulties(),
        )

    def list_exams(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        topic: str | None,
        year: int | None,
        difficulty: str | None,
    ) -> PublicExamPage:
        rows, total = self._repo.list_published_exam_rows(
            search=search,
            topic=topic,
            year=year,
            difficulty=difficulty,
            page=page,
            page_size=page_size,
        )
        return PublicExamPage(
            items=[
                PublicExam(
                    slug=exam.slug,
                    title=version.title,
                    summary=version.summary,
                    topic=topic_row.name,
                    year=version.year,
                    difficulty=version.difficulty,
                    duration_minutes=version.duration_minutes,
                    question_count=question_count,
                )
                for exam, version, topic_row, question_count in rows
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
