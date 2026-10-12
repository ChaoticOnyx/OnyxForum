import datetime
import hashlib
import json
import logging
import secrets
from decimal import Decimal

from flask import current_app
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from flaskbb.extensions import db, db_hub
from flaskbb.utils.helpers import time_utcnow

from hub.models import DiscordUser, HubLog, Player

from ..actions import (
    add_points_transaction_and_notify,
    dispatch_points_transaction_notifications,
)

from .api import BoostyApiClient, event_external_id
from .constants import (
    EVENT_OPERATION_TYPES,
    OPERATION_ERROR,
    OPERATION_GIFT_PURCHASE,
    OPERATION_IGNORED,
    OPERATION_NEW,
    OPERATION_PENDING_LINK,
    OPERATION_PAYOUT,
    OPERATION_PAYOUT_ERROR,
    OPERATION_PROCESSED,
    OPERATION_PROCESSING,
    OPERATION_SUBSCRIPTION_ENDED,
    OPERATION_SUBSCRIPTION_UPGRADE,
    OPERATION_UNKNOWN,
    POINTS_EVENT_TYPES,
    ZERO,
)
from .models import (
    BoostyAccount,
    BoostyAccountLink,
    BoostyCorrection,
    BoostyLinkToken,
    BoostyOperation,
    BoostyProcessingEvent,
    BoostySubscriptionEvent,
)
from .formatting import format_moscow_datetime
from .opyx import calculate_opyx
from .settings import get_settings
from .webhooks import queue_event


logger = logging.getLogger("donations.boosty")


def _dispatch_committed_points_notifications(points_transaction_id, registered_by=None):
    try:
        from hub.models import PointsTransaction

        points_transaction = PointsTransaction.query.get(points_transaction_id)
        if points_transaction is None:
            raise RuntimeError("Points transaction {} was not found after commit".format(points_transaction_id))
        dispatch_points_transaction_notifications(points_transaction, registered_by)
    except Exception:
        # The Points change is already committed. A Discord/notification error
        # must not roll it back or cause a repeated Boosty credit on retry.
        db_hub.session.rollback()
        logger.exception(
            "Failed to dispatch standard Points notifications for transaction %s",
            points_transaction_id,
        )


def public_link_url():
    return str(current_app.config.get(
        "BOOSTY_PUBLIC_LINK_URL",
        "https://community.ss13.ru/donations/boosty/link",
    )).strip()


def format_message(template, **values):
    class SafeValues(dict):
        def __missing__(self, key):
            return "{" + key + "}"
    values.setdefault("linkUrl", public_link_url())
    return str(template or "").format_map(SafeValues(values))


def operation_data(operation):
    return {
        "id": operation.id,
        "externalId": operation.external_id,
        "type": operation.operation_type,
        "amount": str(operation.amount),
        "currency": operation.currency,
        "status": operation.status,
        "boostyAccountId": operation.account.external_id if operation.account else None,
        "boostyName": operation.account.name if operation.account else None,
        "forumUserId": operation.forum_user_id,
        "opyx": str(operation.opyx_amount) if operation.opyx_amount is not None else None,
        "receivedAt": operation.received_at.isoformat() if operation.received_at else None,
        "processedAt": operation.processed_at.isoformat() if operation.processed_at else None,
    }


def record_history(operation, event, message=None, details=None):
    history = BoostyProcessingEvent(
        operation=operation,
        event=event,
        message=message,
        details=details,
    )
    db_hub.session.add(history)
    return history


def audit_admin_action(user, message):
    user_id = getattr(user, "id", None)
    try:
        db.session.add(HubLog(server_id="boosty", user_id=user_id, message=message))
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        logger.exception("Failed to write Boosty administrative audit entry")
        return False


def _source_datetime(payload):
    value = int(payload.get("createdAt") or 0)
    if not value:
        return time_utcnow()
    return datetime.datetime.fromtimestamp(value, datetime.timezone.utc)


