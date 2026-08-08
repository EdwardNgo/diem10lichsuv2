"""add attempt answers table

Revision ID: c2a47f0e71b9
Revises: b63e8c5d4f1a
Create Date: 2026-08-06 08:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c2a47f0e71b9"
down_revision: str | Sequence[str] | None = "b63e8c5d4f1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "attempt_answers",
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("selected_option_id", sa.Uuid(), nullable=True),
        sa.Column("is_marked_for_review", sa.Boolean(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["selected_option_id"], ["question_options.id"]),
        sa.PrimaryKeyConstraint("attempt_id", "question_id"),
    )
    op.create_index(
        "ix_attempt_answers_attempt_updated_at",
        "attempt_answers",
        ["attempt_id", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_attempt_answers_attempt_updated_at", table_name="attempt_answers")
    op.drop_table("attempt_answers")
