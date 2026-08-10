import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from diem10_api.core.logging import get_logger
from diem10_api.models import AdminAllowlist, Asset, AuditLog, User
from diem10_api.repositories.admin_repository import AdminRepository
from diem10_api.schemas.admin import (
    AllowlistEntry,
    AllowlistGrantRequest,
    AllowlistPage,
    AssetResponse,
    SourceDocumentConfirmRequest,
    SourceDocumentUploadRequest,
    SourceDocumentUploadUrl,
)
from diem10_api.storage import (
    PRESIGNED_UPLOAD_TTL_SECONDS,
    SOURCE_DOCUMENT_PREFIX,
    R2Settings,
    StorageConfigurationError,
    build_source_document_key,
    create_presigned_source_upload,
    get_r2_settings,
    validate_source_document_metadata,
)

logger = get_logger("admin_service")


class AdminService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = AdminRepository(session)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _entry_response(entry: AdminAllowlist) -> AllowlistEntry:
        return AllowlistEntry(
            id=str(entry.id),
            email=entry.email,
            added_by_user_id=(
                str(entry.added_by_user_id)
                if entry.added_by_user_id is not None
                else None
            ),
            created_at=entry.created_at,
            revoked_at=entry.revoked_at,
        )

    @staticmethod
    def _asset_response(asset: Asset) -> AssetResponse:
        return AssetResponse(
            id=str(asset.id),
            object_key=asset.object_key,
            bucket=asset.bucket,
            mime_type=asset.mime_type,
            size_bytes=asset.size_bytes,
            checksum_sha256=asset.checksum_sha256,
            asset_kind=asset.asset_kind,
            uploaded_by_user_id=str(asset.uploaded_by_user_id),
            created_at=asset.created_at,
        )

    @staticmethod
    def _validate_source_document_payload(
        payload: SourceDocumentUploadRequest | SourceDocumentConfirmRequest,
    ) -> str:
        try:
            return validate_source_document_metadata(
                filename=payload.filename,
                mime_type=payload.mime_type,
                size_bytes=payload.size_bytes,
                checksum_sha256=payload.checksum_sha256,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error

    @staticmethod
    def _r2_settings_or_503() -> R2Settings:
        try:
            return get_r2_settings()
        except StorageConfigurationError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="R2 storage is not configured",
            ) from error

    def _audit_allowlist_change(
        self,
        actor: User,
        action: str,
        entry: AdminAllowlist,
        client_ip: str | None,
        before_data: dict[str, object] | None,
        after_data: dict[str, object] | None,
    ) -> None:
        self._repo.add_audit_log(
            AuditLog(
                actor_user_id=actor.id,
                action=action,
                target_type="admin_allowlist",
                target_id=entry.id,
                request_id=None,
                ip_address=client_ip,
                before_data=before_data,
                after_data=after_data,
            )
        )

    def create_source_document_upload_url(
        self,
        payload: SourceDocumentUploadRequest,
    ) -> SourceDocumentUploadUrl:
        checksum_sha256 = self._validate_source_document_payload(payload)
        settings = self._r2_settings_or_503()
        object_key = build_source_document_key(payload.filename)
        upload_url, headers = create_presigned_source_upload(
            object_key=object_key,
            mime_type=payload.mime_type,
            checksum_sha256=checksum_sha256,
            settings=settings,
        )
        logger.info(
            "admin.source_document.upload_url_created",
            object_key=object_key,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
        )
        return SourceDocumentUploadUrl(
            object_key=object_key,
            bucket=settings.bucket_name,
            upload_url=upload_url,
            method="PUT",
            headers=headers,
            expires_in_seconds=PRESIGNED_UPLOAD_TTL_SECONDS,
        )

    def confirm_source_document_upload(
        self,
        payload: SourceDocumentConfirmRequest,
        actor: User,
    ) -> AssetResponse:
        checksum_sha256 = self._validate_source_document_payload(payload)
        settings = self._r2_settings_or_503()
        if payload.bucket != settings.bucket_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Bucket does not match configured R2 bucket",
            )
        if not payload.object_key.startswith(SOURCE_DOCUMENT_PREFIX):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Object key is not a source document key",
            )
        existing = self._repo.get_asset_by_object_key(payload.object_key)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Source document already confirmed",
            )

        asset = Asset(
            object_key=payload.object_key,
            bucket=payload.bucket,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
            checksum_sha256=checksum_sha256,
            asset_kind="source_document",
            uploaded_by_user_id=actor.id,
        )
        saved = self._repo.add_asset(asset)
        logger.info(
            "admin.source_document.confirmed",
            asset_id=str(saved.id),
            object_key=saved.object_key,
            uploaded_by=str(actor.id),
        )
        return self._asset_response(saved)

    def list_allowlist(self) -> AllowlistPage:
        entries = self._repo.list_allowlist()
        return AllowlistPage(items=[self._entry_response(entry) for entry in entries])

    def grant_allowlist(
        self,
        payload: AllowlistGrantRequest,
        actor: User,
        client_ip: str | None,
    ) -> AllowlistEntry:
        email = self._repo.normalized_email(payload.email)
        entry = self._repo.get_allowlist_by_email(email)

        if entry is None:
            entry = AdminAllowlist(email=email, added_by_user_id=actor.id)
            self._repo.add_allowlist(entry)
            self._audit_allowlist_change(
                actor=actor,
                action="admin_allowlist.grant",
                entry=entry,
                client_ip=client_ip,
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
            self._audit_allowlist_change(
                actor=actor,
                action="admin_allowlist.reactivate",
                entry=entry,
                client_ip=client_ip,
                before_data=before_data,
                after_data={"email": entry.email, "revoked_at": None},
            )

        self._repo.commit()
        self._repo.refresh(entry)
        logger.info("admin.allowlist.granted", email=email, actor_id=str(actor.id))
        return self._entry_response(entry)

    def revoke_allowlist(
        self,
        entry_id: uuid.UUID,
        actor: User,
        client_ip: str | None,
    ) -> AllowlistEntry:
        entry = self._repo.get_allowlist_by_id(entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        if entry.revoked_at is None:
            if self._repo.active_admin_count() <= 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot revoke the last active admin",
                )

            before_data: dict[str, object] = {"email": entry.email, "revoked_at": None}
            revoked_at = self._now()
            entry.revoked_at = revoked_at
            self._audit_allowlist_change(
                actor=actor,
                action="admin_allowlist.revoke",
                entry=entry,
                client_ip=client_ip,
                before_data=before_data,
                after_data={
                    "email": entry.email,
                    "revoked_at": revoked_at.isoformat(),
                },
            )
            self._repo.commit()
            self._repo.refresh(entry)
            logger.info(
                "admin.allowlist.revoked",
                email=entry.email,
                actor_id=str(actor.id),
            )

        return self._entry_response(entry)
