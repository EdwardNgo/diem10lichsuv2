import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from diem10_api.controllers.admin_common import client_ip
from diem10_api.controllers.deps import require_admin
from diem10_api.database import get_session
from diem10_api.models import User
from diem10_api.repositories.draft_repository import DraftRepository
from diem10_api.schemas.admin import AssetResponse
from diem10_api.schemas.admin_draft import (
    AdminTopicOption,
    AdminTopicPage,
    ArchiveExamResponse,
    DraftDetailResponse,
    DraftImportContextResponse,
    DraftMetadataUpdate,
    DraftPage,
    DraftPublishRequest,
    DraftPublishResponse,
    DraftQuestionsUpdate,
    QuestionImageConfirmRequest,
    QuestionImageLinkRequest,
    QuestionImageUploadRequest,
    QuestionImageUploadUrl,
    ValidationResultResponse,
)
from diem10_api.services.admin_service import AdminService
from diem10_api.services.draft_service import DraftService
from diem10_api.services.publish_service import PublishService

router = APIRouter(prefix="/v1/admin/publishing", tags=["admin-publishing"])


@router.get("/topics", response_model=AdminTopicPage)
def list_admin_topics(
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AdminTopicPage:
    topics = DraftRepository(session).list_active_topics()
    return AdminTopicPage(
        items=[
            AdminTopicOption(id=str(topic.id), slug=topic.slug, name=topic.name)
            for topic in topics
        ]
    )


@router.get("/drafts", response_model=DraftPage)
def list_drafts(
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> DraftPage:
    return DraftService(session).list_drafts(
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get("/drafts/{version_id}", response_model=DraftDetailResponse)
def get_draft(
    version_id: uuid.UUID,
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DraftDetailResponse:
    return DraftService(session).get_draft(version_id)


@router.patch("/drafts/{version_id}", response_model=DraftDetailResponse)
def update_draft_metadata(
    version_id: uuid.UUID,
    payload: DraftMetadataUpdate,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DraftDetailResponse:
    return DraftService(session).update_metadata(version_id, payload, actor)


@router.put("/drafts/{version_id}/questions", response_model=DraftDetailResponse)
def update_draft_questions(
    version_id: uuid.UUID,
    payload: DraftQuestionsUpdate,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DraftDetailResponse:
    return DraftService(session).update_questions(version_id, payload, actor)


@router.get(
    "/drafts/{version_id}/import-context",
    response_model=DraftImportContextResponse,
)
def get_draft_import_context(
    version_id: uuid.UUID,
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DraftImportContextResponse:
    context = DraftService(session).get_import_context(version_id)
    if context is None:
        return DraftImportContextResponse(findings=[])
    return context


@router.post(
    "/drafts/{version_id}/validate",
    response_model=ValidationResultResponse,
)
def validate_draft(
    version_id: uuid.UUID,
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ValidationResultResponse:
    return PublishService(session).validate_draft(version_id)


@router.post(
    "/drafts/{version_id}/publish",
    response_model=DraftPublishResponse,
)
def publish_draft(
    version_id: uuid.UUID,
    payload: DraftPublishRequest,
    request: Request,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DraftPublishResponse:
    return PublishService(session).publish_draft(
        version_id,
        payload,
        actor,
        client_ip(request),
    )


@router.post(
    "/drafts/{version_id}/questions/{question_id}/image",
    response_model=DraftDetailResponse,
)
def link_question_image(
    version_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: QuestionImageLinkRequest,
    request: Request,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DraftDetailResponse:
    return DraftService(session).link_question_image(
        version_id,
        question_id,
        uuid.UUID(payload.asset_id),
        actor,
        client_ip(request),
    )


@router.delete(
    "/drafts/{version_id}/questions/{question_id}/image",
    response_model=DraftDetailResponse,
)
def unlink_question_image(
    version_id: uuid.UUID,
    question_id: uuid.UUID,
    request: Request,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DraftDetailResponse:
    return DraftService(session).unlink_question_image(
        version_id,
        question_id,
        actor,
        client_ip(request),
    )


@router.post("/exams/{exam_id}/archive", response_model=ArchiveExamResponse)
def archive_exam(
    exam_id: uuid.UUID,
    request: Request,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ArchiveExamResponse:
    return PublishService(session).archive_exam(exam_id, actor, client_ip(request))


@router.post("/question-images/upload-url", response_model=QuestionImageUploadUrl)
def create_question_image_upload_url(
    payload: QuestionImageUploadRequest,
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> QuestionImageUploadUrl:
    return AdminService(session).create_question_image_upload_url(payload)


@router.post(
    "/question-images",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_question_image_upload(
    payload: QuestionImageConfirmRequest,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AssetResponse:
    return AdminService(session).confirm_question_image_upload(payload, actor)