def _json_safe(value):
    """Return a JSON-column-safe copy while preserving exact decimal text."""
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _upsert_account(payload):
    user = payload.get("user") or {}
    external_id = str(user.get("id") or "")
    if not external_id:
        raise ValueError("Boosty operation does not contain user.id")
    account = BoostyAccount.query.filter_by(external_id=external_id).first()
    if account is None:
        account = BoostyAccount(external_id=external_id)
        db_hub.session.add(account)
    account.name = user.get("name") or account.name
    account.email = user.get("email") or account.email
    account.last_seen_at = time_utcnow()
    return account


def ingest_donation(payload):
    boosty_id = payload.get("id")
    if boosty_id in (None, ""):
        raise ValueError("Boosty donation does not contain a stable id")
    external_id = "donation:{}".format(boosty_id)
    existing = BoostyOperation.query.filter_by(external_id=external_id).first()
    if existing:
        return existing, False

    try:
        with db_hub.session.begin_nested():
            account = _upsert_account(payload)
            operation = BoostyOperation(
                external_id=external_id,
                account=account,
                operation_type="Donation",
                currency=str(current_app.config.get("BOOSTY_ACCOUNT_CURRENCY", "RUB")),
                amount=Decimal(str(payload.get("amount") or "0")),
                description="Boosty donation ({})".format(payload.get("type") or "author"),
                status=OPERATION_NEW,
                source_created_at=_source_datetime(payload),
                raw_payload=_json_safe(payload) if current_app.config.get("BOOSTY_STORE_RAW_PAYLOAD", True) else None,
            )
            db_hub.session.add(operation)
            db_hub.session.flush()
            record_history(operation, "Received")
            queue_event("boosty.operation.received", operation_data(operation), operation.id)
            db_hub.session.flush()
        return operation, True
    except IntegrityError:
        existing = BoostyOperation.query.filter_by(external_id=external_id).first()
        if existing:
            return existing, False
        raise


def find_operation_for_event(payload):
    external_id = event_external_id(payload)
    existing = BoostyOperation.query.filter_by(external_id=external_id).first()
    if existing or str(payload.get("eventType") or "") != "donation_author":
        return existing

    user = payload.get("user") or {}
    user_id = str(user.get("id") or "")
    if not user_id:
        return None
    return (
        BoostyOperation.query
        .join(BoostyAccount)
        .filter(BoostyOperation.external_id.like("donation:%"))
        .filter(BoostyAccount.external_id == user_id)
        .filter(BoostyOperation.amount == Decimal(str(payload.get("amount") or "0")))
        .filter(BoostyOperation.source_created_at == _source_datetime(payload))
        .first()
    )


def _ignored_event_reason(operation_type, event_type):
    if operation_type == OPERATION_GIFT_PURCHASE:
        return "Gift purchase does not credit the buyer; Points are credited on gift activation"
    if operation_type == OPERATION_SUBSCRIPTION_ENDED:
        return "Subscription end is not a payment or a balance reversal"
    if operation_type in (OPERATION_PAYOUT, OPERATION_PAYOUT_ERROR):
        return "Blogger payout event is not a user payment"
    return "Unsupported Boosty event type: {}".format(event_type or "unknown")


