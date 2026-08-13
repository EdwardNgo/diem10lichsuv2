import uuid
from datetime import UTC, datetime
from pathlib import PurePath

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from diem10_api.core.logging import get_logger
from diem10_api.core.option_labels import (
    mc_label_from_position,
    tf_label_from_position,
)
from diem10_api.models import (
    Asset,
    AssetLink,
    AuditLog,
    Question,
    QuestionOption,
    QuestionStatement,
    User,
)
from diem10_api.repositories.draft_repository import DraftRepository
from diem10_api.schemas.admin_draft import (
    DraftDetailResponse,
    DraftImportContextResponse,
    DraftImportFindingResponse,
    DraftMetadataUpdate,
    DraftPage,
    DraftQuestionInput,
    DraftQuestionOptionResponse,
    DraftQuestionResponse,
    DraftQuestionStatementResponse,
    DraftQuestionsUpdate,
    DraftSummary,
    ValidationIssueResponse,
    ValidationResultResponse,
)
from diem10_api.services.publish_validation import (
    ValidationResult,
    validate_draft_for_publish,
)
from diem10_api.storage import (
    StorageConfigurationError,
    create_presigned_download,
    get_r2_settings,
)

logger = get_logger("draft_service")

EDITABLE_STATUSES = frozenset({"draft", "in_review"})


