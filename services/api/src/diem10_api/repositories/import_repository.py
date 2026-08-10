import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

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
)


class ImportRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_asset(self, asset_id: uuid.UUID) -> Asset | None:
        return self._session.get(Asset, asset_id)

    def list_source_documents(self) -> list[Asset]:
        return list(
            self._session.scalars(
                select(Asset)
                .where(
                    Asset.asset_kind == "source_document",
                    Asset.deleted_at.is_(None),
                )
                .order_by(Asset.created_at.desc())
            ).all()
        )

    def get_succeeded_import_job(
        self,
        source_asset_id: uuid.UUID,
        idempotency_key: str,
    ) -> ImportJob | None:
        return self._session.scalar(
            select(ImportJob).where(
                ImportJob.source_asset_id == source_asset_id,
                ImportJob.idempotency_key == idempotency_key,
                ImportJob.status == "succeeded",
            )
        )

    def get_exam_by_slug(self, slug: str) -> Exam | None:
        return self._session.scalar(select(Exam).where(Exam.slug == slug))

    def add_import_job(self, job: ImportJob) -> ImportJob:
        self._session.add(job)
        self._session.flush()
        return job

    def add_finding(self, finding: ImportFinding) -> None:
        self._session.add(finding)

    def add_exam(self, exam: Exam) -> Exam:
        self._session.add(exam)
        self._session.flush()
        return exam

    def add_exam_version(self, version: ExamVersion) -> ExamVersion:
        self._session.add(version)
        self._session.flush()
        return version

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

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self._session.add(audit_log)

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def refresh(self, instance: object) -> None:
        self._session.refresh(instance)