def _apply_subscription_event(account, payload, event_type):
    if event_type not in (
        "subscribe",
        "recurrent",
        "up_subscription",
        "unsubscribe",
    ):
        return
    now = time_utcnow()
    previous_tier_id = (
        str(payload.get("oldLevelId"))
        if payload.get("oldLevelId") is not None
        else account.tier_id
    )
    tier_id = str(payload.get("levelId")) if payload.get("levelId") is not None else None
    if event_type in ("subscribe", "recurrent", "up_subscription"):
        account.is_paid_subscriber = True
        account.subscription_status = "active"
        account.tier_id = tier_id or account.tier_id
        if event_type == "subscribe":
            event_name = "Started"
        elif event_type == "up_subscription":
            event_name = "Changed"
        else:
            event_name = "Renewed"
    else:
        account.is_paid_subscriber = False
        account.subscription_status = "inactive"
        account.tier_id = tier_id or account.tier_id
        event_name = "Ended"
    account.last_seen_at = now
    db_hub.session.add(BoostySubscriptionEvent(
        account=account,
        event_name=event_name,
        previous_tier_id=previous_tier_id,
        tier_id=account.tier_id,
        tier_name=account.tier_name,
        subscription_status=account.subscription_status,
        observed_at=_source_datetime(payload),
    ))
    if event_type == "subscribe":
        queue_event("boosty.subscription.started", {
            "boostyAccountId": account.external_id,
            "tierId": account.tier_id,
            "status": account.subscription_status,
        })
    elif event_type == "up_subscription":
        queue_event("boosty.subscription.changed", {
            "boostyAccountId": account.external_id,
            "previousTierId": previous_tier_id,
            "tierId": account.tier_id,
            "status": account.subscription_status,
        })
    elif event_type == "unsubscribe":
        queue_event("boosty.subscription.ended", {
            "boostyAccountId": account.external_id,
            "tierId": account.tier_id,
            "status": account.subscription_status,
        })


def ingest_event(payload):
    event_type = str(payload.get("eventType") or "")
    operation_type = EVENT_OPERATION_TYPES.get(event_type, OPERATION_UNKNOWN)
    existing = find_operation_for_event(payload)
    if existing:
        return existing, False

    external_id = event_external_id(payload)
    credits_points = event_type in POINTS_EVENT_TYPES
    try:
        with db_hub.session.begin_nested():
            account = _upsert_account(payload)
            operation = BoostyOperation(
                external_id=external_id,
                account=account,
                operation_type=operation_type,
                currency=str(current_app.config.get("BOOSTY_ACCOUNT_CURRENCY", "RUB")),
                amount=Decimal(str(payload.get("amount") or "0")),
                description="Boosty event ({})".format(event_type or "unknown"),
                status=OPERATION_NEW if credits_points else OPERATION_IGNORED,
                source_created_at=_source_datetime(payload),
                processed_at=None if credits_points else time_utcnow(),
                raw_payload=_json_safe(payload) if current_app.config.get("BOOSTY_STORE_RAW_PAYLOAD", True) else None,
            )
            if not credits_points:
                operation.ignored_reason = _ignored_event_reason(operation_type, event_type)
            db_hub.session.add(operation)
            db_hub.session.flush()
            record_history(operation, "Received")
            queue_event("boosty.operation.received", operation_data(operation), operation.id)
            _apply_subscription_event(account, payload, event_type)
            if not credits_points:
                record_history(operation, "Ignored", operation.ignored_reason)
                queue_event("boosty.operation.ignored", operation_data(operation), operation.id)
            db_hub.session.flush()
        return operation, True
    except IntegrityError:
        existing = find_operation_for_event(payload)
        if existing:
            return existing, False
        raise


def requeue_ignored_subscription_upgrades():
    """Requeue upgrades that were ignored before support was added."""
    return (
        BoostyOperation.query
        .filter(
            BoostyOperation.status == OPERATION_IGNORED,
            BoostyOperation.description == "Boosty event (up_subscription)",
            BoostyOperation.ignored_reason
            == "Unsupported Boosty event type: up_subscription",
            BoostyOperation.points_transaction_id.is_(None),
        )
        .update({
            BoostyOperation.operation_type: OPERATION_SUBSCRIPTION_UPGRADE,
            BoostyOperation.status: OPERATION_NEW,
            BoostyOperation.processed_at: None,
            BoostyOperation.processing_started_at: None,
            BoostyOperation.processing_attempts: 0,
            BoostyOperation.last_error: None,
            BoostyOperation.ignored_reason: None,
        }, synchronize_session=False)
    )


