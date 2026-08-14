import datetime
from collections import OrderedDict
from decimal import Decimal

from babel.dates import get_timezone
from sqlalchemy import func

from flaskbb.extensions import db_hub
from flaskbb.utils.helpers import time_utcnow

from .constants import (
    DISCORD_FAILED,
    OPERATION_ERROR,
    OPERATION_PENDING_LINK,
    OPERATION_PROCESSED,
    POINTS_OPERATION_TYPES,
    WEBHOOK_FAILED,
)
from .models import (
    BoostyAccount,
    BoostyAccountLink,
    BoostyDiscordAction,
    BoostyOperation,
    BoostySubscriptionEvent,
    BoostySyncState,
    BoostyWebhookDelivery,
)


def period_bounds(period, date_from=None, date_to=None):
    now = time_utcnow()
    if date_from and date_to:
        return date_from, date_to
    days = {"day": 1, "week": 7, "month": 30, "3months": 90, "year": 365}.get(period, 30)
    return now - datetime.timedelta(days=days), now


def _base_query(start, end):
    return BoostyOperation.query.filter(
        BoostyOperation.operation_type.in_(POINTS_OPERATION_TYPES),
        BoostyOperation.source_created_at >= start,
        BoostyOperation.source_created_at < end,
    )


def _aggregate(start, end):
    query = _base_query(start, end)
    row = query.with_entities(
        func.coalesce(func.sum(BoostyOperation.amount), 0),
        func.count(BoostyOperation.id),
        func.count(func.distinct(BoostyOperation.account_id)),
        func.coalesce(func.avg(BoostyOperation.amount), 0),
        func.coalesce(func.max(BoostyOperation.amount), 0),
        func.coalesce(func.sum(BoostyOperation.opyx_amount), 0),
    ).first()
    return {
        "revenue": Decimal(str(row[0] or 0)),
        "donations": int(row[1] or 0),
        "donators": int(row[2] or 0),
        "average": Decimal(str(row[3] or 0)),
        "maximum": Decimal(str(row[4] or 0)),
        "opyx": Decimal(str(row[5] or 0)),
    }


def _chart(start, end):
    operations = _base_query(start, end).order_by(BoostyOperation.source_created_at.asc()).all()
    points = OrderedDict()
    for operation in operations:
        key = operation.source_created_at.astimezone(get_timezone()).date().isoformat()
        item = points.setdefault(key, {"date": key, "revenue": Decimal("0"), "donations": 0, "donators": set()})
        item["revenue"] += Decimal(str(operation.amount))
        item["donations"] += 1
        item["donators"].add(operation.account_id)
    return [
        {
            "date": item["date"],
            "revenue": str(item["revenue"]),
            "donations": item["donations"],
            "donators": len(item["donators"]),
        }
        for item in points.values()
    ]


def _subscription_chart(start, end):
    events = (
        BoostySubscriptionEvent.query
        .filter(BoostySubscriptionEvent.observed_at >= start, BoostySubscriptionEvent.observed_at < end)
        .order_by(BoostySubscriptionEvent.observed_at.asc())
        .all()
    )
    daily = OrderedDict()
    net_change = 0
    for event in events:
        change = 1 if event.event_name == "Started" else -1 if event.event_name == "Ended" else 0
        net_change += change
        key = event.observed_at.astimezone(get_timezone()).date().isoformat()
        item = daily.setdefault(key, {"date": key, "started": 0, "ended": 0, "changed": 0, "change": 0})
        item[event.event_name.lower()] = item.get(event.event_name.lower(), 0) + 1
        item["change"] += change

    running = BoostyAccount.query.filter_by(is_paid_subscriber=True).count() - net_change
    result = []
    for item in daily.values():
        running += item.pop("change")
        item["subscribers"] = max(running, 0)
        result.append(item)
    return result


def dashboard(period="month", date_from=None, date_to=None):
    now = time_utcnow()
    start, end = period_bounds(period, date_from, date_to)
    duration = end - start
    previous = _aggregate(start - duration, start)
    current = _aggregate(start, end)
    previous_revenue = previous["revenue"]
    change = None
    if previous_revenue:
        change = ((current["revenue"] - previous_revenue) / previous_revenue * Decimal("100")).quantize(Decimal("0.01"))

    state = BoostySyncState.query.get(1)
    pending_query = BoostyOperation.query.filter_by(status=OPERATION_PENDING_LINK)
    failed_operations = BoostyOperation.query.filter_by(status=OPERATION_ERROR).count()
    discord_failures = BoostyDiscordAction.query.filter_by(status=DISCORD_FAILED).count()
    webhook_failures = BoostyWebhookDelivery.query.filter_by(status=WEBHOOK_FAILED).count()
    stale_after = datetime.timedelta(seconds=180)
    if state and state.last_successful_sync_at:
        stale_after = datetime.timedelta(seconds=max(180, int((state.next_sync_at - state.last_successful_sync_at).total_seconds()) * 3) if state.next_sync_at else 180)
    if state and state.last_error:
        health = "Error"
    elif failed_operations or discord_failures or webhook_failures or not state or not state.last_successful_sync_at or state.last_successful_sync_at + stale_after < now:
        health = "Warning"
    else:
        health = "Healthy"

    local_now = now.astimezone(get_timezone())
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(datetime.timezone.utc)
    local_today_start = today_start.astimezone(get_timezone())
    week_start = (local_today_start - datetime.timedelta(days=local_today_start.weekday())).astimezone(datetime.timezone.utc)
    month_start = local_today_start.replace(day=1).astimezone(datetime.timezone.utc)
    subscription_events = BoostySubscriptionEvent.query.filter(
        BoostySubscriptionEvent.observed_at >= start,
        BoostySubscriptionEvent.observed_at < end,
    )
    return {
        "period": period,
        "start": start,
        "end": end,
        "current": current,
        "previous": previous,
        "changePercent": change,
        "todayRevenue": _aggregate(today_start, now)["revenue"],
        "weekRevenue": _aggregate(week_start, now)["revenue"],
        "monthRevenue": _aggregate(month_start, now)["revenue"],
        "linkedAccounts": BoostyAccountLink.query.count(),
        "unlinkedAccounts": BoostyAccount.query.outerjoin(BoostyAccountLink).filter(BoostyAccountLink.id.is_(None)).count(),
        "paidSubscribers": BoostyAccount.query.filter_by(is_paid_subscriber=True).count(),
        "newPaidSubscribers": subscription_events.filter_by(event_name="Started").count(),
        "endedSubscriptions": subscription_events.filter_by(event_name="Ended").count(),
        "tierChanges": subscription_events.filter_by(event_name="Changed").count(),
        "pendingOperations": pending_query.count(),
        "pendingAmount": Decimal(str(pending_query.with_entities(func.coalesce(func.sum(BoostyOperation.amount), 0)).scalar() or 0)),
        "failedOperations": failed_operations,
        "discordFailures": discord_failures,
        "webhookFailures": webhook_failures,
        "health": health,
        "state": state,
        "lastOperation": BoostyOperation.query.order_by(BoostyOperation.received_at.desc()).first(),
        "chart": _chart(start, end),
        "subscriptionChart": _subscription_chart(start, end),
    }
