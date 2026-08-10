"""add import jobs, findings and asset links

Revision ID: a3b8c1d4e5f6
Revises: f4a7c9d2e8b1
Create Date: 2026-08-10 22:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a3b8c1d4e5f6"
down_revision: str | Sequence[str] | None = "f4a7c9d2e8b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_asset_id", sa.Uuid(), nullable=False),
        sa.Column("exam_version_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('running', 'succeeded', 'failed', 'timed_out')",
            name="import_jobs_status_check",
        ),
        sa.ForeignKeyConstraint(["exam_version_id"], ["exam_versions.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_import_jobs_exam_version_id"),
        "import_jobs",
        ["exam_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_import_jobs_source_asset_id"),
        "import_jobs",
        ["source_asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_import_jobs_source_idempotency",
        "import_jobs",
        ["source_asset_id", "idempotency_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_import_jobs_status"), "import_jobs", ["status"], unique=False
    )

    op.create_table(
        "import_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_job_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("field_path", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "severity IN ('warning', 'error')",
            name="import_findings_severity_check",
        ),
        sa.ForeignKeyConstraint(["import_job_id"], ["import_jobs.id"]),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_import_findings_import_job_id"),
        "import_findings",
        ["import_job_id"],
        unique=False,
    )

    op.create_table(
        "asset_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("exam_version_id", sa.Uuid(), nullable=True),
        sa.Column("question_id", sa.Uuid(), nullable=True),
        sa.Column("purpose", sa.String(length=30), nullable=False),
        sa.CheckConstraint(
            "(exam_version_id IS NOT NULL AND question_id IS NULL) OR "
            "(exam_version_id IS NULL AND question_id IS NOT NULL)",
            name="asset_links_owner_check",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["exam_version_id"], ["exam_versions.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_asset_links_asset_id"), "asset_links", ["asset_id"], unique=False
    )
    op.create_index(
        op.f("ix_asset_links_exam_version_id"),
        "asset_links",
        ["exam_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_asset_links_question_id"),
        "asset_links",
        ["question_id"],
        unique=False,
    )
    op.create_index(
        "uq_asset_links_source_exam",
        "asset_links",
        ["asset_id", "exam_version_id"],
        unique=True,
        sqlite_where=sa.text("purpose = 'source_document'"),
        postgresql_where=sa.text("purpose = 'source_document'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_asset_links_source_exam", table_name="asset_links")
    op.drop_index(op.f("ix_asset_links_question_id"), table_name="asset_links")
    op.drop_index(op.f("ix_asset_links_exam_version_id"), table_name="asset_links")
    op.drop_index(op.f("ix_asset_links_asset_id"), table_name="asset_links")
    op.drop_table("asset_links")
    op.drop_index(op.f("ix_import_findings_import_job_id"), table_name="import_findings")
    op.drop_table("import_findings")
    op.drop_index("ix_import_jobs_source_idempotency", table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_status"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_source_asset_id"), table_name="import_jobs")
    op.drop_index(op.f("ix_import_jobs_exam_version_id"), table_name="import_jobs")
    op.drop_table("import_jobs")