def ensure_link_token(account, settings=None, allow_reissue=False):
    settings = settings or get_settings()
    now = time_utcnow()
    unused = (
        BoostyLinkToken.query
        .filter_by(account_id=account.id, used_at=None)
        .order_by(BoostyLinkToken.created_at.desc())
        .with_for_update()
        .all()
    )
    active = next((item for item in unused if item.expires_at > now), None)
    if not allow_reissue:
        # The raw value cannot be recovered from the hash. Returning the latest
        # token without creating a replacement guarantees that polling sends
        # only the first automatic link message, even after it expires.
        if active:
            return active, None
        if unused:
            return unused[0], None

    for item in unused:
        if item.expires_at > now:
            item.expires_at = now

    raw_token = secrets.token_urlsafe(24)
    digest = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    ttl = max(int(settings.get("boosty_link_token_ttl_minutes") or 60), 5)
    token = BoostyLinkToken(
        account=account,
        token_hash=digest,
        token_hint=raw_token[-8:],
        expires_at=now + datetime.timedelta(minutes=ttl),
    )
    db_hub.session.add(token)
    return token, raw_token


def _send_account_message(account_id, message, token_id=None):
    account = BoostyAccount.query.get(account_id)
    token = BoostyLinkToken.query.get(token_id) if token_id else None
    try:
        with BoostyApiClient(current_app.config) as client:
            if not account.dialog_id:
                account.dialog_id = client.find_dialog_id(
                    account.external_id,
                    int(current_app.config.get("BOOSTY_DIALOG_SEARCH_MAX_PAGES", 20)),
                )
            if not account.dialog_id:
                raise RuntimeError("Boosty dialog for account {} was not found".format(account.external_id))
            client.send_dialog_message(account.dialog_id, message)
        if token:
            token.message_sent_at = time_utcnow()
            token.send_error = None
        db_hub.session.commit()
        return True
    except Exception as exc:
        db_hub.session.rollback()
        if token:
            token = BoostyLinkToken.query.get(token_id)
            token.send_error = str(exc)
            token.expires_at = time_utcnow()
            db_hub.session.commit()
        logger.exception("Failed to send Boosty message to account %s", account_id)
        return False


def _send_link_token(account, token, raw_token, settings):
    link_url = public_link_url()
    message = format_message(
        settings.get("boosty_message_token"),
        boostyName=account.name or account.external_id,
        token=raw_token,
        expiresAt=format_moscow_datetime(token.expires_at),
        user="",
        amount="",
        opix="",
    )
    # Existing installations can have the old editable template persisted in
    # settings. Keep custom text, but always include the canonical full URL.
    if link_url and link_url not in message:
        message = "{}\nСтраница привязки: {}".format(message.rstrip(), link_url)
    sent = _send_account_message(account.id, message, token.id)
    operations = (
        BoostyOperation.query
        .filter_by(account_id=account.id, status=OPERATION_PENDING_LINK)
        .all()
    )
    for operation in operations:
        record_history(operation, "LinkMessageSent" if sent else "LinkMessageError", None if sent else token.send_error)
    if operations:
        db_hub.session.commit()
    return sent


