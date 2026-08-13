"""add user last login

Revision ID: c9d8e7f6a5b4
Revises: b4c5d6e7f8a9
Create Date: 2026-08-13 22:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c9d8e7f6a5b4"
down_revision: str | Sequence[str] | None = "b4c5d6e7f8a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "last_login_at")
