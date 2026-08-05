import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from diem10_api.auth import normalize_email, require_admin
from diem10_api.database import get_session
from diem10_api.models import AdminAllowlist, AuditLog, User

router = APIRouter(prefix="/v1/admin", tags=["admin"])


class AdminProbe(BaseModel):
    ok: bool


class AllowlistEntry(BaseModel):
    id: str
    email: str
    added_by_user_id: str | None
    created_at: datetime
    revoked_at: datetime | None


class AllowlistGrantRequest(BaseModel):
    email: str = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = normalize_email(value)
        if "@" not in normalized:
            raise ValueError("email must contain @")
        return normalized


class AllowlistPage(BaseModel):
    items: list[AllowlistEntry]


def _now() -> datetime:
    return datetime.now(UTC)


def _entry_response(entry: AdminAllowlist) -> AllowlistEntry:
    return AllowlistEntry(
        id=str(entry.id),
        email=entry.email,
        added_by_user_id=(
            str(entry.added_by_user_id) if entry.added_by_user_id is not None else None
        ),
        created_at=entry.created_at,
        revoked_at=entry.revoked_at,
    )


def _client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


def _audit_allowlist_change(
    session: Session,
    actor: User,
    action: str,
    entry: AdminAllowlist,
    request: Request,
    before_data: dict[str, object] | None,
    after_data: dict[str, object] | None,
) -> None:
    session.add(
        AuditLog(
            actor_user_id=actor.id,
            action=action,
            target_type="admin_allowlist",
            target_id=entry.id,
            request_id=None,
            ip_address=_client_ip(request),
            before_data=before_data,
            after_data=after_data,
        )
    )


def _active_admin_count(session: Session) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(AdminAllowlist)
            .where(AdminAllowlist.revoked_at.is_(None))
        )
        or 0
    )


@router.get("/probe", response_model=AdminProbe)
def admin_probe(_: User = Depends(require_admin)) -> AdminProbe:
    return AdminProbe(ok=True)


@router.get("/allowlist", response_model=AllowlistPage)
def list_allowlist(
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AllowlistPage:
    entries = session.scalars(
        select(AdminAllowlist).order_by(
            AdminAllowlist.revoked_at.is_not(None),
            AdminAllowlist.email.asc(),
        )
    ).all()
    return AllowlistPage(items=[_entry_response(entry) for entry in entries])


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
    email = normalize_email(payload.email)
    entry = session.scalar(select(AdminAllowlist).where(AdminAllowlist.email == email))

    if entry is None:
        entry = AdminAllowlist(email=email, added_by_user_id=actor.id)
        session.add(entry)
        session.flush()
        _audit_allowlist_change(
            session=session,
            actor=actor,
            action="admin_allowlist.grant",
            entry=entry,
            request=request,
            before_data=None,
            after_data={"email": email, "revoked_at": None},
        )
    elif entry.revoked_at is not None:
        before_data: dict[str, object] = {
            "email": entry.email,
            "revoked_at": entry.revoked_at.isoformat(),
        }
        entry.revoked_at = None
        entry.added_by_user_id = actor.id
        _audit_allowlist_change(
            session=session,
            actor=actor,
            action="admin_allowlist.reactivate",
            entry=entry,
            request=request,
            before_data=before_data,
            after_data={"email": entry.email, "revoked_at": None},
        )

    session.commit()
    session.refresh(entry)
    return _entry_response(entry)


@router.delete("/allowlist/{entry_id}", response_model=AllowlistEntry)
def revoke_allowlist(
    entry_id: uuid.UUID,
    request: Request,
    actor: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AllowlistEntry:
    entry = session.get(AdminAllowlist, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if entry.revoked_at is None:
        if _active_admin_count(session) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot revoke the last active admin",
            )

        before_data: dict[str, object] = {"email": entry.email, "revoked_at": None}
        revoked_at = _now()
        entry.revoked_at = revoked_at
        _audit_allowlist_change(
            session=session,
            actor=actor,
            action="admin_allowlist.revoke",
            entry=entry,
            request=request,
            before_data=before_data,
            after_data={
                "email": entry.email,
                "revoked_at": revoked_at.isoformat(),
            },
        )
        session.commit()
        session.refresh(entry)

    return _entry_response(entry)