def request_new_link_token(email, settings=None):
    """Issue a replacement token after an explicit, rate-limited user request.

    ``accepted`` is intentionally also returned for unknown/linked accounts so
    the profile page cannot be used to enumerate Boosty email addresses.
    """
    settings = settings or get_settings()
    if not settings.get("boosty_integration_enabled"):
        return "unavailable"

    normalized_email = str(email or "").strip().lower()
    account_ids = [
        item[0] for item in
        BoostyAccount.query.with_entities(BoostyAccount.id)
        .filter(func.lower(BoostyAccount.email) == normalized_email)
        .limit(2)
        .all()
    ]
    if len(account_ids) != 1:
        return "accepted"

    account = BoostyAccount.query.filter_by(id=account_ids[0]).with_for_update().one()
    if BoostyAccountLink.query.filter_by(account_id=account.id).first() is not None:
        db_hub.session.rollback()
        return "accepted"

    now = time_utcnow()
    latest = (
        BoostyLinkToken.query
        .filter_by(account_id=account.id, used_at=None)
        .order_by(BoostyLinkToken.created_at.desc())
        .with_for_update()
        .first()
    )
    cooldown = max(int(current_app.config.get("BOOSTY_LINK_TOKEN_RESEND_COOLDOWN_SECONDS", 300)), 0)
    if (
        latest is not None
        and latest.send_error is None
        and latest.created_at > now - datetime.timedelta(seconds=cooldown)
    ):
        db_hub.session.commit()
        return "accepted"

    token, raw_token = ensure_link_token(account, settings, allow_reissue=True)
    db_hub.session.flush()
    token_id = token.id
    account_id = account.id
    db_hub.session.commit()

    token = BoostyLinkToken.query.get(token_id)
    account = BoostyAccount.query.get(account_id)
    return "sent" if _send_link_token(account, token, raw_token, settings) else "failed"


