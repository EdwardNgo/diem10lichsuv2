import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from diem10_api.controllers.admin_common import client_ip
from diem10_api.controllers.deps import require_admin
from diem10_api.database import get_session
from diem10_api.models import User
from diem10_api.schemas.admin import (
    AllowlistEntry,
    AllowlistGrantRequest,
    AllowlistPage,
)
from diem10_api.services.admin_service import AdminService

router = APIRouter(prefix="/v1/admin/access", tags=["admin-access"])


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
        client_ip(request),
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
        client_ip(request),
    )
