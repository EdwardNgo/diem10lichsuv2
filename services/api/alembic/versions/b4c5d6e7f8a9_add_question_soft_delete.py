"""add soft delete columns for draft question editing

Revision ID: b4c5d6e7f8a9
Revises: a3b8c1d4e5f6
Create Date: 2026-08-10 23:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b4c5d6e7f8a9"
down_revision: str | Sequence[str] | None = "a3b8c1d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "questions",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "question_options",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "question_statements",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.drop_index("uq_questions_version_position", table_name="questions")
    op.drop_index("uq_questions_version_part_position", table_name="questions")
    op.create_index(
        "uq_questions_version_position",
        "questions",
        ["exam_version_id", "position"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_questions_version_part_position",
        "questions",
        ["exam_version_id", "part_number", "part_position"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.drop_index("uq_question_options_position", table_name="question_options")
    op.create_index(
        "uq_question_options_position",
        "question_options",
        ["question_id", "position"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.drop_index("uq_question_statements_position", table_name="question_statements")
    op.create_index(
        "uq_question_statements_position",
        "question_statements",
        ["question_id", "position"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
        sqlite_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_question_statements_position", table_name="question_statements")
    op.create_index(
        "uq_question_statements_position",
        "question_statements",
        ["question_id", "position"],
        unique=True,
    )

    op.drop_index("uq_question_options_position", table_name="question_options")
    op.create_index(
        "uq_question_options_position",
        "question_options",
        ["question_id", "position"],
        unique=True,
    )

    op.drop_index("uq_questions_version_part_position", table_name="questions")
    op.drop_index("uq_questions_version_position", table_name="questions")
    op.create_index(
        "uq_questions_version_position",
        "questions",
        ["exam_version_id", "position"],
        unique=True,
    )
    op.create_index(
        "uq_questions_version_part_position",
        "questions",
        ["exam_version_id", "part_number", "part_position"],
        unique=True,
    )

    op.drop_column("question_statements", "deleted_at")
    op.drop_column("question_options", "deleted_at")
    op.drop_column("questions", "deleted_at")