def process_operation(operation_id, force=False, allow_exhausted_attempts=False):
    settings = get_settings()
    token_to_send = None
    account_id = None
    try:
        account_id = (
            BoostyOperation.query.with_entities(BoostyOperation.account_id)
            .filter_by(id=operation_id)
            .scalar()
        )
        if account_id is None:
            db_hub.session.rollback()
            return None
        account = BoostyAccount.query.filter_by(id=account_id).with_for_update().one()
        operation = (
            BoostyOperation.query
            .filter_by(id=operation_id)
            .with_for_update()
            .one()
        )
        if operation.status in (OPERATION_PROCESSED, OPERATION_IGNORED):
            db_hub.session.commit()
            return operation
        maximum_attempts = int(current_app.config.get("BOOSTY_OPERATION_MAX_ATTEMPTS", 10))
        if not force and not allow_exhausted_attempts and operation.processing_attempts >= maximum_attempts:
            db_hub.session.commit()
            return operation
        # Serialize linking/token work per Boosty account. Different donations
        # from the same account can otherwise race and generate two live tokens.
        link = BoostyAccountLink.query.filter_by(account_id=operation.account_id).first()
        if link is None:
            if operation.status == OPERATION_PENDING_LINK and not settings.get("boosty_automatic_linking_enabled"):
                db_hub.session.commit()
                return operation
            operation.processing_attempts += 1
            operation.status = OPERATION_PENDING_LINK
            operation.last_error = None
            record_history(operation, "UserNotLinked")
            record_history(operation, "PendingLink")
            if settings.get("boosty_automatic_linking_enabled"):
                token, raw_token = ensure_link_token(account, settings)
                if raw_token:
                    db_hub.session.flush()
                    token_to_send = (token.id, raw_token)
                    account_id = operation.account_id
            queue_event("boosty.donation.pending_link", operation_data(operation), operation.id)
            db_hub.session.commit()
            if token_to_send:
                token = BoostyLinkToken.query.get(token_to_send[0])
                account = BoostyAccount.query.get(account_id)
                _send_link_token(account, token, token_to_send[1], settings)
            return BoostyOperation.query.get(operation_id)

        if not force and not settings.get("boosty_automatic_opyx_enabled"):
            db_hub.session.commit()
            return operation

        operation.processing_attempts += 1
        operation.status = OPERATION_PROCESSING
        operation.processing_started_at = time_utcnow()
        operation.forum_user_id = link.forum_user_id
        operation.player_id = link.player_id
        operation.last_error = None
        record_history(operation, "ProcessingStarted")

        calculation = calculate_opyx(operation.amount, settings)
        operation.base_rate = calculation.base_rate
        operation.bonus_percent = calculation.bonus_percent
        operation.final_rate = calculation.final_rate
        operation.opyx_amount = calculation.opyx
        if not calculation.eligible:
            operation.status = OPERATION_IGNORED
            operation.ignored_reason = calculation.reason
            operation.processed_at = time_utcnow()
            record_history(operation, "Ignored", calculation.reason)
            queue_event("boosty.operation.ignored", operation_data(operation), operation.id)
            db_hub.session.commit()
            return BoostyOperation.query.get(operation_id)

        if operation.points_transaction_id is not None:
            raise RuntimeError("Operation already references an Opyx transaction")

        points = add_points_transaction_and_notify(
            player=link.player,
            amount=int(calculation.opyx),
            reason="Boosty {} {} ({} RUB)".format(
                operation.operation_type,
                operation.external_id,
                operation.amount,
            ),
            commit=False,
            notify=False,
            transaction_type="donation",
        )
        operation.points_transaction_id = points.id
        operation.status = OPERATION_PROCESSED
        operation.processed_at = time_utcnow()
        record_history(operation, "OpyxGranted", details={"pointsTransactionId": points.id, "amount": str(calculation.opyx)})
        record_history(operation, "Completed")
        queue_event("boosty.donation.processed", operation_data(operation), operation.id)
        db_hub.session.commit()

        _dispatch_committed_points_notifications(points.id)

        try:
            from .discord_roles import queue_account_role_sync
            queue_account_role_sync(operation.account_id, operation.id, include_donator=True)
        except Exception:
            logger.exception("Failed to enqueue Discord synchronization for operation %s", operation.id)

        message = format_message(
            settings.get("boosty_message_opyx_credited"),
            boostyName=operation.account.name or operation.account.external_id,
            amount=str(operation.amount),
            opix=str(operation.opyx_amount),
            user=str(operation.forum_user_id),
            token="",
            expiresAt="",
        )
        _send_account_message(operation.account_id, message)
        return BoostyOperation.query.get(operation_id)
    except Exception as exc:
        db_hub.session.rollback()
        operation = BoostyOperation.query.get(operation_id)
        if operation and operation.status != OPERATION_PROCESSED:
            operation.status = OPERATION_ERROR
            operation.processing_attempts += 1
            operation.last_error = str(exc)
            notify_processing_error = operation.processing_attempts == 1
            failed_account_id = operation.account_id
            record_history(operation, "ProcessingError", str(exc))
            queue_event("boosty.operation.failed", operation_data(operation), operation.id)
            db_hub.session.commit()
            if notify_processing_error:
                error_message = format_message(
                    settings.get("boosty_message_processing_error"),
                    boostyName=operation.account.name or operation.account.external_id,
                    user=str(operation.forum_user_id or ""),
                    token="",
                    amount=str(operation.amount),
                    opix="",
                    expiresAt="",
                )
                _send_account_message(failed_account_id, error_message)
        logger.exception("Failed to process Boosty operation %s", operation_id)
        return operation


def preview_operation(operation):
    return calculate_opyx(operation.amount, get_settings())


def _ensure_player_for_user(forum_user):
    if not forum_user.discord:
        raise ValueError("Forum user has no Discord account")
    discord_id = str(forum_user.discord)
    discord_user = DiscordUser.query.get(discord_id)
    if discord_user is None:
        discord_user = DiscordUser(id=discord_id, nickname=forum_user.display_name)
        db_hub.session.add(discord_user)
        db_hub.session.flush()
    player = Player.query.filter_by(discord_user_id=discord_id).first()
    if player is None:
        player = Player(discord_user_id=discord_id)
        db_hub.session.add(player)
        db_hub.session.flush()
    return player


def _link_account(account, forum_user, linked_by_user_id=None, allow_relink=False):
    link = BoostyAccountLink.query.filter_by(account_id=account.id).with_for_update().first()
    if link and link.forum_user_id != forum_user.id and not allow_relink:
        raise ValueError("Boosty account is already linked to another forum user")
    player = _ensure_player_for_user(forum_user)
    if link is None:
        link = BoostyAccountLink(account=account)
        db_hub.session.add(link)
    link.forum_user_id = forum_user.id
    link.player_id = player.id
    link.linked_by_user_id = linked_by_user_id
    link.linked_at = time_utcnow()
    link.updated_at = time_utcnow()
    return link


