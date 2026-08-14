"""Add bind-aware Boosty integration tables.

Revision ID: b57a91c24e31
Revises: 6424764cf08a
Create Date: 2026-08-14 21:00:00

The project keeps Opyx in the ``hub`` SQLAlchemy bind while Alembic's version
table lives in the forum database. The migration therefore creates the tables
through the existing ``db_hub`` engine; this is the same bind used by the
runtime models and is required for an atomic Boosty operation/Opyx grant.
"""

from flask import current_app

from flaskbb.extensions import db_hub
from hub.features.donations.boosty import models  # noqa: F401


revision = "b57a91c24e31"
down_revision = "6424764cf08a"
branch_labels = None
depends_on = None


TABLES = (
    "boosty_accounts",
    "boosty_account_links",
    "boosty_link_tokens",
    "boosty_operations",
    "boosty_processing_events",
    "boosty_discord_role_mappings",
    "boosty_subscription_events",
    "boosty_discord_actions",
    "boosty_webhook_endpoints",
    "boosty_webhook_deliveries",
    "boosty_sync_state",
    "boosty_reconciliation_issues",
    "boosty_corrections",
)


def _engine():
    return db_hub.get_engine(current_app, bind="hub")


def upgrade():
    engine = _engine()
    with engine.begin() as connection:
        for table_name in TABLES:
            db_hub.metadata.tables[table_name].create(bind=connection, checkfirst=True)


def downgrade():
    engine = _engine()
    with engine.begin() as connection:
        for table_name in reversed(TABLES):
            db_hub.metadata.tables[table_name].drop(bind=connection, checkfirst=True)
