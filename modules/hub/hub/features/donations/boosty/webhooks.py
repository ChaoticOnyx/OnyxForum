import datetime
import logging
import uuid

import requests
from flask import current_app

from flaskbb.extensions import db_hub
from flaskbb.utils.helpers import time_utcnow

from .constants import WEBHOOK_DELIVERED, WEBHOOK_FAILED, WEBHOOK_PENDING
from .models import BoostyProcessingEvent, BoostyWebhookDelivery, BoostyWebhookEndpoint
from .settings import get_settings
from .signing import calculate_signature
from .webhook_payload import serialize_delivery_payload


logger = logging.getLogger("donations.boosty.webhooks")


def queue_event(event_name, data, operation_id=None, endpoint_id=None, force=False):
    settings = get_settings()
    if not force and not settings.get("boosty_outgoing_webhooks_enabled"):
        return []

    query = BoostyWebhookEndpoint.query.filter_by(enabled=True, deleted_at=None)
    if endpoint_id is not None:
        query = query.filter_by(id=endpoint_id)
    endpoints = query.all()
    event_id = str(uuid.uuid4())
    created_at = time_utcnow()
    envelope = {
        "eventId": event_id,
        "event": event_name,
        "createdAt": created_at.isoformat(),
        "data": data,
    }
    deliveries = []
    for endpoint in endpoints:
        selected_events = endpoint.events or []
        if not force and event_name not in selected_events:
            continue
        delivery = BoostyWebhookDelivery(
            event_id=event_id,
            event_name=event_name,
            endpoint_id=endpoint.id,
            operation_id=operation_id,
            payload=envelope,
            status=WEBHOOK_PENDING,
            next_attempt_at=created_at,
        )
        db_hub.session.add(delivery)
        deliveries.append(delivery)
    return deliveries


def _deliver(delivery, now):
    endpoint = delivery.endpoint
    if not endpoint.enabled or endpoint.deleted_at is not None:
        delivery.status = WEBHOOK_FAILED
        delivery.next_attempt_at = None
        delivery.last_error = "Webhook endpoint is disabled or archived"
        return
    timestamp = str(int(now.timestamp()))
    body = serialize_delivery_payload(delivery.payload, endpoint.url)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": delivery.event_name,
        "X-Webhook-Event-Id": delivery.event_id,
        "X-Webhook-Timestamp": timestamp,
        "X-Webhook-Signature": calculate_signature(endpoint.secret, timestamp, body),
    }
    delivery.attempts += 1
    delivery.last_attempt_at = now
    try:
        response = requests.post(
            endpoint.url,
            data=body.encode("utf-8"),
            headers=headers,
            timeout=endpoint.timeout_seconds,
        )
        delivery.http_status = response.status_code
        if 200 <= response.status_code < 300:
            delivery.status = WEBHOOK_DELIVERED
            delivery.last_error = None
            delivery.next_attempt_at = None
            endpoint.last_delivery_status = WEBHOOK_DELIVERED
            endpoint.last_error = None
            if delivery.operation_id:
                db_hub.session.add(BoostyProcessingEvent(
                    operation_id=delivery.operation_id,
                    event="WebhookDelivered",
                    details={"deliveryId": delivery.id, "endpointId": endpoint.id},
                ))
            return
        error = "HTTP {}: {}".format(response.status_code, response.text[:1000])
    except requests.RequestException as exc:
        error = str(exc)

    delivery.last_error = error
    endpoint.last_error = error
    maximum_attempts = endpoint.retry_count + 1
    if delivery.attempts >= maximum_attempts:
        delivery.status = WEBHOOK_FAILED
        delivery.next_attempt_at = None
        endpoint.last_delivery_status = WEBHOOK_FAILED
        if delivery.operation_id:
            db_hub.session.add(BoostyProcessingEvent(
                operation_id=delivery.operation_id,
                event="WebhookFailed",
                message=error,
                details={"deliveryId": delivery.id, "endpointId": endpoint.id},
            ))
    else:
        delivery.status = WEBHOOK_PENDING
        base = int(current_app.config.get("BOOSTY_WEBHOOK_RETRY_BACKOFF_SECONDS", 10))
        maximum = int(current_app.config.get("BOOSTY_WEBHOOK_MAX_BACKOFF_SECONDS", 3600))
        delay = min(base * (2 ** (delivery.attempts - 1)), maximum)
        delivery.next_attempt_at = now + datetime.timedelta(seconds=delay)
        endpoint.last_delivery_status = WEBHOOK_PENDING


def process_pending_deliveries(limit=50):
    if not get_settings().get("boosty_outgoing_webhooks_enabled"):
        return 0
    now = time_utcnow()
    delivery_ids = [
        item[0] for item in
        BoostyWebhookDelivery.query.with_entities(BoostyWebhookDelivery.id)
        .filter(BoostyWebhookDelivery.status == WEBHOOK_PENDING)
        .filter(BoostyWebhookDelivery.next_attempt_at <= now)
        .order_by(BoostyWebhookDelivery.created_at.asc())
        .limit(limit)
        .all()
    ]
    processed = 0
    for delivery_id in delivery_ids:
        try:
            delivery = (
                BoostyWebhookDelivery.query
                .filter_by(id=delivery_id, status=WEBHOOK_PENDING)
                .filter(BoostyWebhookDelivery.next_attempt_at <= time_utcnow())
                .with_for_update()
                .first()
            )
            if delivery is None:
                db_hub.session.rollback()
                continue
            lease_seconds = max(int(delivery.endpoint.timeout_seconds), 1) + 60
            delivery.next_attempt_at = time_utcnow() + datetime.timedelta(seconds=lease_seconds)
            db_hub.session.commit()
            delivery = BoostyWebhookDelivery.query.get(delivery_id)
            _deliver(delivery, now)
            db_hub.session.commit()
            processed += 1
        except Exception:
            db_hub.session.rollback()
            logger.exception("Unexpected webhook delivery failure for %s", delivery_id)
    return processed


def retry_delivery(delivery):
    delivery.status = WEBHOOK_PENDING
    delivery.next_attempt_at = time_utcnow()
    delivery.last_error = None
    db_hub.session.add(delivery)


def queue_test(endpoint):
    return queue_event(
        "boosty.test",
        {"endpoint": endpoint.name, "message": "Boosty webhook test"},
        endpoint_id=endpoint.id,
        force=True,
    )
