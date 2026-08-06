"""add attempts table

Revision ID: b63e8c5d4f1a
Revises: 7f0b31c9ab2d
Create Date: 2026-08-05 23:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b63e8c5d4f1a"
down_revision: str | Sequence[str] | None = "7f0b31c9ab2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("exam_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.CheckConstraint("attempt_number > 0", name="attempts_number_check"),
        sa.CheckConstraint("expires_at > started_at", name="attempts_expires_at_check"),
        sa.CheckConstraint(
            "status IN ('in_progress', 'submitted', 'expired_and_submitted')",
            name="attempts_status_check",
        ),
        sa.ForeignKeyConstraint(["exam_version_id"], ["exam_versions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_attempts_exam_version_id"),
        "attempts",
        ["exam_version_id"],
        unique=False,
    )
    op.create_index(op.f("ix_attempts_expires_at"), "attempts", ["expires_at"])
    op.create_index(op.f("ix_attempts_status"), "attempts", ["status"])
    op.create_index(op.f("ix_attempts_user_id"), "attempts", ["user_id"])
    op.create_index(
        "ix_attempts_user_started_at",
        "attempts",
        ["user_id", "started_at"],
        unique=False,
    )
    op.create_index(
        "uq_attempts_open_user_exam_version",
        "attempts",
        ["user_id", "exam_version_id"],
        unique=True,
        postgresql_where=sa.text("status = 'in_progress'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "uq_attempts_open_user_exam_version",
        table_name="attempts",
        postgresql_where=sa.text("status = 'in_progress'"),
    )
    op.drop_index("ix_attempts_user_started_at", table_name="attempts")
    op.drop_index(op.f("ix_attempts_user_id"), table_name="attempts")
    op.drop_index(op.f("ix_attempts_status"), table_name="attempts")
    op.drop_index(op.f("ix_attempts_expires_at"), table_name="attempts")
    op.drop_index(op.f("ix_attempts_exam_version_id"), table_name="attempts")
    op.drop_table("attempts")
