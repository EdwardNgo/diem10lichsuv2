"""add attempt pause time

Revision ID: e91a6c2f4d73
Revises: d8f19a2b6c30
Create Date: 2026-08-08 15:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e91a6c2f4d73"
down_revision: str | Sequence[str] | None = "d8f19a2b6c30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "attempts",
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("attempts", "paused_at")
