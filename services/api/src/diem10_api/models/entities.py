import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    google_subject: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled')", name="users_status_check"),
    )


class AdminAllowlist(Base):
    __tablename__ = "admin_allowlist"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    added_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    request_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    before_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    after_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_audit_logs_target_created_at",
            "target_type",
            "target_id",
            "created_at",
        ),
    )


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    object_key: Mapped[str] = mapped_column(Text, unique=True)
    bucket: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True)
    asset_kind: Mapped[str] = mapped_column(String(30), index=True)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="assets_size_bytes_check"),
        CheckConstraint(
            "asset_kind IN ('source_document', 'question_image')",
            name="assets_kind_check",
        ),
    )


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_user_sessions_user_expires_at", "user_id", "expires_at"),
    )


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    code_verifier: Mapped[str] = mapped_column(String(128))
    return_to: Mapped[str] = mapped_column(String(2048))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    exam_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exam_versions.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_number: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'in_progress', 'submitted', 'expired_and_submitted', 'abandoned'"
            ")",
            name="attempts_status_check",
        ),
        CheckConstraint("expires_at > started_at", name="attempts_expires_at_check"),
        CheckConstraint("attempt_number > 0", name="attempts_number_check"),
        Index("ix_attempts_user_started_at", "user_id", "started_at"),
        Index(
            "uq_attempts_open_user_exam_version",
            "user_id",
            "exam_version_id",
            unique=True,
            postgresql_where=(status == "in_progress"),
            sqlite_where=(status == "in_progress"),
        ),
    )


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attempts.id"), primary_key=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id"), primary_key=True
    )
    selected_option_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("question_options.id")
    )
    is_marked_for_review: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_attempt_answers_attempt_updated_at", "attempt_id", "updated_at"),
    )


class AttemptStatementAnswer(Base):
    __tablename__ = "attempt_statement_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attempts.id"), primary_key=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"))
    statement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("question_statements.id"), primary_key=True
    )
    selected_value: Mapped[bool | None] = mapped_column(Boolean)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "ix_attempt_statement_answers_attempt_updated_at",
            "attempt_id",
            "updated_at",
        ),
    )


class AttemptResult(Base):
    __tablename__ = "attempt_results"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attempts.id"), primary_key=True
    )
    correct_count: Mapped[int] = mapped_column(Integer)
    incorrect_count: Mapped[int] = mapped_column(Integer)
    unanswered_count: Mapped[int] = mapped_column(Integer)
    part1_score: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    part2_score: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    score: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    graded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("correct_count >= 0", name="attempt_results_correct_check"),
        CheckConstraint("incorrect_count >= 0", name="attempt_results_incorrect_check"),
        CheckConstraint(
            "unanswered_count >= 0", name="attempt_results_unanswered_check"
        ),
        CheckConstraint(
            "part1_score >= 0 AND part1_score <= 6",
            name="attempt_results_part1_score_check",
        ),
        CheckConstraint(
            "part2_score >= 0 AND part2_score <= 4",
            name="attempt_results_part2_score_check",
        ),
        CheckConstraint(
            "score >= 0 AND score <= 10", name="attempt_results_score_check"
        ),
    )


