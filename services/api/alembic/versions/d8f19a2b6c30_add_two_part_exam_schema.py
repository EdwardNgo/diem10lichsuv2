"""add two part exam schema

Revision ID: d8f19a2b6c30
Revises: c2a47f0e71b9
Create Date: 2026-08-06 22:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d8f19a2b6c30"
down_revision: str | Sequence[str] | None = "c2a47f0e71b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    is_sqlite = op.get_bind().dialect.name == "sqlite"
    if not is_sqlite:
        op.drop_constraint("attempts_status_check", "attempts", type_="check")
        op.create_check_constraint(
            "attempts_status_check",
            "attempts",
            "status IN ("
            "'in_progress', 'submitted', 'expired_and_submitted', 'abandoned'"
            ")",
        )
    op.add_column(
        "questions",
        sa.Column(
            "part_number",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )
    op.add_column(
        "questions",
        sa.Column(
            "part_position",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )
    op.add_column(
        "questions",
        sa.Column(
            "question_type",
            sa.String(length=30),
            server_default=sa.text("'multiple_choice'"),
            nullable=False,
        ),
    )
    op.add_column("questions", sa.Column("source_text", sa.Text(), nullable=True))
    op.execute("UPDATE questions SET part_position = position")
    if not is_sqlite:
        op.alter_column("questions", "part_number", server_default=None)
        op.alter_column("questions", "part_position", server_default=None)
        op.alter_column("questions", "question_type", server_default=None)
        op.create_check_constraint(
            "questions_part_check",
            "questions",
            "part_number IN (1, 2)",
        )
        op.create_check_constraint(
            "questions_part_position_check",
            "questions",
            "part_position > 0",
        )
        op.create_check_constraint(
            "questions_type_check",
            "questions",
            "question_type IN ('multiple_choice', 'true_false_group')",
        )
    op.create_index(
        "uq_questions_version_part_position",
        "questions",
        ["exam_version_id", "part_number", "part_position"],
        unique=True,
    )

    op.create_table(
        "question_statements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "position > 0",
            name="question_statements_position_check",
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_question_statements_question_id"),
        "question_statements",
        ["question_id"],
    )
    op.create_index(
        "uq_question_statements_position",
        "question_statements",
        ["question_id", "position"],
        unique=True,
    )

    op.create_table(
        "attempt_statement_answers",
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("statement_id", sa.Uuid(), nullable=False),
        sa.Column("selected_value", sa.Boolean(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["statement_id"], ["question_statements.id"]),
        sa.PrimaryKeyConstraint("attempt_id", "statement_id"),
    )
    op.create_index(
        "ix_attempt_statement_answers_attempt_updated_at",
        "attempt_statement_answers",
        ["attempt_id", "updated_at"],
    )

    op.create_table(
        "attempt_results",
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("incorrect_count", sa.Integer(), nullable=False),
        sa.Column("unanswered_count", sa.Integer(), nullable=False),
        sa.Column("part1_score", sa.Numeric(4, 2), nullable=False),
        sa.Column("part2_score", sa.Numeric(4, 2), nullable=False),
        sa.Column("score", sa.Numeric(4, 2), nullable=False),
        sa.Column(
            "graded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "correct_count >= 0",
            name="attempt_results_correct_check",
        ),
        sa.CheckConstraint(
            "incorrect_count >= 0",
            name="attempt_results_incorrect_check",
        ),
        sa.CheckConstraint(
            "unanswered_count >= 0",
            name="attempt_results_unanswered_check",
        ),
        sa.CheckConstraint(
            "part1_score >= 0 AND part1_score <= 6",
            name="attempt_results_part1_score_check",
        ),
        sa.CheckConstraint(
            "part2_score >= 0 AND part2_score <= 4",
            name="attempt_results_part2_score_check",
        ),
        sa.CheckConstraint(
            "score >= 0 AND score <= 10",
            name="attempt_results_score_check",
        ),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"]),
        sa.PrimaryKeyConstraint("attempt_id"),
    )

    op.create_table(
        "attempt_question_results",
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("part_number", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("earned_score", sa.Numeric(4, 2), nullable=False),
        sa.Column("max_score", sa.Numeric(4, 2), nullable=False),
        sa.CheckConstraint("part_number IN (1, 2)", name="attempt_qr_part_check"),
        sa.CheckConstraint("correct_count >= 0", name="attempt_qr_correct_check"),
        sa.CheckConstraint("total_count > 0", name="attempt_qr_total_check"),
        sa.CheckConstraint(
            "earned_score >= 0",
            name="attempt_qr_earned_score_check",
        ),
        sa.CheckConstraint("max_score > 0", name="attempt_qr_max_score_check"),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("attempt_id", "question_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    is_sqlite = op.get_bind().dialect.name == "sqlite"
    if not is_sqlite:
        op.drop_constraint("attempts_status_check", "attempts", type_="check")
        op.create_check_constraint(
            "attempts_status_check",
            "attempts",
            "status IN ('in_progress', 'submitted', 'expired_and_submitted')",
        )
    op.drop_table("attempt_question_results")
    op.drop_table("attempt_results")
    op.drop_index(
        "ix_attempt_statement_answers_attempt_updated_at",
        table_name="attempt_statement_answers",
    )
    op.drop_table("attempt_statement_answers")
    op.drop_index(
        "uq_question_statements_position",
        table_name="question_statements",
    )
    op.drop_index(
        op.f("ix_question_statements_question_id"),
        table_name="question_statements",
    )
    op.drop_table("question_statements")
    op.drop_index("uq_questions_version_part_position", table_name="questions")
    if not is_sqlite:
        op.drop_constraint("questions_type_check", "questions", type_="check")
        op.drop_constraint("questions_part_position_check", "questions", type_="check")
        op.drop_constraint("questions_part_check", "questions", type_="check")
    op.drop_column("questions", "source_text")
    op.drop_column("questions", "question_type")
    op.drop_column("questions", "part_position")
    op.drop_column("questions", "part_number")