def _queue_tier_role_removals(account_id, discord_user_id):
    settings = get_settings()
    if not discord_user_id or not settings.get("boosty_discord_sync_enabled"):
        return
    guild_id = str(settings.get("boosty_discord_guild_id") or "")
    if not guild_id:
        return
    from .discord_roles import queue_role_removal
    from .models import BoostyDiscordRoleMapping
    role_ids = {
        item[0] for item in
        BoostyDiscordRoleMapping.query.with_entities(BoostyDiscordRoleMapping.role_id)
        .filter_by(guild_id=guild_id)
        .all()
    }
    for role_id in role_ids:
        queue_role_removal(account_id, guild_id, role_id, discord_user_id)


def redeem_link_token(raw_token, forum_user):
    digest = hashlib.sha256(str(raw_token).strip().encode("utf-8")).hexdigest()
    now = time_utcnow()
    token = BoostyLinkToken.query.filter_by(token_hash=digest).with_for_update().first()
    if token is None or token.used_at is not None:
        raise ValueError("Invalid or already used Boosty link token")
    if token.expires_at <= now:
        raise ValueError("Boosty link token has expired")

    account = BoostyAccount.query.filter_by(id=token.account_id).with_for_update().one()
    pending = (
        BoostyOperation.query
        .filter_by(account_id=token.account_id, status=OPERATION_PENDING_LINK)
        .with_for_update()
        .all()
    )
    link = _link_account(account, forum_user, forum_user.id, allow_relink=False)
    token.used_at = now
    token.used_by_forum_user_id = forum_user.id
    for operation in pending:
        operation.status = OPERATION_NEW
        operation.forum_user_id = forum_user.id
        operation.player_id = link.player_id
        record_history(operation, "AccountLinked", details={"forumUserId": forum_user.id})
    queue_event(
        "boosty.account.linked",
        {"boostyAccountId": token.account.external_id, "forumUserId": forum_user.id, "pendingOperations": len(pending)},
    )
    db_hub.session.commit()

    processed = 0
    for operation in pending:
        if process_operation(operation.id, allow_exhausted_attempts=True).status == OPERATION_PROCESSED:
            processed += 1
    if processed:
        queue_event(
            "boosty.pending_donations.processed",
            {"boostyAccountId": token.account.external_id, "processed": processed},
        )
        db_hub.session.commit()
    settings = get_settings()
    message = format_message(
        settings.get("boosty_message_link_success"),
        boostyName=token.account.name or token.account.external_id,
        user=forum_user.display_name,
        token="",
        amount="",
        opix="",
        expiresAt="",
    )
    _send_account_message(token.account_id, message)
    try:
        from .discord_roles import queue_account_role_sync
        if not processed:
            queue_account_role_sync(token.account_id, include_donator=False)
    except Exception:
        logger.exception("Failed to enqueue Discord synchronization after Boosty link")
    return link, processed


