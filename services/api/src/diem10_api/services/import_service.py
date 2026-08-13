import re
import unicodedata
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import UTC, datetime
from pathlib import PurePath

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from diem10_api.core.logging import get_logger
from diem10_api.core.option_labels import mc_position_from_label, tf_position_from_label
from diem10_api.models import (
    Asset,
    AssetLink,
    AuditLog,
    Exam,
    ExamVersion,
    ImportFinding,
    ImportJob,
    Question,
    QuestionOption,
    QuestionStatement,
    User,
)
from diem10_api.parsers import (
    OcrNotSupportedError,
    UnsupportedSourceDocumentError,
    parse_source,
)
from diem10_api.parsers.types import ParsedExamDraft, ParserFinding
from diem10_api.repositories.import_repository import ImportRepository
from diem10_api.schemas.admin import (
    ImportFindingResponse,
    ImportJobResponse,
    ImportSummary,
)
from diem10_api.storage import (
    MAX_SOURCE_DOCUMENT_BYTES,
    StorageConfigurationError,
    download_object,
    get_r2_settings,
)

IMPORT_TIMEOUT_SECONDS = 120
logger = get_logger("import_service")


class ImportService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = ImportRepository(session)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _slugify(value: str) -> str:
        text = unicodedata.normalize("NFC", value).strip().lower()
        text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
        text = re.sub(r"[\s_]+", "-", text)
        text = re.sub(r"-+", "-", text).strip("-")
        return text or "de-import"

    def _unique_exam_slug(self, title: str) -> str:
        base_slug = self._slugify(title)[:140]
        slug = base_slug
        suffix = 2
        while self._repo.get_exam_by_slug(slug) is not None:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        return slug

    @staticmethod
    def _fallback_title(asset: object) -> str:
        object_key = getattr(asset, "object_key", "")
        return PurePath(str(object_key)).stem or "Bản nháp import"

    def list_source_documents(self) -> list[Asset]:
        return self._repo.list_source_documents()

    def import_source_document(
        self,
        asset_id: uuid.UUID,
        actor: User,
        idempotency_key: str | None,
        client_ip: str | None,
    ) -> ImportJobResponse:
        asset = self._repo.get_asset(asset_id)
        if asset is None or asset.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if asset.asset_kind != "source_document":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Asset is not a source document",
            )
        if asset.size_bytes > MAX_SOURCE_DOCUMENT_BYTES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Source document exceeds size limit",
            )

        resolved_key = idempotency_key or asset.checksum_sha256
        existing_job = self._repo.get_succeeded_import_job(asset_id, resolved_key)
        if existing_job is not None and existing_job.exam_version_id is not None:
            findings = self._load_findings(existing_job.id)
            part1_count, part2_count = self._count_questions(existing_job.exam_version_id)
            return self._job_response(
                existing_job,
                findings,
                part1_count=part1_count,
                part2_count=part2_count,
            )

        started_at = self._now()
        job = ImportJob(
            source_asset_id=asset.id,
            status="running",
            idempotency_key=resolved_key,
            requested_by_user_id=actor.id,
            started_at=started_at,
        )
        self._repo.add_import_job(job)

        try:
            settings = get_r2_settings()
            content = download_object(asset.object_key, asset.bucket, settings)
        except (StorageConfigurationError, OSError, ValueError) as error:
            return self._fail_job(
                job=job,
                error_code="storage_download_failed",
                message=str(error),
                actor=actor,
                client_ip=client_ip,
            )

        try:
            draft = self._parse_with_timeout(
                content=content,
                mime_type=asset.mime_type,
                fallback_title=self._fallback_title(asset),
            )
        except FuturesTimeoutError:
            return self._fail_job(
                job=job,
                error_code="timed_out",
                message="Import processing exceeded time limit",
                actor=actor,
                client_ip=client_ip,
                status_value="timed_out",
            )
        except OcrNotSupportedError as error:
            return self._fail_job(
                job=job,
                error_code="ocr_not_supported",
                message=str(error),
                actor=actor,
                client_ip=client_ip,
            )
        except UnsupportedSourceDocumentError as error:
            return self._fail_job(
                job=job,
                error_code="unsupported_document",
                message=str(error),
                actor=actor,
                client_ip=client_ip,
            )
        except Exception as error:
            logger.exception("import.parse_failed", asset_id=str(asset_id))
            return self._fail_job(
                job=job,
                error_code="parser_error",
                message=str(error),
                actor=actor,
                client_ip=client_ip,
            )

        self._persist_findings(job, draft.findings)

        if not draft.is_safe_to_persist:
            job.status = "failed"
            job.error_code = "unsafe_parse_result"
            job.completed_at = self._now()
            self._repo.add_audit_log(
                AuditLog(
                    actor_user_id=actor.id,
                    action="admin.import.failed",
                    target_type="import_job",
                    target_id=job.id,
                    request_id=None,
                    ip_address=client_ip,
                    before_data=None,
                    after_data={
                        "source_asset_id": str(asset.id),
                        "error_code": job.error_code,
                    },
                )
            )
            self._repo.commit()
            self._repo.refresh(job)
            return self._job_response(
                job,
                draft.findings,
                part1_count=len(draft.part1_questions),
                part2_count=len(draft.part2_questions),
            )

        exam_version = self._persist_draft(draft, actor)
        self._repo.add_asset_link(
            AssetLink(
                asset_id=asset.id,
                exam_version_id=exam_version.id,
                question_id=None,
                purpose="source_document",
            )
        )
        job.exam_version_id = exam_version.id
        job.status = "succeeded"
        job.completed_at = self._now()
        self._repo.add_audit_log(
            AuditLog(
                actor_user_id=actor.id,
                action="admin.import.succeeded",
                target_type="import_job",
                target_id=job.id,
                request_id=None,
                ip_address=client_ip,
                before_data=None,
                after_data={
                    "source_asset_id": str(asset.id),
                    "exam_version_id": str(exam_version.id),
                },
            )
        )
        self._repo.commit()
        self._repo.refresh(job)
        logger.info(
            "import.succeeded",
            import_job_id=str(job.id),
            exam_version_id=str(exam_version.id),
            asset_id=str(asset.id),
        )
        return self._job_response(
            job,
            draft.findings,
            part1_count=len(draft.part1_questions),
            part2_count=len(draft.part2_questions),
        )

    def _parse_with_timeout(
        self,
        *,
        content: bytes,
        mime_type: str,
        fallback_title: str,
    ) -> ParsedExamDraft:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                parse_source,
                content,
                mime_type,
                fallback_title=fallback_title,
            )
            result: ParsedExamDraft = future.result(timeout=IMPORT_TIMEOUT_SECONDS)
            return result

    def _persist_draft(self, draft: ParsedExamDraft, actor: User) -> ExamVersion:
        exam = Exam(
            slug=self._unique_exam_slug(draft.title),
            created_by_user_id=actor.id,
        )
        self._repo.add_exam(exam)
        version = ExamVersion(
            exam_id=exam.id,
            version_number=1,
            status="draft",
            title=draft.title[:255],
            summary=draft.summary,
            year=draft.year,
            difficulty=draft.difficulty[:50],
            duration_minutes=draft.duration_minutes,
            published_at=None,
            created_by_user_id=actor.id,
        )
        self._repo.add_exam_version(version)

        for mc_question in draft.part1_questions:
            position = mc_question.part_position
            question = Question(
                exam_version_id=version.id,
                position=position,
                part_number=1,
                part_position=mc_question.part_position,
                question_type="multiple_choice",
                body=mc_question.body,
                source_text=None,
                explanation=mc_question.explanation,
            )
            self._repo.add_question(question)
            for option in mc_question.options:
                self._repo.add_option(
                    QuestionOption(
                        question_id=question.id,
                        position=mc_position_from_label(option.label),
                        body=option.body,
                        is_correct=option.is_correct,
                    )
                )

        for tf_question in draft.part2_questions:
            position = 24 + tf_question.part_position
            question = Question(
                exam_version_id=version.id,
                position=position,
                part_number=2,
                part_position=tf_question.part_position,
                question_type="true_false_group",
                body=tf_question.body,
                source_text=tf_question.source_text,
                explanation=tf_question.explanation,
            )
            self._repo.add_question(question)
            for statement in tf_question.statements:
                self._repo.add_statement(
                    QuestionStatement(
                        question_id=question.id,
                        position=tf_position_from_label(statement.label),
                        body=statement.body,
                        is_correct=bool(statement.is_correct),
                    )
                )
        return version

    def _persist_findings(
        self,
        job: ImportJob,
        findings: list[ParserFinding],
    ) -> None:
        for finding in findings:
            self._repo.add_finding(
                ImportFinding(
                    import_job_id=job.id,
                    severity=finding.severity,
                    field_path=finding.field_path,
                    message=finding.message,
                    raw_value=finding.raw_value,
                )
            )

    def _load_findings(self, import_job_id: uuid.UUID) -> list[ParserFinding]:
        rows = self._session.scalars(
            select(ImportFinding).where(ImportFinding.import_job_id == import_job_id)
        ).all()
        return [
            ParserFinding(
                severity=row.severity,  # type: ignore[arg-type]
                field_path=row.field_path,
                message=row.message,
                raw_value=row.raw_value,
            )
            for row in rows
        ]

    def _count_questions(
        self,
        exam_version_id: uuid.UUID,
    ) -> tuple[int, int]:
        rows = self._session.scalars(
            select(Question).where(Question.exam_version_id == exam_version_id)
        ).all()
        part1 = sum(1 for row in rows if row.part_number == 1)
        part2 = sum(1 for row in rows if row.part_number == 2)
        return part1, part2

    @staticmethod
    def _job_response(
        job: ImportJob,
        findings: list[ParserFinding],
        *,
        part1_count: int = 0,
        part2_count: int = 0,
    ) -> ImportJobResponse:
        warnings = sum(1 for finding in findings if finding.severity == "warning")
        errors = sum(1 for finding in findings if finding.severity == "error")
        return ImportJobResponse(
            import_job_id=str(job.id),
            exam_version_id=(
                str(job.exam_version_id) if job.exam_version_id is not None else None
            ),
            status=job.status,
            error_code=job.error_code,
            findings=[
                ImportFindingResponse(
                    severity=finding.severity,
                    field_path=finding.field_path,
                    message=finding.message,
                    raw_value=finding.raw_value,
                )
                for finding in findings
            ],
            summary=ImportSummary(
                part1_count=part1_count,
                part2_count=part2_count,
                warnings=warnings,
                errors=errors,
            ),
        )

    def _fail_job(
        self,
        *,
        job: ImportJob,
        error_code: str,
        message: str,
        actor: User,
        client_ip: str | None,
        status_value: str = "failed",
    ) -> ImportJobResponse:
        job.status = status_value
        job.error_code = error_code
        job.completed_at = self._now()
        self._repo.add_finding(
            ImportFinding(
                import_job_id=job.id,
                severity="error",
                field_path="_document",
                message=message,
                raw_value=error_code,
            )
        )
        self._repo.add_audit_log(
            AuditLog(
                actor_user_id=actor.id,
                action="admin.import.failed",
                target_type="import_job",
                target_id=job.id,
                request_id=None,
                ip_address=client_ip,
                before_data=None,
                after_data={
                    "source_asset_id": str(job.source_asset_id),
                    "error_code": error_code,
                },
            )
        )
        self._repo.commit()
        self._repo.refresh(job)
        findings = self._load_findings(job.id)
        return self._job_response(job, findings)
