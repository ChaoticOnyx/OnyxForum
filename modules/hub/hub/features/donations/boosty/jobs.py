import logging

from flaskbb.extensions import scheduler

from .sync import synchronize
from .webhooks import process_pending_deliveries
from .discord_roles import process_pending_role_actions


logger = logging.getLogger("donations.boosty.jobs")


def _scheduled_sync():
    with scheduler.app.app_context():
        try:
            synchronize()
        except Exception:
            logger.exception("Scheduled Boosty synchronization failed")


def _scheduled_webhooks():
    with scheduler.app.app_context():
        try:
            process_pending_deliveries()
        except Exception:
            logger.exception("Scheduled Boosty webhook processing failed")


def _scheduled_reconciliation():
    with scheduler.app.app_context():
        try:
            from .reconciliation import reconcile
            reconcile()
        except Exception as exc:
            try:
                from .reconciliation import report_reconciliation_failure
                report_reconciliation_failure(exc)
            except Exception:
                logger.exception("Failed to queue Boosty reconciliation failure event")
            logger.exception("Scheduled Boosty reconciliation failed")


def _scheduled_discord():
    with scheduler.app.app_context():
        try:
            process_pending_role_actions()
        except Exception:
            logger.exception("Scheduled Boosty Discord recovery failed")


def register_boosty_jobs(app):
    jobs = (
        ("boosty_operations_poll", _scheduled_sync, int(app.config.get("BOOSTY_POLLING_INTERVAL_SECONDS", 60))),
        ("boosty_webhook_delivery", _scheduled_webhooks, int(app.config.get("BOOSTY_WEBHOOK_JOB_INTERVAL_SECONDS", 15))),
        ("boosty_discord_recovery", _scheduled_discord, int(app.config.get("BOOSTY_DISCORD_JOB_INTERVAL_SECONDS", 60))),
        ("boosty_reconciliation", _scheduled_reconciliation, int(app.config.get("BOOSTY_RECONCILIATION_INTERVAL_SECONDS", 3600))),
    )
    for job_id, function, seconds in jobs:
        if scheduler.get_job(job_id) is None:
            scheduler.add_job(
                id=job_id,
                func=function,
                trigger="interval",
                seconds=seconds,
                coalesce=True,
                max_instances=1,
                misfire_grace_time=max(seconds, 60),
                replace_existing=False,
            )
