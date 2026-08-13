import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from diem10_api.core.logging import get_logger
from diem10_api.models import AuditLog, User
from diem10_api.repositories.draft_repository import DraftRepository
from diem10_api.schemas.admin_draft import (
    ArchiveExamResponse,
    DraftPublishRequest,
    DraftPublishResponse,
    ValidationResultResponse,
)
from diem10_api.services.draft_service import DraftService
from diem10_api.services.publish_validation import ValidationResult

logger = get_logger("publish_service")


class PublishService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = DraftRepository(session)
        self._drafts = DraftService(session)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def validate_draft(self, version_id: uuid.UUID) -> ValidationResultResponse:
        return self._drafts.validate_draft(version_id)

    def publish_draft(
        self,
        version_id: uuid.UUID,
        payload: DraftPublishRequest,
        actor: User,
        client_ip: str | None,
    ) -> DraftPublishResponse:
        version = self._repo.get_version(version_id)
        if version is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if version.status not in {"draft", "in_review"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chỉ có thể xuất bản bản nháp",
            )
        if not DraftService.timestamps_match(payload.expected_updated_at, version.updated_at):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bản nháp đã được cập nhật bởi phiên khác. Hãy tải lại.",
            )

        validation = self._drafts.build_validation_result(version)
        self._ensure_publishable(validation, payload.acknowledge_warnings)

        exam = self._repo.get_exam(version.exam_id)
        if exam is None or exam.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        published = self._repo.get_published_version(exam.id)
        before_data = {
            "exam_id": str(exam.id),
            "draft_version_id": str(version.id),
            "published_version_id": str(published.id) if published else None,
        }

        try:
            if published is not None and published.id != version.id:
                published.status = "archived"
            published_at = self._now()
            version.status = "published"
            version.published_at = published_at
            _job, _asset, findings = self._repo.get_import_context(version.id)
            if payload.acknowledge_warnings:
                self._repo.resolve_findings(findings, actor.id)
            self._repo.add_audit_log(
                AuditLog(
                    actor_user_id=actor.id,
                    action="exam.publish",
                    target_type="exam_version",
                    target_id=version.id,
                    request_id=None,
                    ip_address=client_ip,
                    before_data=before_data,
                    after_data={
                        "exam_id": str(exam.id),
                        "exam_slug": exam.slug,
                        "version_id": str(version.id),
                        "published_at": published_at.isoformat(),
                    },
                )
            )
            self._repo.commit()
            self._repo.refresh(version)
        except Exception:
            self._repo.rollback()
            self._repo.add_audit_log(
                AuditLog(
                    actor_user_id=actor.id,
                    action="exam.publish.failed",
                    target_type="exam_version",
                    target_id=version.id,
                    request_id=None,
                    ip_address=client_ip,
                    before_data=before_data,
                    after_data={"error": "transaction_failed"},
                )
            )
            self._repo.commit()
            raise

        logger.info(
            "admin.exam.published",
            exam_id=str(exam.id),
            version_id=str(version.id),
            actor_id=str(actor.id),
        )
        return DraftPublishResponse(
            exam_id=str(exam.id),
            exam_slug=exam.slug,
            version_id=str(version.id),
            published_at=published_at,
        )

    def archive_exam(
        self,
        exam_id: uuid.UUID,
        actor: User,
        client_ip: str | None,
    ) -> ArchiveExamResponse:
        exam = self._repo.get_exam(exam_id)
        if exam is None or exam.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        published = self._repo.get_published_version(exam.id)
        if published is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Đề chưa được xuất bản",
            )

        before_data = {
            "exam_id": str(exam.id),
            "published_version_id": str(published.id),
        }
        published.status = "archived"
        self._repo.add_audit_log(
            AuditLog(
                actor_user_id=actor.id,
                action="exam.archive",
                target_type="exam",
                target_id=exam.id,
                request_id=None,
                ip_address=client_ip,
                before_data=before_data,
                after_data={
                    "exam_id": str(exam.id),
                    "archived_version_id": str(published.id),
                },
            )
        )
        self._repo.commit()
        self._repo.refresh(published)
        logger.info(
            "admin.exam.archived",
            exam_id=str(exam.id),
            version_id=str(published.id),
            actor_id=str(actor.id),
        )
        return ArchiveExamResponse(
            exam_id=str(exam.id),
            exam_slug=exam.slug,
            archived_version_id=str(published.id),
        )

    @staticmethod
    def _ensure_publishable(
        validation: ValidationResult,
        acknowledge_warnings: bool,
    ) -> None:
        if validation.error_count > 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "message": "Bản nháp chưa đạt điều kiện xuất bản",
                    "errors": [
                        {
                            "field_path": issue.field_path,
                            "message": issue.message,
                            "question_id": issue.question_id,
                            "part_number": issue.part_number,
                            "part_position": issue.part_position,
                        }
                        for issue in validation.errors
                    ],
                    "warnings": [
                        {
                            "field_path": issue.field_path,
                            "message": issue.message,
                        }
                        for issue in validation.warnings
                    ],
                },
            )
        if validation.warning_count > 0 and not acknowledge_warnings:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "message": "Còn cảnh báo cần được xác nhận trước khi xuất bản",
                    "warnings": [
                        {
                            "field_path": issue.field_path,
                            "message": issue.message,
                        }
                        for issue in validation.warnings
                    ],
                },
            )
