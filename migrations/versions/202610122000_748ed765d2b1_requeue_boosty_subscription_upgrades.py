"""Requeue ignored Boosty subscription upgrades.

Revision ID: 748ed765d2b1
Revises: c34d6b98a125
Create Date: 2026-10-12 20:00:00

``boosty_operations`` lives in the hub bind, so this migration updates it
through the same engine used by the Boosty models.  The description is always
stored even when raw-payload storage is disabled, which makes it a portable
way to identify operations created before ``up_subscription`` was supported.
"""

import sqlalchemy as sa
from flask import current_app

from flaskbb.extensions import db_hub


revision = "748ed765d2b1"
down_revision = "c34d6b98a125"
branch_labels = None
depends_on = None


def _engine():
    return db_hub.get_engine(current_app, bind="hub")


def upgrade():
    statement = sa.text("""
        UPDATE boosty_operations
        SET operation_type = :operation_type,
            status = :new_status,
            processed_at = NULL,
            processing_started_at = NULL,
            processing_attempts = 0,
            last_error = NULL,
            ignored_reason = NULL
        WHERE status = :ignored_status
          AND description = :description
          AND points_transaction_id IS NULL
    """)
    with _engine().begin() as connection:
        connection.execute(statement, {
            "operation_type": "SubscriptionUpgrade",
            "new_status": "New",
            "ignored_status": "Ignored",
            "description": "Boosty event (up_subscription)",
        })


def downgrade():
    # Reverting already queued or credited payments would risk taking away
    # Opyx or making an operation eligible for a duplicate credit.
    pass
