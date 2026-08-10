"""add assets table

Revision ID: f4a7c9d2e8b1
Revises: e91a6c2f4d73
Create Date: 2026-08-09 22:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f4a7c9d2e8b1"
down_revision: str | Sequence[str] | None = "e91a6c2f4d73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("bucket", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("asset_kind", sa.String(length=30), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "asset_kind IN ('source_document', 'question_image')",
            name="assets_kind_check",
        ),
        sa.CheckConstraint("size_bytes > 0", name="assets_size_bytes_check"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assets_asset_kind"), "assets", ["asset_kind"], unique=False
    )
    op.create_index(
        op.f("ix_assets_checksum_sha256"),
        "assets",
        ["checksum_sha256"],
        unique=False,
    )
    op.create_index(op.f("ix_assets_object_key"), "assets", ["object_key"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_assets_object_key"), table_name="assets")
    op.drop_index(op.f("ix_assets_checksum_sha256"), table_name="assets")
    op.drop_index(op.f("ix_assets_asset_kind"), table_name="assets")
    op.drop_table("assets")
