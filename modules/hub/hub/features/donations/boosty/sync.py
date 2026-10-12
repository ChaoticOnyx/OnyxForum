import datetime
import logging
from decimal import Decimal

from flask import current_app

from flaskbb.extensions import db_hub
from flaskbb.utils.helpers import time_utcnow

from .api import BoostyApiClient, event_external_id, next_page_offset
from .constants import OPERATION_ERROR, OPERATION_NEW, OPERATION_PENDING_LINK, SUBSCRIPTION_EVENT_TYPES
from .models import BoostyAccount, BoostyLinkToken, BoostyOperation, BoostySubscriptionEvent, BoostySyncState
from .service import (
    ingest_event,
    process_operation,
    requeue_ignored_subscription_upgrades,
)
from .settings import get_settings
from .webhooks import queue_event


logger = logging.getLogger("donations.boosty.sync")


def get_sync_state(for_update=False):
    query = BoostySyncState.query.filter_by(id=1)
    if for_update:
        query = query.with_for_update()
    state = query.first()
    if state is None:
        state = BoostySyncState(id=1)
        db_hub.session.add(state)
        db_hub.session.flush()
    return state


def _sync_subscribers(client, state):
    now = time_utcnow()
    interval = int(current_app.config.get("BOOSTY_SUBSCRIBERS_POLL_INTERVAL_SECONDS", 300))
    if state.last_subscription_sync_at and state.last_subscription_sync_at + datetime.timedelta(seconds=interval) > now:
        return 0

    page_size = int(current_app.config.get("BOOSTY_SUBSCRIBERS_PAGE_SIZE", 100))
    offset = 0
    changed_accounts = []
    total_seen = 0
    while True:
        subscribers, page = client.subscribers(page_size, offset)
        if not subscribers:
            break
        for subscriber in subscribers:
            external_id = str(subscriber.get("id") or "")
            if not external_id:
                continue
            account = BoostyAccount.query.filter_by(external_id=external_id).with_for_update().first()
            if account is None:
                account = BoostyAccount(external_id=external_id)
                db_hub.session.add(account)
            old_paid = bool(account.is_paid_subscriber)
            old_tier = account.tier_id
            level = subscriber.get("level") or {}
            price = Decimal(str((level.get("currencyPrices") or {}).get("RUB", level.get("price") or 0)))
            status = str(subscriber.get("status") or "")
            paid = bool(subscriber.get("subscribed") and status == "active" and price > 0)
            account.name = subscriber.get("name") or account.name
            account.email = subscriber.get("email") or account.email
            account.tier_id = str(level.get("id")) if level.get("id") is not None else None
            account.tier_name = level.get("name")
            account.subscription_status = status
            account.is_paid_subscriber = paid
            account.last_seen_at = now

            event = None
            # The first snapshot is a baseline. Later snapshots use Boosty's
            # current status/tier as the authoritative state transition source.
            if state.last_subscription_sync_at is not None:
                if not old_paid and paid:
                    event = "boosty.subscription.started"
                elif old_paid and not paid:
                    event = "boosty.subscription.ended"
                elif old_paid and paid and old_tier != account.tier_id:
                    event = "boosty.subscription.changed"
            if event:
                db_hub.session.add(BoostySubscriptionEvent(
                    account=account,
                    event_name=event.rsplit(".", 1)[-1].title(),
                    previous_tier_id=old_tier,
                    tier_id=account.tier_id,
                    tier_name=account.tier_name,
                    subscription_status=status,
                    observed_at=now,
                ))
                queue_event(event, {
                    "boostyAccountId": external_id,
                    "tierId": account.tier_id,
                    "tierName": account.tier_name,
                    "status": status,
                    "previousTierId": old_tier,
                })
            if account.link and (event or state.last_subscription_sync_at is None):
                changed_accounts.append(account)
            total_seen += 1

        db_hub.session.flush()
        next_offset = next_page_offset(offset, len(subscribers), page, page_size)
        if next_offset is None:
            break
        offset = next_offset

    state.last_subscription_sync_at = now
    db_hub.session.commit()
    for account in changed_accounts:
        if account.link:
            try:
                from .discord_roles import queue_account_role_sync
                queue_account_role_sync(account.id)
            except Exception:
                logger.exception("Failed to queue subscription role sync for Boosty account %s", account.id)
    return total_seen


