import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from diem10_api.models import (
    Asset,
    AssetLink,
    AuditLog,
    Exam,
    ExamVersion,
    ExamVersionTopic,
    ImportFinding,
    ImportJob,
    Question,
    QuestionOption,
    QuestionStatement,
    Topic,
)


class DraftRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def list_draft_versions(
        self,
        *,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[ExamVersion, Exam]], int]:
        query = (
            select(ExamVersion, Exam)
            .join(Exam, Exam.id == ExamVersion.exam_id)
            .where(Exam.deleted_at.is_(None))
            .where(ExamVersion.status.in_(("draft", "in_review")))
        )
        if status is not None:
            query = query.where(ExamVersion.status == status)
        query = query.order_by(ExamVersion.updated_at.desc())
        total = (
            self._session.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )
        rows = list(
            self._session.execute(
                query.offset((page - 1) * page_size).limit(page_size)
            ).all()
        )
        return [(row[0], row[1]) for row in rows], total

    def get_version(self, version_id: uuid.UUID) -> ExamVersion | None:
        return self._session.get(ExamVersion, version_id)

    def get_exam(self, exam_id: uuid.UUID) -> Exam | None:
        return self._session.get(Exam, exam_id)

    def get_published_version(self, exam_id: uuid.UUID) -> ExamVersion | None:
        return self._session.scalar(
            select(ExamVersion).where(
                ExamVersion.exam_id == exam_id,
                ExamVersion.status == "published",
            )
        )

    def get_primary_topic(self, version_id: uuid.UUID) -> Topic | None:
        return self._session.scalar(
            select(Topic)
            .join(ExamVersionTopic, ExamVersionTopic.topic_id == Topic.id)
            .where(ExamVersionTopic.exam_version_id == version_id)
            .where(ExamVersionTopic.is_primary.is_(True))
        )

    def get_primary_topic_link(
        self,
        version_id: uuid.UUID,
    ) -> ExamVersionTopic | None:
        return self._session.scalar(
            select(ExamVersionTopic).where(
                ExamVersionTopic.exam_version_id == version_id,
                ExamVersionTopic.is_primary.is_(True),
            )
        )

    def set_primary_topic(self, version_id: uuid.UUID, topic_id: uuid.UUID) -> None:
        existing_links = list(
            self._session.scalars(
                select(ExamVersionTopic).where(
                    ExamVersionTopic.exam_version_id == version_id
                )
            ).all()
        )
        for link in existing_links:
            if link.is_primary:
                self._session.delete(link)
        self._session.add(
            ExamVersionTopic(
                exam_version_id=version_id,
                topic_id=topic_id,
                is_primary=True,
            )
        )

    def list_active_questions(self, version_id: uuid.UUID) -> list[Question]:
        return list(
            self._session.scalars(
                select(Question)
                .where(
                    Question.exam_version_id == version_id,
                    Question.deleted_at.is_(None),
                )
                .order_by(
                    Question.part_number.asc(),
                    Question.part_position.asc(),
                    Question.position.asc(),
                )
            ).all()
        )

    def list_active_options(
        self,
        question_ids: list[uuid.UUID],
    ) -> list[QuestionOption]:
        if not question_ids:
            return []
        return list(
            self._session.scalars(
                select(QuestionOption)
                .where(
                    QuestionOption.question_id.in_(question_ids),
                    QuestionOption.deleted_at.is_(None),
                )
                .order_by(
                    QuestionOption.question_id.asc(),
                    QuestionOption.position.asc(),
                )
            ).all()
        )

    def list_active_statements(
        self,
        question_ids: list[uuid.UUID],
    ) -> list[QuestionStatement]:
        if not question_ids:
            return []
        return list(
            self._session.scalars(
                select(QuestionStatement)
                .where(
                    QuestionStatement.question_id.in_(question_ids),
                    QuestionStatement.deleted_at.is_(None),
                )
                .order_by(
                    QuestionStatement.question_id.asc(),
                    QuestionStatement.position.asc(),
                )
            ).all()
        )

    def get_question(self, question_id: uuid.UUID) -> Question | None:
        return self._session.get(Question, question_id)

    def get_topic(self, topic_id: uuid.UUID) -> Topic | None:
        return self._session.get(Topic, topic_id)

    def list_active_topics(self) -> list[Topic]:
        return list(
            self._session.scalars(
                select(Topic)
                .where(Topic.is_active.is_(True))
                .order_by(Topic.sort_order.asc(), Topic.name.asc())
            ).all()
        )

    def get_import_context(
        self,
        version_id: uuid.UUID,
    ) -> tuple[ImportJob | None, Asset | None, list[ImportFinding]]:
        job = self._session.scalar(
            select(ImportJob)
            .where(ImportJob.exam_version_id == version_id)
            .order_by(ImportJob.completed_at.desc())
            .limit(1)
        )
        asset_link = self._session.scalar(
            select(AssetLink).where(
                AssetLink.exam_version_id == version_id,
                AssetLink.purpose == "source_document",
            )
        )
        asset = None
        if asset_link is not None:
            asset = self._session.get(Asset, asset_link.asset_id)
        findings: list[ImportFinding] = []
        if job is not None:
            findings = list(
                self._session.scalars(
                    select(ImportFinding).where(
                        ImportFinding.import_job_id == job.id
                    )
                ).all()
            )
        return job, asset, findings

    def get_question_image_link(
        self,
        question_id: uuid.UUID,
    ) -> AssetLink | None:
        return self._session.scalar(
            select(AssetLink).where(
                AssetLink.question_id == question_id,
                AssetLink.purpose == "question_image",
            )
        )

    def get_asset(self, asset_id: uuid.UUID) -> Asset | None:
        return self._session.get(Asset, asset_id)

    def add_question(self, question: Question) -> Question:
        self._session.add(question)
        self._session.flush()
        return question

    def add_option(self, option: QuestionOption) -> None:
        self._session.add(option)

    def add_statement(self, statement: QuestionStatement) -> None:
        self._session.add(statement)

    def add_asset_link(self, link: AssetLink) -> None:
        self._session.add(link)

    def soft_delete_question(self, question: Question) -> None:
        question.deleted_at = self._now()

    def soft_delete_option(self, option: QuestionOption) -> None:
        option.deleted_at = self._now()

    def soft_delete_statement(self, statement: QuestionStatement) -> None:
        statement.deleted_at = self._now()

    def resolve_findings(
        self,
        findings: list[ImportFinding],
        actor_id: uuid.UUID,
    ) -> None:
        now = self._now()
        for finding in findings:
            if finding.resolved_at is None:
                finding.resolved_at = now
                finding.resolved_by_user_id = actor_id

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self._session.add(audit_log)

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def refresh(self, instance: object) -> None:
        self._session.refresh(instance)

    def flush(self) -> None:
        self._session.flush()
