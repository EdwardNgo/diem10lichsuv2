from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from diem10_api.controllers.deps import get_current_user
from diem10_api.database import get_session
from diem10_api.models import User
from diem10_api.schemas.student_exams import StudentExamDetail, StudentExamPage
from diem10_api.services.student_exam_service import StudentExamService

router = APIRouter(prefix="/v1/student/exams", tags=["student-exams"])


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
    return StudentExamService(session).list_exams(
        current_user,
        page=page,
        page_size=page_size,
        search=search,
        topic=topic,
        year=year,
        difficulty=difficulty,
    )


@router.get("/{slug}", response_model=StudentExamDetail)
def get_student_exam_detail(
    slug: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> StudentExamDetail:
    return StudentExamService(session).get_exam_detail(current_user, slug)
