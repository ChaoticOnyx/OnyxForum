from sqlalchemy import Column, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.orm import relationship

from flaskbb.extensions import db_hub
from flaskbb.utils.database import UTCDateTime
from flaskbb.utils.helpers import time_utcnow


class BoostyAccount(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_accounts"

    id = Column(db_hub.Integer, primary_key=True)
    external_id = Column(db_hub.String(64), nullable=False, unique=True)
    name = Column(db_hub.String(255), nullable=True)
    email = Column(db_hub.String(255), nullable=True)
    dialog_id = Column(db_hub.String(64), nullable=True)
    tier_id = Column(db_hub.String(64), nullable=True)
    tier_name = Column(db_hub.String(255), nullable=True)
    subscription_status = Column(db_hub.String(32), nullable=True)
    is_paid_subscriber = Column(db_hub.Boolean, nullable=False, default=False, server_default=text("0"))
    first_seen_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)
    last_seen_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)

    link = relationship("BoostyAccountLink", uselist=False, back_populates="account")


class BoostyAccountLink(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_account_links"

    id = Column(db_hub.Integer, primary_key=True)
    account_id = Column(db_hub.Integer, ForeignKey("boosty_accounts.id", ondelete="CASCADE"), nullable=False, unique=True)
    forum_user_id = Column(db_hub.Integer, nullable=False, index=True)
    player_id = Column(db_hub.Integer, ForeignKey("players.id", ondelete="RESTRICT"), nullable=False, index=True)
    linked_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)
    linked_by_user_id = Column(db_hub.Integer, nullable=True)
    updated_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow, onupdate=time_utcnow)

    account = relationship("BoostyAccount", back_populates="link")
    player = relationship("Player", lazy="joined")


