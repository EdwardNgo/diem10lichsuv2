import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from diem10_api.controllers.deps import require_admin
from diem10_api.database import get_session
from diem10_api.models import User
from diem10_api.schemas.admin import (
    AdminProbe,
    AllowlistEntry,
    AllowlistGrantRequest,
    AllowlistPage,
    AssetResponse,
    ImportJobResponse,
    ImportRequest,
    SourceDocumentConfirmRequest,
    SourceDocumentPage,
    SourceDocumentUploadRequest,
    SourceDocumentUploadUrl,
)
from diem10_api.services.admin_service import AdminService
from diem10_api.services.import_service import ImportService

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


@router.get("/probe", response_model=AdminProbe)
def admin_probe(_: User = Depends(require_admin)) -> AdminProbe:
    return AdminProbe(ok=True)


@router.post(
    "/assets/source-documents/upload-url",
    response_model=SourceDocumentUploadUrl,
)
def create_source_document_upload_url(
    payload: SourceDocumentUploadRequest,
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> SourceDocumentUploadUrl:
    return AdminService(session).create_source_document_upload_url(payload)


@router.post(
    "/assets/source-documents",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_source_document_upload(
    payload: SourceDocumentConfirmRequest,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AssetResponse:
    return AdminService(session).confirm_source_document_upload(payload, actor)


@router.get("/assets/source-documents", response_model=SourceDocumentPage)
def list_source_documents(
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> SourceDocumentPage:
    return AdminService(session).list_source_documents()


@router.post(
    "/assets/{asset_id}/import",
    response_model=ImportJobResponse,
)
def import_source_document(
    asset_id: uuid.UUID,
    request: Request,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
    payload: ImportRequest | None = None,
) -> ImportJobResponse:
    return ImportService(session).import_source_document(
        asset_id,
        actor,
        payload.idempotency_key if payload is not None else None,
        _client_ip(request),
    )


@router.get("/allowlist", response_model=AllowlistPage)
def list_allowlist(
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AllowlistPage:
    return AdminService(session).list_allowlist()


@router.post(
    "/allowlist",
    response_model=AllowlistEntry,
    status_code=status.HTTP_201_CREATED,
)
def grant_allowlist(
    payload: AllowlistGrantRequest,
    request: Request,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AllowlistEntry:
    return AdminService(session).grant_allowlist(
        payload,
        actor,
        _client_ip(request),
    )


@router.delete("/allowlist/{entry_id}", response_model=AllowlistEntry)
def revoke_allowlist(
    entry_id: uuid.UUID,
    request: Request,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AllowlistEntry:
    return AdminService(session).revoke_allowlist(
        entry_id,
        actor,
        _client_ip(request),
    )
