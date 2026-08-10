import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from diem10_api.controllers.deps import get_current_user
from diem10_api.database import get_session
from diem10_api.models import User
from diem10_api.schemas.student_attempts import (
    AttemptDetail,
    AttemptHistoryPage,
    AttemptResultResponse,
    SaveAttemptAnswerRequest,
    SavedAttemptAnswer,
)
from diem10_api.services.student_attempt_service import StudentAttemptService

router = APIRouter(prefix="/v1/student", tags=["student-attempts"])


@router.post("/exams/{slug}/attempts", response_model=AttemptDetail)
def start_or_resume_attempt(
    slug: str,
    restart: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AttemptDetail:
    return StudentAttemptService(session).start_or_resume_attempt(
        current_user,
        slug,
        restart,
    )


@router.get("/attempts", response_model=AttemptHistoryPage)
def list_attempt_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AttemptHistoryPage:
    return StudentAttemptService(session).list_attempt_history(
        current_user,
        page,
        page_size,
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptDetail)
def get_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AttemptDetail:
    return StudentAttemptService(session).get_attempt(current_user, attempt_id)


@router.post("/attempts/{attempt_id}/resume", response_model=AttemptDetail)
def resume_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AttemptDetail:
    return StudentAttemptService(session).resume_attempt(current_user, attempt_id)


@router.post("/attempts/{attempt_id}/pause", status_code=status.HTTP_204_NO_CONTENT)
def pause_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    StudentAttemptService(session).pause_attempt(current_user, attempt_id)


@router.put(
    "/attempts/{attempt_id}/answers/{question_id}",
    response_model=SavedAttemptAnswer,
)
def save_attempt_answer(
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: SaveAttemptAnswerRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> SavedAttemptAnswer:
    return StudentAttemptService(session).save_attempt_answer(
        current_user,
        attempt_id,
        question_id,
        payload,
    )


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptResultResponse)
def submit_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AttemptResultResponse:
    return StudentAttemptService(session).submit_attempt(current_user, attempt_id)


@router.get("/attempts/{attempt_id}/result", response_model=AttemptResultResponse)
def get_attempt_result(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AttemptResultResponse:
    return StudentAttemptService(session).get_attempt_result(current_user, attempt_id)