class DraftService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = DraftRepository(session)

    @staticmethod
    def timestamps_match(expected: datetime, actual: datetime) -> bool:
        if expected.tzinfo is None:
            expected = expected.replace(tzinfo=UTC)
        if actual.tzinfo is None:
            actual = actual.replace(tzinfo=UTC)
        return abs((expected - actual).total_seconds()) < 1

    def _ensure_version_lock(self, version: object, expected_updated_at: datetime) -> None:
        if not self.timestamps_match(expected_updated_at, version.updated_at):  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bản nháp đã được cập nhật bởi phiên khác. Hãy tải lại.",
            )

    def _ensure_editable(self, version_id: uuid.UUID) -> tuple[object, object]:
        version = self._repo.get_version(version_id)
        if version is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if version.status not in EDITABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chỉ có thể sửa bản nháp. Tạo bản nháp mới để chỉnh sửa đề đã xuất bản.",
            )
        exam = self._repo.get_exam(version.exam_id)
        if exam is None or exam.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return version, exam

    def list_drafts(
        self,
        *,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> DraftPage:
        rows, total = self._repo.list_draft_versions(
            status=status_filter,
            page=page,
            page_size=page_size,
        )
        items: list[DraftSummary] = []
        for version, exam in rows:
            questions = self._repo.list_active_questions(version.id)
            part1 = sum(1 for question in questions if question.part_number == 1)
            part2 = sum(1 for question in questions if question.part_number == 2)
            _, _, findings = self._repo.get_import_context(version.id)
            unresolved_warnings = sum(
                1
                for finding in findings
                if finding.resolved_at is None and finding.severity == "warning"
            )
            items.append(
                DraftSummary(
                    id=str(version.id),
                    exam_id=str(exam.id),
                    exam_slug=exam.slug,
                    title=version.title,
                    status=version.status,
                    updated_at=version.updated_at,
                    part1_count=part1,
                    part2_count=part2,
                    import_warnings=unresolved_warnings or None,
                )
            )
        return DraftPage(items=items, page=page, page_size=page_size, total=total)

    def get_draft(self, version_id: uuid.UUID) -> DraftDetailResponse:
        version = self._repo.get_version(version_id)
        if version is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        exam = self._repo.get_exam(version.exam_id)
        if exam is None or exam.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        questions = self._repo.list_active_questions(version.id)
        question_ids = [question.id for question in questions]
        options = self._repo.list_active_options(question_ids)
        statements = self._repo.list_active_statements(question_ids)
        options_by_question: dict[uuid.UUID, list[QuestionOption]] = {}
        for option in options:
            options_by_question.setdefault(option.question_id, []).append(option)
        statements_by_question: dict[uuid.UUID, list[QuestionStatement]] = {}
        for statement in statements:
            statements_by_question.setdefault(statement.question_id, []).append(
                statement
            )

        primary_topic = self._repo.get_primary_topic(version.id)
        import_context = self._build_import_context(version.id)

        return DraftDetailResponse(
            id=str(version.id),
            exam_id=str(exam.id),
            exam_slug=exam.slug,
            version_number=version.version_number,
            status=version.status,
            title=version.title,
            summary=version.summary,
            year=version.year,
            difficulty=version.difficulty,
            duration_minutes=version.duration_minutes,
            primary_topic_id=str(primary_topic.id) if primary_topic else None,
            primary_topic_name=primary_topic.name if primary_topic else None,
            updated_at=version.updated_at,
            questions=[
                self._question_response(
                    question,
                    options_by_question.get(question.id, []),
                    statements_by_question.get(question.id, []),
                )
                for question in questions
            ],
            import_context=import_context,
        )

    def get_import_context(self, version_id: uuid.UUID) -> DraftImportContextResponse:
        version = self._repo.get_version(version_id)
        if version is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return self._build_import_context(version_id)

    def update_metadata(
        self,
        version_id: uuid.UUID,
        payload: DraftMetadataUpdate,
        actor: User,
    ) -> DraftDetailResponse:
        version, _exam = self._ensure_editable(version_id)
        self._ensure_version_lock(version, payload.expected_updated_at)

        if payload.title is not None:
            version.title = payload.title.strip()[:255]  # type: ignore[attr-defined]
        if payload.summary is not None:
            version.summary = payload.summary  # type: ignore[attr-defined]
        if payload.year is not None:
            version.year = payload.year  # type: ignore[attr-defined]
        if payload.difficulty is not None:
            version.difficulty = payload.difficulty.strip()[:50]  # type: ignore[attr-defined]
        if payload.duration_minutes is not None:
            version.duration_minutes = payload.duration_minutes  # type: ignore[attr-defined]
        if payload.primary_topic_id is not None:
            topic = self._repo.get_topic(uuid.UUID(payload.primary_topic_id))
            if topic is None or not topic.is_active:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Chủ đề không hợp lệ",
                )
            self._repo.set_primary_topic(version.id, topic.id)  # type: ignore[attr-defined]

        _job, _asset, findings = self._repo.get_import_context(version.id)  # type: ignore[attr-defined]
        resolved_paths: set[str] = set()
        if payload.summary is not None and payload.summary.strip():
            resolved_paths.add("metadata.summary")
        if payload.primary_topic_id is not None:
            resolved_paths.add("metadata.topic")
            resolved_paths.add("metadata.primary_topic_id")
        if payload.year is not None:
            resolved_paths.add("metadata.year")
        if payload.difficulty is not None and payload.difficulty.strip() not in {
            "",
            "Chưa phân loại",
        }:
            resolved_paths.add("metadata.difficulty")
        to_resolve = [
            finding
            for finding in findings
            if finding.resolved_at is None and finding.field_path in resolved_paths
        ]
        if to_resolve:
            self._repo.resolve_findings(to_resolve, actor.id)

        self._repo.commit()
        self._repo.refresh(version)
        logger.info(
            "admin.draft.metadata_updated",
            version_id=str(version_id),
            actor_id=str(actor.id),
        )
        return self.get_draft(version_id)

    def update_questions(
        self,
        version_id: uuid.UUID,
        payload: DraftQuestionsUpdate,
        actor: User,
    ) -> DraftDetailResponse:
        version, _exam = self._ensure_editable(version_id)
        self._ensure_version_lock(version, payload.expected_updated_at)

        existing_questions = self._repo.list_active_questions(version.id)  # type: ignore[attr-defined]
        existing_by_key = {
            (question.part_number, question.part_position): question
            for question in existing_questions
        }
        existing_by_id = {str(question.id): question for question in existing_questions}
        seen_keys: set[tuple[int, int]] = set()

        for question_input in payload.questions:
            key = (question_input.part_number, question_input.part_position)
            if key in seen_keys:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Trùng vị trí câu hỏi",
                )
            seen_keys.add(key)
            question = self._resolve_question(
                version.id,  # type: ignore[attr-defined]
                question_input,
                existing_by_key,
                existing_by_id,
            )
            self._sync_question_children(question, question_input)

        for key, question in existing_by_key.items():
            if key not in seen_keys:
                self._soft_delete_question_tree(question)

        self._repo.commit()
        self._repo.refresh(version)
        logger.info(
            "admin.draft.questions_updated",
            version_id=str(version_id),
            actor_id=str(actor.id),
        )
        return self.get_draft(version_id)

    def validate_draft(self, version_id: uuid.UUID) -> ValidationResultResponse:
        version = self._repo.get_version(version_id)
        if version is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if version.status not in EDITABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chỉ có thể kiểm tra bản nháp",
            )
        result = self._validation_result(version)
        return self._validation_response(result)

    def link_question_image(
        self,
        version_id: uuid.UUID,
        question_id: uuid.UUID,
        asset_id: uuid.UUID,
        actor: User,
        client_ip: str | None,
    ) -> DraftDetailResponse:
        version, _exam = self._ensure_editable(version_id)
        question = self._repo.get_question(question_id)
        if (
            question is None
            or question.deleted_at is not None
            or question.exam_version_id != version.id  # type: ignore[attr-defined]
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        asset = self._repo.get_asset(asset_id)
        if (
            asset is None
            or asset.deleted_at is not None
            or asset.asset_kind != "question_image"
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Ảnh không hợp lệ",
            )
        existing = self._repo.get_question_image_link(question_id)
        if existing is not None:
            self._session.delete(existing)
        self._repo.add_asset_link(
            AssetLink(
                asset_id=asset.id,
                question_id=question.id,
                purpose="question_image",
            )
        )
        self._repo.add_audit_log(
            AuditLog(
                actor_user_id=actor.id,
                action="exam.question_image.link",
                target_type="question",
                target_id=question.id,
                request_id=None,
                ip_address=client_ip,
                before_data=None,
                after_data={
                    "version_id": str(version_id),
                    "asset_id": str(asset.id),
                },
            )
        )
        self._repo.commit()
        logger.info(
            "admin.draft.question_image_linked",
            version_id=str(version_id),
            question_id=str(question_id),
            asset_id=str(asset_id),
            actor_id=str(actor.id),
        )
        return self.get_draft(version_id)

    def unlink_question_image(
        self,
        version_id: uuid.UUID,
        question_id: uuid.UUID,
        actor: User,
        client_ip: str | None,
    ) -> DraftDetailResponse:
        version, _exam = self._ensure_editable(version_id)
        question = self._repo.get_question(question_id)
        if (
            question is None
            or question.deleted_at is not None
            or question.exam_version_id != version.id  # type: ignore[attr-defined]
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        existing = self._repo.get_question_image_link(question_id)
        if existing is not None:
            self._session.delete(existing)
            self._repo.add_audit_log(
                AuditLog(
                    actor_user_id=actor.id,
                    action="exam.question_image.unlink",
                    target_type="question",
                    target_id=question.id,
                    request_id=None,
                    ip_address=client_ip,
                    before_data={"asset_id": str(existing.asset_id)},
                    after_data=None,
                )
            )
        self._repo.commit()
        return self.get_draft(version_id)

    def build_validation_result(self, version: object) -> ValidationResult:
        return self._validation_result(version)

    def _validation_result(self, version: object) -> ValidationResult:
        questions = self._repo.list_active_questions(version.id)  # type: ignore[attr-defined]
        question_ids = [question.id for question in questions]
        options = self._repo.list_active_options(question_ids)
        statements = self._repo.list_active_statements(question_ids)
        options_by_question: dict[object, list[QuestionOption]] = {}
        for option in options:
            options_by_question.setdefault(option.question_id, []).append(option)
        statements_by_question: dict[object, list[QuestionStatement]] = {}
        for statement in statements:
            statements_by_question.setdefault(statement.question_id, []).append(
                statement
            )
        primary_topic = self._repo.get_primary_topic(version.id)  # type: ignore[attr-defined]
        _job, _asset, findings = self._repo.get_import_context(version.id)  # type: ignore[attr-defined]
        return validate_draft_for_publish(
            version,  # type: ignore[arg-type]
            questions=questions,
            options_by_question=options_by_question,
            statements_by_question=statements_by_question,
            primary_topic=primary_topic,
            unresolved_findings=findings,
        )

    def _resolve_question(
        self,
        version_id: uuid.UUID,
        question_input: DraftQuestionInput,
        existing_by_key: dict[tuple[int, int], Question],
        existing_by_id: dict[str, Question],
    ) -> Question:
        question: Question | None = None
        if question_input.id is not None:
            question = existing_by_id.get(question_input.id)
        if question is None:
            question = existing_by_key.get(
                (question_input.part_number, question_input.part_position)
            )
        if question is None:
            question = Question(
                exam_version_id=version_id,
                position=question_input.position,
                part_number=question_input.part_number,
                part_position=question_input.part_position,
                question_type=question_input.question_type,
                body=question_input.body,
                source_text=question_input.source_text,
                explanation=question_input.explanation,
            )
            self._repo.add_question(question)
            return question

        question.position = question_input.position
        question.part_number = question_input.part_number
        question.part_position = question_input.part_position
        question.question_type = question_input.question_type
        question.body = question_input.body
        question.source_text = question_input.source_text
        question.explanation = question_input.explanation
        return question

    def _sync_question_children(
        self,
        question: Question,
        question_input: DraftQuestionInput,
    ) -> None:
        if question_input.question_type == "multiple_choice":
            existing_options = self._repo.list_active_options([question.id])
            existing_by_position = {option.position: option for option in existing_options}
            seen_positions: set[int] = set()
            for option_input in question_input.options:
                seen_positions.add(option_input.position)
                option = existing_by_position.get(option_input.position)
                if option is None:
                    self._repo.add_option(
                        QuestionOption(
                            question_id=question.id,
                            position=option_input.position,
                            body=option_input.body,
                            is_correct=option_input.is_correct,
                        )
                    )
                else:
                    option.body = option_input.body
                    option.is_correct = option_input.is_correct
            for position, option in existing_by_position.items():
                if position not in seen_positions:
                    self._repo.soft_delete_option(option)
            existing_statements = self._repo.list_active_statements([question.id])
            for statement in existing_statements:
                self._repo.soft_delete_statement(statement)
            return

        existing_options = self._repo.list_active_options([question.id])
        for option in existing_options:
            self._repo.soft_delete_option(option)
        existing_statements = self._repo.list_active_statements([question.id])
        existing_by_position = {
            statement.position: statement for statement in existing_statements
        }
        seen_positions: set[int] = set()
        for statement_input in question_input.statements:
            seen_positions.add(statement_input.position)
            statement = existing_by_position.get(statement_input.position)
            if statement is None:
                self._repo.add_statement(
                    QuestionStatement(
                        question_id=question.id,
                        position=statement_input.position,
                        body=statement_input.body,
                        is_correct=statement_input.is_correct,
                    )
                )
            else:
                statement.body = statement_input.body
                statement.is_correct = statement_input.is_correct
        for position, statement in existing_by_position.items():
            if position not in seen_positions:
                self._repo.soft_delete_statement(statement)

    def _soft_delete_question_tree(self, question: Question) -> None:
        for option in self._repo.list_active_options([question.id]):
            self._repo.soft_delete_option(option)
        for statement in self._repo.list_active_statements([question.id]):
            self._repo.soft_delete_statement(statement)
        self._repo.soft_delete_question(question)

    def _question_response(
        self,
        question: Question,
        options: list[QuestionOption],
        statements: list[QuestionStatement],
    ) -> DraftQuestionResponse:
        image_link = self._repo.get_question_image_link(question.id)
        image_response = None
        if image_link is not None:
            asset = self._repo.get_asset(image_link.asset_id)
            if asset is not None and asset.deleted_at is None:
                image_response = {
                    "asset_id": str(asset.id),
                    "mime_type": asset.mime_type,
                    "download_url": self._optional_download_url(asset),
                }
        return DraftQuestionResponse(
            id=str(question.id),
            position=question.position,
            part_number=question.part_number,
            part_position=question.part_position,
            question_type=question.question_type,
            body=question.body,
            source_text=question.source_text,
            explanation=question.explanation,
            options=[
                DraftQuestionOptionResponse(
                    id=str(option.id),
                    position=option.position,
                    label=mc_label_from_position(option.position),
                    body=option.body,
                    is_correct=option.is_correct,
                )
                for option in options
            ],
            statements=[
                DraftQuestionStatementResponse(
                    id=str(statement.id),
                    position=statement.position,
                    label=tf_label_from_position(statement.position),
                    body=statement.body,
                    is_correct=statement.is_correct,
                )
                for statement in statements
            ],
            image=image_response,  # type: ignore[arg-type]
        )

    def _build_import_context(
        self,
        version_id: uuid.UUID,
    ) -> DraftImportContextResponse | None:
        job, asset, findings = self._repo.get_import_context(version_id)
        if job is None and asset is None and not findings:
            return None
        download_url = self._optional_download_url(asset) if asset else None
        return DraftImportContextResponse(
            import_job_id=str(job.id) if job else None,
            source_asset_id=str(asset.id) if asset else None,
            source_filename=(
                PurePath(asset.object_key).name if asset is not None else None
            ),
            source_mime_type=asset.mime_type if asset else None,
            source_download_url=download_url,
            findings=[
                DraftImportFindingResponse(
                    id=str(finding.id),
                    severity=finding.severity,
                    field_path=finding.field_path,
                    message=finding.message,
                    resolved_at=finding.resolved_at,
                )
                for finding in findings
            ],
        )

    def _optional_download_url(self, asset: Asset) -> str | None:
        try:
            settings = get_r2_settings()
        except StorageConfigurationError:
            return None
        if asset.bucket != settings.bucket_name:
            return None
        return create_presigned_download(asset.object_key, settings)

    @staticmethod
    def _validation_response(result: ValidationResult) -> ValidationResultResponse:
        def to_issue(issue: object) -> ValidationIssueResponse:
            return ValidationIssueResponse(
                severity=issue.severity,  # type: ignore[attr-defined]
                field_path=issue.field_path,  # type: ignore[attr-defined]
                message=issue.message,  # type: ignore[attr-defined]
                question_id=issue.question_id,  # type: ignore[attr-defined]
                part_number=issue.part_number,  # type: ignore[attr-defined]
                part_position=issue.part_position,  # type: ignore[attr-defined]
            )

        return ValidationResultResponse(
            valid=result.valid,
            errors=[to_issue(issue) for issue in result.errors],
            warnings=[to_issue(issue) for issue in result.warnings],
        )