class BoostyLinkToken(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_link_tokens"

    id = Column(db_hub.Integer, primary_key=True)
    account_id = Column(db_hub.Integer, ForeignKey("boosty_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(db_hub.String(64), nullable=False, unique=True)
    token_hint = Column(db_hub.String(12), nullable=False)
    created_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)
    expires_at = Column(UTCDateTime(timezone=True), nullable=False, index=True)
    used_at = Column(UTCDateTime(timezone=True), nullable=True)
    used_by_forum_user_id = Column(db_hub.Integer, nullable=True)
    message_sent_at = Column(UTCDateTime(timezone=True), nullable=True)
    send_error = Column(db_hub.Text, nullable=True)

    account = relationship("BoostyAccount", lazy="joined")


class BoostyOperation(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_operations"

    id = Column(db_hub.Integer, primary_key=True)
    external_id = Column(db_hub.String(128), nullable=False, unique=True)
    account_id = Column(db_hub.Integer, ForeignKey("boosty_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    operation_type = Column(db_hub.String(64), nullable=False, index=True)
    currency = Column(db_hub.String(3), nullable=False, default="RUB", server_default="RUB")
    amount = Column(db_hub.Numeric(18, 2), nullable=False)
    description = Column(db_hub.Text, nullable=True)
    status = Column(db_hub.String(32), nullable=False, index=True)
    forum_user_id = Column(db_hub.Integer, nullable=True, index=True)
    player_id = Column(db_hub.Integer, ForeignKey("players.id", ondelete="RESTRICT"), nullable=True, index=True)
    base_rate = Column(db_hub.Numeric(18, 6), nullable=True)
    bonus_percent = Column(db_hub.Numeric(9, 4), nullable=True)
    final_rate = Column(db_hub.Numeric(18, 6), nullable=True)
    opyx_amount = Column(db_hub.Numeric(18, 2), nullable=True)
    points_transaction_id = Column(db_hub.Integer, ForeignKey("points_transactions.id", ondelete="RESTRICT"), nullable=True, unique=True)
    source_created_at = Column(UTCDateTime(timezone=True), nullable=False, index=True)
    received_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow, index=True)
    processing_started_at = Column(UTCDateTime(timezone=True), nullable=True)
    processed_at = Column(UTCDateTime(timezone=True), nullable=True)
    processing_attempts = Column(db_hub.Integer, nullable=False, default=0, server_default=text("0"))
    last_error = Column(db_hub.Text, nullable=True)
    ignored_reason = Column(db_hub.Text, nullable=True)
    raw_payload = Column(db_hub.JSON, nullable=True)

    account = relationship("BoostyAccount", lazy="joined")
    player = relationship("Player", foreign_keys=[player_id], lazy="joined")
    points_transaction = relationship("PointsTransaction", foreign_keys=[points_transaction_id])
    history = relationship("BoostyProcessingEvent", back_populates="operation", order_by="BoostyProcessingEvent.created_at")

    __table_args__ = (
        Index("ix_boosty_operations_status_received", "status", "received_at"),
    )


class BoostyProcessingEvent(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_processing_events"

    id = Column(db_hub.Integer, primary_key=True)
    operation_id = Column(db_hub.Integer, ForeignKey("boosty_operations.id", ondelete="CASCADE"), nullable=False, index=True)
    event = Column(db_hub.String(64), nullable=False, index=True)
    message = Column(db_hub.Text, nullable=True)
    details = Column(db_hub.JSON, nullable=True)
    created_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow, index=True)

    operation = relationship("BoostyOperation", back_populates="history")


class BoostyDiscordRoleMapping(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_discord_role_mappings"

    id = Column(db_hub.Integer, primary_key=True)
    guild_id = Column(db_hub.String(64), nullable=False)
    tier_id = Column(db_hub.String(64), nullable=False)
    tier_name = Column(db_hub.String(255), nullable=True)
    role_id = Column(db_hub.String(64), nullable=False)
    enabled = Column(db_hub.Boolean, nullable=False, default=True, server_default=text("1"))
    created_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)
    updated_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow, onupdate=time_utcnow)

    __table_args__ = (
        UniqueConstraint("guild_id", "tier_id", name="uq_boosty_discord_mapping_guild_tier"),
    )


class BoostySubscriptionEvent(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_subscription_events"

    id = Column(db_hub.Integer, primary_key=True)
    account_id = Column(db_hub.Integer, ForeignKey("boosty_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    event_name = Column(db_hub.String(32), nullable=False, index=True)
    previous_tier_id = Column(db_hub.String(64), nullable=True)
    tier_id = Column(db_hub.String(64), nullable=True)
    tier_name = Column(db_hub.String(255), nullable=True)
    subscription_status = Column(db_hub.String(32), nullable=True)
    observed_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow, index=True)

    account = relationship("BoostyAccount", lazy="joined")

    __table_args__ = (
        Index("ix_boosty_subscription_events_observed_event", "observed_at", "event_name"),
    )


class BoostyDiscordAction(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_discord_actions"

    id = Column(db_hub.Integer, primary_key=True)
    operation_id = Column(db_hub.Integer, ForeignKey("boosty_operations.id", ondelete="SET NULL"), nullable=True, index=True)
    account_id = Column(db_hub.Integer, ForeignKey("boosty_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    guild_id = Column(db_hub.String(64), nullable=False)
    discord_user_id = Column(db_hub.String(64), nullable=True)
    role_id = Column(db_hub.String(64), nullable=True)
    action = Column(db_hub.String(32), nullable=False)
    status = Column(db_hub.String(32), nullable=False, index=True)
    attempts = Column(db_hub.Integer, nullable=False, default=0, server_default=text("0"))
    created_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)
    processed_at = Column(UTCDateTime(timezone=True), nullable=True)
    last_error = Column(db_hub.Text, nullable=True)

    operation = relationship("BoostyOperation", lazy="joined")
    account = relationship("BoostyAccount", lazy="joined")


class BoostyWebhookEndpoint(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_webhook_endpoints"

    id = Column(db_hub.Integer, primary_key=True)
    name = Column(db_hub.String(255), nullable=False)
    url = Column(db_hub.String(2048), nullable=False)
    enabled = Column(db_hub.Boolean, nullable=False, default=True, server_default=text("1"))
    secret = Column(db_hub.Text, nullable=False)
    events = Column(db_hub.JSON, nullable=False)
    timeout_seconds = Column(db_hub.Integer, nullable=False, default=10, server_default=text("10"))
    retry_count = Column(db_hub.Integer, nullable=False, default=5, server_default=text("5"))
    last_delivery_status = Column(db_hub.String(32), nullable=True)
    last_error = Column(db_hub.Text, nullable=True)
    created_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)
    updated_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow, onupdate=time_utcnow)
    deleted_at = Column(UTCDateTime(timezone=True), nullable=True, index=True)


class BoostyWebhookDelivery(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_webhook_deliveries"

    id = Column(db_hub.Integer, primary_key=True)
    event_id = Column(db_hub.String(64), nullable=False)
    event_name = Column(db_hub.String(128), nullable=False, index=True)
    endpoint_id = Column(
        db_hub.Integer,
        ForeignKey(
            "boosty_webhook_endpoints.id",
            name="fk_boosty_hook_delivery_endpoint",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    operation_id = Column(db_hub.Integer, ForeignKey("boosty_operations.id", ondelete="SET NULL"), nullable=True, index=True)
    payload = Column(db_hub.JSON, nullable=False)
    status = Column(db_hub.String(32), nullable=False, index=True)
    attempts = Column(db_hub.Integer, nullable=False, default=0, server_default=text("0"))
    created_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow, index=True)
    last_attempt_at = Column(UTCDateTime(timezone=True), nullable=True)
    next_attempt_at = Column(UTCDateTime(timezone=True), nullable=True, index=True)
    http_status = Column(db_hub.Integer, nullable=True)
    last_error = Column(db_hub.Text, nullable=True)

    endpoint = relationship("BoostyWebhookEndpoint", lazy="joined")
    operation = relationship("BoostyOperation", lazy="joined")

    __table_args__ = (
        UniqueConstraint("event_id", "endpoint_id", name="uq_boosty_webhook_delivery_event_endpoint"),
    )


class BoostySyncState(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_sync_state"

    id = Column(db_hub.Integer, primary_key=True, default=1)
    last_operation_external_id = Column(db_hub.String(128), nullable=True)
    last_operation_created_at = Column(UTCDateTime(timezone=True), nullable=True)
    last_sync_started_at = Column(UTCDateTime(timezone=True), nullable=True)
    last_successful_sync_at = Column(UTCDateTime(timezone=True), nullable=True)
    next_sync_at = Column(UTCDateTime(timezone=True), nullable=True)
    last_subscription_sync_at = Column(UTCDateTime(timezone=True), nullable=True)
    last_error_at = Column(UTCDateTime(timezone=True), nullable=True)
    last_error = Column(db_hub.Text, nullable=True)
    consecutive_failures = Column(db_hub.Integer, nullable=False, default=0, server_default=text("0"))


class BoostyReconciliationIssue(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_reconciliation_issues"

    id = Column(db_hub.Integer, primary_key=True)
    fingerprint = Column(db_hub.String(128), nullable=False, unique=True)
    issue_type = Column(db_hub.String(64), nullable=False, index=True)
    severity = Column(db_hub.String(16), nullable=False, index=True)
    operation_id = Column(db_hub.Integer, ForeignKey("boosty_operations.id", ondelete="SET NULL"), nullable=True, index=True)
    message = Column(db_hub.Text, nullable=False)
    details = Column(db_hub.JSON, nullable=True)
    status = Column(db_hub.String(16), nullable=False, default="Open", server_default="Open", index=True)
    detected_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)
    last_seen_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)
    resolved_at = Column(UTCDateTime(timezone=True), nullable=True)

    operation = relationship("BoostyOperation", lazy="joined")


class BoostyCorrection(db_hub.Model):
    __bind_key__ = "hub"
    __tablename__ = "boosty_corrections"

    id = Column(db_hub.Integer, primary_key=True)
    operation_id = Column(db_hub.Integer, ForeignKey("boosty_operations.id", ondelete="SET NULL"), nullable=True, index=True)
    points_transaction_id = Column(db_hub.Integer, ForeignKey("points_transactions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    amount = Column(db_hub.Numeric(18, 2), nullable=False)
    author_user_id = Column(db_hub.Integer, nullable=False)
    reason = Column(db_hub.Text, nullable=False)
    created_at = Column(UTCDateTime(timezone=True), nullable=False, default=time_utcnow)

    operation = relationship("BoostyOperation", lazy="joined")
    points_transaction = relationship("PointsTransaction", lazy="joined")
