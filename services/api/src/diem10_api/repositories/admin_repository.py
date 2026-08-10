import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from diem10_api.core.security import normalize_email
from diem10_api.models import AdminAllowlist, Asset, AuditLog


class AdminRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_allowlist(self) -> list[AdminAllowlist]:
        return list(
            self._session.scalars(
                select(AdminAllowlist).order_by(
                    AdminAllowlist.revoked_at.is_not(None),
                    AdminAllowlist.email.asc(),
                )
            ).all()
        )

    def get_allowlist_by_email(self, email: str) -> AdminAllowlist | None:
        return self._session.scalar(
            select(AdminAllowlist).where(AdminAllowlist.email == email)
        )

    def get_allowlist_by_id(self, entry_id: uuid.UUID) -> AdminAllowlist | None:
        return self._session.get(AdminAllowlist, entry_id)

    def active_admin_count(self) -> int:
        return (
            self._session.scalar(
                select(func.count())
                .select_from(AdminAllowlist)
                .where(AdminAllowlist.revoked_at.is_(None))
            )
            or 0
        )

    def add_allowlist(self, entry: AdminAllowlist) -> AdminAllowlist:
        self._session.add(entry)
        self._session.flush()
        return entry

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self._session.add(audit_log)

    def get_asset_by_object_key(self, object_key: str) -> Asset | None:
        return self._session.scalar(select(Asset).where(Asset.object_key == object_key))

    def add_asset(self, asset: Asset) -> Asset:
        self._session.add(asset)
        self._session.commit()
        self._session.refresh(asset)
        return asset

    def commit(self) -> None:
        self._session.commit()

    def refresh(self, instance: object) -> None:
        self._session.refresh(instance)

    def flush(self) -> None:
        self._session.flush()

    @staticmethod
    def normalized_email(email: str) -> str:
        return normalize_email(email)
