"""Add configurable server update script path.

Revision ID: c34d6b98a125
Revises: b57a91c24e31
Create Date: 2026-09-25 01:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "c34d6b98a125"
down_revision = "b57a91c24e31"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "servers",
        sa.Column("update_script_path", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("servers", "update_script_path")