def synchronize(force=False):
    settings = get_settings()
    if not settings.get("boosty_integration_enabled"):
        return {"skipped": True, "reason": "Boosty integration is disabled", "received": 0, "processed": 0}

    now = time_utcnow()
    state = get_sync_state(for_update=True)
    if not force and state.next_sync_at and state.next_sync_at > now:
        db_hub.session.rollback()
        return {"skipped": True, "reason": "Synchronization is not due", "received": 0, "processed": 0}
    interval = max(int(settings.get("boosty_polling_interval") or 60), 60)
    state.last_sync_started_at = now
    state.next_sync_at = now + datetime.timedelta(seconds=interval)
    db_hub.session.commit()

    requeued = requeue_ignored_subscription_upgrades()
    if requeued:
        logger.info(
            "Requeued %s previously ignored Boosty subscription upgrades",
            requeued,
        )
    db_hub.session.commit()

    received_ids = []
    received_count = 0
    processed = 0
    try:
        with BoostyApiClient(current_app.config) as client:
            state = get_sync_state()
            page_size = int(current_app.config.get("BOOSTY_EVENTS_PAGE_SIZE", 100))
            max_pages = int(current_app.config.get("BOOSTY_EVENTS_MAX_PAGES_PER_SYNC", 100))
            initial_days = max(int(current_app.config.get("BOOSTY_EVENTS_INITIAL_BACKFILL_DAYS", 31)), 1)
            lookback_seconds = max(int(current_app.config.get("BOOSTY_EVENTS_LOOKBACK_SECONDS", 300)), 0)
            event_cursor = str(state.last_operation_external_id or "").startswith("event:")
            if force or not event_cursor or not state.last_operation_created_at:
                range_start = now - datetime.timedelta(days=initial_days)
            else:
                range_start = state.last_operation_created_at - datetime.timedelta(seconds=lookback_seconds)
            timestamp_from = max(int(range_start.timestamp()), 0)
            timestamp_to = int(now.timestamp()) + 1
            reached_boundary = False
            offset = 0
            payloads = []

            for _ in range(max_pages):
                events, extra = client.stat_events(timestamp_from, timestamp_to, page_size, offset)
                if not events:
                    reached_boundary = True
                    break
                payloads.extend(events)
                next_offset = next_page_offset(offset, len(events), extra, page_size)
                if next_offset is None:
                    reached_boundary = True
                    break
                offset = next_offset

            if not reached_boundary:
                raise RuntimeError(
                    "Boosty events page limit was reached before a safe history boundary; "
                    "increase BOOSTY_EVENTS_MAX_PAGES_PER_SYNC"
                )

            subscription_account_ids = set()
            newest = max(payloads, key=lambda item: int(item.get("createdAt") or 0)) if payloads else None
            for payload in sorted(payloads, key=lambda item: int(item.get("createdAt") or 0)):
                operation, created = ingest_event(payload)
                if created:
                    received_count += 1
                    if operation.status == OPERATION_NEW:
                        received_ids.append(operation.id)
                    if str(payload.get("eventType") or "") in SUBSCRIPTION_EVENT_TYPES:
                        subscription_account_ids.add(operation.account_id)
            db_hub.session.commit()

            for operation_id in received_ids:
                operation = process_operation(operation_id)
                if operation and operation.status == "Processed":
                    processed += 1
                    subscription_account_ids.discard(operation.account_id)

            maximum_attempts = int(current_app.config.get("BOOSTY_OPERATION_MAX_ATTEMPTS", 10))
            retry_ids = [
                item[0] for item in
                BoostyOperation.query.with_entities(BoostyOperation.id)
                .filter(BoostyOperation.status.in_((OPERATION_NEW, OPERATION_ERROR)))
                .filter(BoostyOperation.processing_attempts < maximum_attempts)
                .order_by(BoostyOperation.received_at.asc())
                .limit(100)
                .all()
            ]
            active_token_accounts = (
                BoostyLinkToken.query.with_entities(BoostyLinkToken.account_id)
                .filter(BoostyLinkToken.used_at.is_(None), BoostyLinkToken.expires_at > time_utcnow())
            )
            retry_ids.extend([
                item[0] for item in
                BoostyOperation.query.with_entities(BoostyOperation.id)
                .filter(BoostyOperation.status == OPERATION_PENDING_LINK)
                .filter(~BoostyOperation.account_id.in_(active_token_accounts))
                .filter(BoostyOperation.processing_attempts < maximum_attempts)
                .order_by(BoostyOperation.received_at.asc())
                .limit(100)
                .all()
            ])
            for operation_id in set(retry_ids) - set(received_ids):
                operation = process_operation(operation_id)
                if operation and operation.status == "Processed":
                    processed += 1

            for account_id in subscription_account_ids:
                try:
                    from .discord_roles import queue_account_role_sync
                    queue_account_role_sync(account_id)
                except Exception:
                    logger.exception("Failed to queue event-driven role sync for Boosty account %s", account_id)

            state = get_sync_state(for_update=True)
            if newest:
                state.last_operation_external_id = event_external_id(newest)
                created_at = int(newest.get("createdAt") or 0)
                state.last_operation_created_at = (
                    datetime.datetime.fromtimestamp(created_at, datetime.timezone.utc)
                    if created_at else time_utcnow()
                )
            _sync_subscribers(client, state)

        state = get_sync_state(for_update=True)
        state.last_successful_sync_at = time_utcnow()
        state.last_error = None
        state.last_error_at = None
        state.consecutive_failures = 0
        db_hub.session.commit()
        return {
            "skipped": False,
            "received": received_count,
            "processed": processed,
            "requeued": requeued,
        }
    except Exception as exc:
        db_hub.session.rollback()
        state = get_sync_state(for_update=True)
        state.last_error = str(exc)
        state.last_error_at = time_utcnow()
        state.consecutive_failures += 1
        queue_event("boosty.sync.failed", {"error": str(exc), "startedAt": now.isoformat()})
        db_hub.session.commit()
        logger.exception("Boosty synchronization failed")
        raise
