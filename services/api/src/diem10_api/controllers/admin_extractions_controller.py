import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from diem10_api.controllers.admin_common import client_ip
from diem10_api.controllers.deps import require_admin
from diem10_api.database import get_session
from diem10_api.models import User
from diem10_api.schemas.admin import ImportJobResponse, ImportRequest
from diem10_api.services.import_service import ImportService

router = APIRouter(prefix="/v1/admin/extractions", tags=["admin-extractions"])


@router.post("/{asset_id}", response_model=ImportJobResponse)
def extract_draft_from_source_document(
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
        client_ip(request),
    )