def manual_link(account, forum_user, administrator):
    account = BoostyAccount.query.filter_by(id=account.id).with_for_update().one()
    pending = (
        BoostyOperation.query
        .filter_by(account_id=account.id, status=OPERATION_PENDING_LINK)
        .with_for_update()
        .all()
    )
    existing_link = BoostyAccountLink.query.filter_by(account_id=account.id).first()
    previous = existing_link.forum_user_id if existing_link else None
    previous_discord_user_id = (
        existing_link.player.discord_user_id
        if existing_link and existing_link.player else None
    )
    link = _link_account(account, forum_user, administrator.id, allow_relink=True)
    for operation in pending:
        operation.status = OPERATION_NEW
        operation.forum_user_id = forum_user.id
        operation.player_id = link.player_id
        record_history(operation, "AccountLinked", "Manual administrative link")
    queue_event(
        "boosty.account.linked",
        {"boostyAccountId": account.external_id, "forumUserId": forum_user.id, "previousForumUserId": previous},
    )
    db_hub.session.commit()
    # A manual link is not permission to bypass the automatic Opyx kill switch.
    processed = sum(
        process_operation(operation.id, allow_exhausted_attempts=True).status == OPERATION_PROCESSED
        for operation in pending
    )
    audit_admin_action(
        administrator,
        "Boosty account {} linked to forum user {} (previous: {})".format(account.external_id, forum_user.id, previous),
    )
    if previous is not None and previous != forum_user.id:
        try:
            _queue_tier_role_removals(account.id, previous_discord_user_id)
        except Exception:
            logger.exception("Failed to enqueue old Discord tier role removal after Boosty relink")
    try:
        from .discord_roles import queue_account_role_sync
        if not processed:
            queue_account_role_sync(account.id, include_donator=False)
    except Exception:
        logger.exception("Failed to enqueue Discord synchronization after manual Boosty link")
    return link, processed


def unlink_account(account, administrator):
    BoostyAccount.query.filter_by(id=account.id).with_for_update().one()
    link = BoostyAccountLink.query.filter_by(account_id=account.id).with_for_update().first()
    if link is None:
        return False
    previous = link.forum_user_id
    previous_discord_user_id = link.player.discord_user_id if link.player else None
    db_hub.session.delete(link)
    queue_event("boosty.account.unlinked", {"boostyAccountId": account.external_id, "forumUserId": previous})
    db_hub.session.commit()
    try:
        _queue_tier_role_removals(account.id, previous_discord_user_id)
    except Exception:
        logger.exception("Failed to enqueue Discord tier role removal after Boosty unlink")
    audit_admin_action(administrator, "Boosty account {} unlinked from forum user {}".format(account.external_id, previous))
    return True


def mark_ignored(operation, reason, administrator):
    operation = BoostyOperation.query.filter_by(id=operation.id).with_for_update().one()
    if operation.status == OPERATION_PROCESSED or operation.points_transaction_id is not None:
        raise ValueError("Processed operation cannot be marked ignored")
    operation.status = OPERATION_IGNORED
    operation.ignored_reason = reason
    operation.processed_at = time_utcnow()
    record_history(operation, "Ignored", reason, {"administratorId": administrator.id})
    queue_event("boosty.operation.ignored", operation_data(operation), operation.id)
    db_hub.session.commit()
    audit_admin_action(administrator, "Boosty operation {} marked ignored: {}".format(operation.external_id, reason))


def add_manual_correction(operation, amount, reason, administrator):
    amount = Decimal(str(amount))
    if amount == ZERO or amount != amount.to_integral_value():
        raise ValueError("Opyx correction must be a non-zero whole number")
    operation = BoostyOperation.query.filter_by(id=operation.id).with_for_update().one()
    if not operation.player_id:
        raise ValueError("Operation is not linked to a player")
    points = add_points_transaction_and_notify(
        player=operation.player,
        amount=int(amount),
        reason="Manual correction for Boosty operation {}: {}".format(operation.external_id, reason),
        commit=False,
        notify=False,
        transaction_type="other",
    )
    correction = BoostyCorrection(
        operation_id=operation.id,
        points_transaction_id=points.id,
        amount=amount,
        author_user_id=administrator.id,
        reason=reason,
    )
    db_hub.session.add(correction)
    record_history(operation, "ManualCorrection", reason, {"amount": str(amount), "pointsTransactionId": points.id})
    db_hub.session.commit()
    _dispatch_committed_points_notifications(points.id, administrator)
    audit_admin_action(administrator, "Manual Opyx correction {} for Boosty operation {}: {}".format(amount, operation.external_id, reason))
    return correction
