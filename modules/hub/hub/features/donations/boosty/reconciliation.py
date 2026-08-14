import datetime
import hashlib

from flask import current_app
from sqlalchemy import and_, or_

from flaskbb.extensions import db_hub
from flaskbb.user.models import User
from flaskbb.utils.helpers import time_utcnow

from .api import BoostyApiClient, event_external_id, next_page_offset
from .constants import DISCORD_FAILED, ISSUE_CRITICAL, ISSUE_WARNING, OPERATION_ERROR, OPERATION_PROCESSED, OPERATION_PROCESSING, WEBHOOK_FAILED
from .models import (
    BoostyDiscordAction,
    BoostyAccountLink,
    BoostyOperation,
    BoostyReconciliationIssue,
    BoostyWebhookDelivery,
)
from hub.models import PointsTransaction
from .service import find_operation_for_event
from .webhooks import queue_event


def _fingerprint(issue_type, object_id):
    return hashlib.sha256("{}:{}".format(issue_type, object_id).encode("utf-8")).hexdigest()


def _upsert(issue_type, object_id, severity, message, operation_id=None, details=None):
    fingerprint = _fingerprint(issue_type, object_id)
    issue = BoostyReconciliationIssue.query.filter_by(fingerprint=fingerprint).first()
    now = time_utcnow()
    if issue is None:
        issue = BoostyReconciliationIssue(
            fingerprint=fingerprint,
            issue_type=issue_type,
            severity=severity,
            operation_id=operation_id,
            message=message,
            details=details,
            status="Open",
        )
        db_hub.session.add(issue)
    else:
        issue.severity = severity
        issue.message = message
        issue.details = details
        issue.status = "Open"
        issue.resolved_at = None
        issue.last_seen_at = now
    return fingerprint


def reconcile():
    now = time_utcnow()
    seen = set()
    stuck_minutes = int(current_app.config.get("BOOSTY_STUCK_OPERATION_MINUTES", 15))
    stuck_before = now - datetime.timedelta(minutes=stuck_minutes)

    stuck = BoostyOperation.query.filter(
        or_(
            and_(BoostyOperation.status == OPERATION_PROCESSING, BoostyOperation.processing_started_at < stuck_before),
            and_(BoostyOperation.status == "New", BoostyOperation.received_at < stuck_before),
        ),
    ).all()
    for operation in stuck:
        seen.add(_upsert("OperationStuck", operation.id, ISSUE_WARNING, "Operation is stuck in {}".format(operation.status), operation.id))

    broken = BoostyOperation.query.outerjoin(
        PointsTransaction,
        BoostyOperation.points_transaction_id == PointsTransaction.id,
    ).filter(
        BoostyOperation.status == OPERATION_PROCESSED,
        or_(BoostyOperation.points_transaction_id.is_(None), PointsTransaction.id.is_(None)),
    ).all()
    for operation in broken:
        seen.add(_upsert("ProcessedWithoutOpyx", operation.id, ISSUE_CRITICAL, "Processed operation has no Opyx transaction", operation.id))

    processed = BoostyOperation.query.filter_by(status=OPERATION_PROCESSED).filter(BoostyOperation.points_transaction_id.isnot(None)).all()
    for operation in processed:
        duplicate_count = PointsTransaction.query.filter(PointsTransaction.comment.like("%{}%".format(operation.external_id))).count()
        if duplicate_count > 1:
            seen.add(_upsert(
                "DuplicateOpyxTransaction",
                operation.id,
                ISSUE_CRITICAL,
                "Multiple Opyx transactions reference this Boosty operation",
                operation.id,
                {"count": duplicate_count},
            ))

    errors = BoostyOperation.query.filter_by(status=OPERATION_ERROR).all()
    for operation in errors:
        seen.add(_upsert("OperationError", operation.id, ISSUE_WARNING, operation.last_error or "Operation processing failed", operation.id))

    user_ids = {operation.forum_user_id for operation in BoostyOperation.query.filter(BoostyOperation.forum_user_id.isnot(None)).all()}
    existing_user_ids = {item[0] for item in User.query.with_entities(User.id).filter(User.id.in_(user_ids)).all()} if user_ids else set()
    for user_id in user_ids - existing_user_ids:
        seen.add(_upsert("MissingForumUser", user_id, ISSUE_CRITICAL, "Linked forum user {} does not exist".format(user_id)))

    link_user_ids = {item[0] for item in BoostyAccountLink.query.with_entities(BoostyAccountLink.forum_user_id).all()}
    existing_link_user_ids = {
        item[0] for item in User.query.with_entities(User.id).filter(User.id.in_(link_user_ids)).all()
    } if link_user_ids else set()
    for user_id in link_user_ids - existing_link_user_ids:
        seen.add(_upsert("MissingLinkedForumUser", user_id, ISSUE_CRITICAL, "Boosty link references missing forum user {}".format(user_id)))

    if current_app.config.get("BOOSTY_API_BASE_URL") and current_app.config.get("BOOSTY_BLOG_NAME"):
        page_size = int(current_app.config.get("BOOSTY_EVENTS_PAGE_SIZE", 100))
        lookback_pages = max(int(current_app.config.get("BOOSTY_RECONCILIATION_LOOKBACK_PAGES", 2)), 1)
        lookback_days = max(int(current_app.config.get("BOOSTY_RECONCILIATION_LOOKBACK_DAYS", 7)), 1)
        timestamp_from = int((now - datetime.timedelta(days=lookback_days)).timestamp())
        timestamp_to = int(now.timestamp()) + 1
        offset = 0
        remote_events = []
        with BoostyApiClient(current_app.config) as client:
            for _ in range(lookback_pages):
                events, extra = client.stat_events(timestamp_from, timestamp_to, page_size, offset)
                remote_events.extend(events)
                next_offset = next_page_offset(offset, len(events), extra, page_size)
                if next_offset is None:
                    break
                offset = next_offset
        for payload in remote_events:
            if find_operation_for_event(payload) is None:
                external_id = event_external_id(payload)
                seen.add(_upsert(
                    "RemoteOperationMissingLocally",
                    external_id,
                    ISSUE_CRITICAL,
                    "Boosty event {} is missing locally".format(external_id),
                    details={"externalId": external_id, "eventType": payload.get("eventType")},
                ))

    for delivery in BoostyWebhookDelivery.query.filter_by(status=WEBHOOK_FAILED).all():
        seen.add(_upsert("WebhookFailed", delivery.id, ISSUE_WARNING, delivery.last_error or "Webhook delivery failed", delivery.operation_id))

    for action in BoostyDiscordAction.query.filter_by(status=DISCORD_FAILED).all():
        seen.add(_upsert("DiscordFailed", action.id, ISSUE_WARNING, action.last_error or "Discord synchronization failed", action.operation_id))

    open_issues = BoostyReconciliationIssue.query.filter_by(status="Open").all()
    for issue in open_issues:
        if issue.fingerprint not in seen:
            issue.status = "Resolved"
            issue.resolved_at = now
    db_hub.session.commit()
    return len(seen)


def report_reconciliation_failure(error):
    queue_event("boosty.reconciliation.failed", {"error": str(error)})
    db_hub.session.commit()
