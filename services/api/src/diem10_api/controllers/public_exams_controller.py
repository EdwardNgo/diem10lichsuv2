from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from diem10_api.database import get_session
from diem10_api.schemas.public_exams import PublicExamFilters, PublicExamPage
from diem10_api.services.public_exam_service import PublicExamService

router = APIRouter(prefix="/v1/public/exams", tags=["public-exams"])


@router.get("/filters", response_model=PublicExamFilters)
def list_public_exam_filters(
    session: Session = Depends(get_session),
) -> PublicExamFilters:
    return PublicExamService(session).list_filters()


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
    return PublicExamService(session).list_exams(
        page=page,
        page_size=page_size,
        search=search,
        topic=topic,
        year=year,
        difficulty=difficulty,
    )