class AttemptQuestionResult(Base):
    __tablename__ = "attempt_question_results"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attempts.id"), primary_key=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id"), primary_key=True
    )
    part_number: Mapped[int] = mapped_column(Integer)
    correct_count: Mapped[int] = mapped_column(Integer)
    total_count: Mapped[int] = mapped_column(Integer)
    earned_score: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    max_score: Mapped[Decimal] = mapped_column(Numeric(4, 2))

    __table_args__ = (
        CheckConstraint("part_number IN (1, 2)", name="attempt_qr_part_check"),
        CheckConstraint("correct_count >= 0", name="attempt_qr_correct_check"),
        CheckConstraint("total_count > 0", name="attempt_qr_total_check"),
        CheckConstraint("earned_score >= 0", name="attempt_qr_earned_score_check"),
        CheckConstraint("max_score > 0", name="attempt_qr_max_score_check"),
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("topics.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExamVersion(Base):
    __tablename__ = "exam_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    exam_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exams.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    difficulty: Mapped[str] = mapped_column(String(50), index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("version_number > 0", name="exam_versions_number_check"),
        CheckConstraint("duration_minutes > 0", name="exam_versions_duration_check"),
        CheckConstraint(
            "status IN ('draft', 'in_review', 'published', 'archived')",
            name="exam_versions_status_check",
        ),
        CheckConstraint(
            "(status != 'published') OR published_at IS NOT NULL",
            name="exam_versions_published_at_check",
        ),
        Index(
            "uq_exam_versions_exam_version", "exam_id", "version_number", unique=True
        ),
        Index(
            "uq_exam_versions_one_published",
            "exam_id",
            unique=True,
            postgresql_where=(status == "published"),
            sqlite_where=(status == "published"),
        ),
        Index("ix_exam_versions_published_at", "status", "published_at"),
    )


class ExamVersionTopic(Base):
    __tablename__ = "exam_version_topics"

    exam_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exam_versions.id"), primary_key=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id"), primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index(
            "uq_exam_version_topics_primary",
            "exam_version_id",
            unique=True,
            postgresql_where=(is_primary.is_(True)),
        ),
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    exam_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exam_versions.id"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    part_number: Mapped[int] = mapped_column(Integer, default=1)
    part_position: Mapped[int] = mapped_column(Integer, default=1)
    question_type: Mapped[str] = mapped_column(String(30), default="multiple_choice")
    body: Mapped[str] = mapped_column(Text)
    source_text: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("position > 0", name="questions_position_check"),
        CheckConstraint("part_number IN (1, 2)", name="questions_part_check"),
        CheckConstraint("part_position > 0", name="questions_part_position_check"),
        CheckConstraint(
            "question_type IN ('multiple_choice', 'true_false_group')",
            name="questions_type_check",
        ),
        Index(
            "uq_questions_version_position",
            "exam_version_id",
            "position",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
            sqlite_where=(deleted_at.is_(None)),
        ),
        Index(
            "uq_questions_version_part_position",
            "exam_version_id",
            "part_number",
            "part_position",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
            sqlite_where=(deleted_at.is_(None)),
        ),
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("position > 0", name="question_options_position_check"),
        Index(
            "uq_question_options_position",
            "question_id",
            "position",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
            sqlite_where=(deleted_at.is_(None)),
        ),
    )


class QuestionStatement(Base):
    __tablename__ = "question_statements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("position > 0", name="question_statements_position_check"),
        Index(
            "uq_question_statements_position",
            "question_id",
            "position",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
            sqlite_where=(deleted_at.is_(None)),
        ),
    )


class AssetLink(Base):
    __tablename__ = "asset_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), index=True)
    exam_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("exam_versions.id"), index=True
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("questions.id"), index=True
    )
    purpose: Mapped[str] = mapped_column(String(30))

    __table_args__ = (
        CheckConstraint(
            "(exam_version_id IS NOT NULL AND question_id IS NULL) OR "
            "(exam_version_id IS NULL AND question_id IS NOT NULL)",
            name="asset_links_owner_check",
        ),
        Index(
            "uq_asset_links_source_exam",
            "asset_id",
            "exam_version_id",
            unique=True,
            postgresql_where=(purpose == "source_document"),
            sqlite_where=(purpose == "source_document"),
        ),
    )


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id"), index=True
    )
    exam_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("exam_versions.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), index=True)
    error_code: Mapped[str | None] = mapped_column(String(50))
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'succeeded', 'failed', 'timed_out')",
            name="import_jobs_status_check",
        ),
        Index("ix_import_jobs_source_idempotency", "source_asset_id", "idempotency_key"),
    )


class ImportFinding(Base):
    __tablename__ = "import_findings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    import_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("import_jobs.id"), index=True
    )
    severity: Mapped[str] = mapped_column(String(20))
    field_path: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    raw_value: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id")
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('warning', 'error')",
            name="import_findings_severity_check",
        ),
    )
