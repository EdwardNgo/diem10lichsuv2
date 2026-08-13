from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from diem10_api.controllers.deps import require_admin
from diem10_api.database import get_session
from diem10_api.models import User
from diem10_api.schemas.admin import (
    AssetResponse,
    SourceDocumentConfirmRequest,
    SourceDocumentPage,
    SourceDocumentUploadRequest,
    SourceDocumentUploadUrl,
)
from diem10_api.services.admin_service import AdminService

router = APIRouter(prefix="/v1/admin/source-documents", tags=["admin-source-documents"])


@router.post("/upload-url", response_model=SourceDocumentUploadUrl)
def create_source_document_upload_url(
    payload: SourceDocumentUploadRequest,
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> SourceDocumentUploadUrl:
    return AdminService(session).create_source_document_upload_url(payload)


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_source_document_upload(
    payload: SourceDocumentConfirmRequest,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AssetResponse:
    return AdminService(session).confirm_source_document_upload(payload, actor)


@router.get("", response_model=SourceDocumentPage)
def list_source_documents(
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> SourceDocumentPage:
    return AdminService(session).list_source_documents()
