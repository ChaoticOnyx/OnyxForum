import datetime
from decimal import Decimal, InvalidOperation

from flask import abort, current_app, flash, jsonify, redirect, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_babelplus import gettext as _
from babel.dates import get_timezone
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from flaskbb.display.navigation import NavigationLink
from flaskbb.extensions import allows, db_hub, discordClient
from flaskbb.plugins.models import PluginRegistry
from flaskbb.user.models import User
from flaskbb.utils.helpers import FlashAndRedirect, render_template, time_utcnow
from flaskbb.utils.requirements import IsAdmin
from hub.models import DiscordRole

from .analytics import dashboard
from .constants import EVENT_OPERATION_TYPES, OPERATION_STATUSES, OPERATION_UNKNOWN
from .discord_roles import queue_account_role_sync, queue_role_removal, retry_discord_action
from .forms import (
    BoostyLinkTokenForm,
    BoostyLinkTokenRequestForm,
    BoostySettingsForm,
    CorrectionForm,
    DiscordRoleMappingForm,
    IgnoreOperationForm,
    ManualLinkForm,
    WebhookEndpointForm,
)
from .models import (
    BoostyAccount,
    BoostyAccountLink,
    BoostyCorrection,
    BoostyDiscordAction,
    BoostyDiscordRoleMapping,
    BoostyOperation,
    BoostyReconciliationIssue,
    BoostyWebhookDelivery,
    BoostyWebhookEndpoint,
)
from .reconciliation import reconcile
from .service import (
    add_manual_correction,
    audit_admin_action,
    manual_link,
    mark_ignored,
    operation_data,
    preview_operation,
    public_link_url,
    request_new_link_token,
    redeem_link_token,
    unlink_account,
    process_operation,
)
from .settings import DEFAULT_SETTINGS, PLUGIN_SETTINGS, get_settings
from .sync import synchronize
from .webhooks import queue_test, retry_delivery


admin_required = allows.requires(
    IsAdmin,
    on_fail=FlashAndRedirect(
        message=_("You are not allowed to access this page"),
        level="danger",
        endpoint="forum.index",
    ),
)


def _validation_message(form):
    return "; ".join(
        "{}: {}".format(field, ", ".join(errors))
        for field, errors in form.errors.items()
    ) or "Invalid form data"


def _admin_actions():
    return [
        NavigationLink(endpoint="hub.boosty_dashboard", name=_("Dashboard"), icon="fa fa-dashboard"),
        NavigationLink(endpoint="hub.boosty_operations", name=_("История операций"), icon="fa fa-list"),
        NavigationLink(endpoint="hub.boosty_statistics", name=_("Статистика"), icon="fa fa-line-chart"),
        NavigationLink(endpoint="hub.boosty_links", name=_("Boosty ↔ Forum"), icon="fa fa-link"),
        NavigationLink(endpoint="hub.boosty_discord", name=_("Discord roles"), icon="fa fa-discord"),
        NavigationLink(endpoint="hub.boosty_webhooks", name=_("Notifications / Webhooks"), icon="fa fa-bell"),
        NavigationLink(endpoint="hub.boosty_issues", name=_("Reconciliation / Issues"), icon="fa fa-warning"),
        NavigationLink(endpoint="hub.boosty_settings", name=_("Настройки"), icon="fa fa-cog"),
        NavigationLink(endpoint="hub.points_transactions", name=_("Все транзакции Opyx"), icon="fa fa-sun-o"),
    ]


def _queue_linked_account_role_sync():
    if not get_settings().get("boosty_discord_sync_enabled"):
        return 0
    try:
        account_ids = [
            item[0] for item in
            BoostyAccount.query.with_entities(BoostyAccount.id)
            .join(BoostyAccountLink)
            .all()
        ]
    except Exception:
        current_app.logger.exception("Failed to load linked Boosty accounts for Discord sync")
        return 0
    queued = 0
    for account_id in account_ids:
        try:
            queue_account_role_sync(account_id, include_donator=True)
            queued += 1
        except Exception:
            current_app.logger.exception("Failed to queue Boosty Discord sync for account %s", account_id)
    return queued


class BoostyAdminView(MethodView):
    decorators = [admin_required]

    def template_args(self, **kwargs):
        kwargs["actions"] = _admin_actions()
        return kwargs


def _parse_date(value, end=False):
    if not value:
        return None
    try:
        parsed = datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        abort(400, description="Date must use YYYY-MM-DD format")
    if end:
        parsed += datetime.timedelta(days=1)
    local_timezone = get_timezone()
    if hasattr(local_timezone, "localize"):
        parsed = local_timezone.localize(parsed)
    else:
        parsed = parsed.replace(tzinfo=local_timezone)
    return parsed.astimezone(datetime.timezone.utc)


class BoostyDashboardView(BoostyAdminView):
    def get(self):
        period = request.args.get("period", "month")
        date_from = _parse_date(request.args.get("date_from"))
        date_to = _parse_date(request.args.get("date_to"), end=True)
        data = dashboard(period, date_from, date_to)
        return render_template("features/donations/hub/boosty/dashboard.html", **self.template_args(dashboard=data, statistics=False))


class BoostyStatisticsView(BoostyAdminView):
    def get(self):
        period = request.args.get("period", "month")
        date_from = _parse_date(request.args.get("date_from"))
        date_to = _parse_date(request.args.get("date_to"), end=True)
        data = dashboard(period, date_from, date_to)
        return render_template("features/donations/hub/boosty/dashboard.html", **self.template_args(dashboard=data, statistics=True))


def _operation_query():
    query = BoostyOperation.query.join(BoostyAccount)
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    operation_type = request.args.get("type", "").strip()
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"), end=True)
    if search:
        like = "%{}%".format(search)
        query = query.filter(or_(
            BoostyOperation.external_id.like(like),
            BoostyAccount.external_id.like(like),
            BoostyAccount.name.like(like),
            BoostyAccount.email.like(like),
        ))
    if status in OPERATION_STATUSES:
        query = query.filter(BoostyOperation.status == status)
    if operation_type:
        query = query.filter(BoostyOperation.operation_type == operation_type)
    if date_from:
        query = query.filter(BoostyOperation.source_created_at >= date_from)
    if date_to:
        query = query.filter(BoostyOperation.source_created_at < date_to)
    sort = request.args.get("sort", "source_created_at")
    direction = request.args.get("direction", "desc")
    columns = {
        "source_created_at": BoostyOperation.source_created_at,
        "amount": BoostyOperation.amount,
        "status": BoostyOperation.status,
        "processed_at": BoostyOperation.processed_at,
        "external_id": BoostyOperation.external_id,
    }
    column = columns.get(sort, BoostyOperation.source_created_at)
    return query.order_by(column.asc() if direction == "asc" else column.desc())


class BoostyOperationsView(BoostyAdminView):
    def get(self):
        page = request.args.get("page", 1, type=int)
        pagination = _operation_query().paginate(page, 30, False)
        user_ids = {operation.forum_user_id for operation in pagination.items if operation.forum_user_id}
        users = {user.id: user for user in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
        pagination_args = request.args.to_dict()
        pagination_args.pop("page", None)
        return render_template(
            "features/donations/hub/boosty/operations.html",
            **self.template_args(
                pagination=pagination,
                operations=pagination.items,
                users=users,
                statuses=OPERATION_STATUSES,
                operation_types=tuple(dict.fromkeys(EVENT_OPERATION_TYPES.values())) + (OPERATION_UNKNOWN,),
            ),
            pagination_url=url_for("hub.boosty_operations", **pagination_args),
            pagination_with_args=bool(pagination_args),
        )


class BoostyOperationDetailView(BoostyAdminView):
    def get(self, operation_id):
        operation = BoostyOperation.query.get_or_404(operation_id)
        forum_user = User.query.get(operation.forum_user_id) if operation.forum_user_id else None
        discord_actions = BoostyDiscordAction.query.filter_by(operation_id=operation.id).order_by(BoostyDiscordAction.created_at.desc()).all()
        deliveries = BoostyWebhookDelivery.query.filter_by(operation_id=operation.id).order_by(BoostyWebhookDelivery.created_at.desc()).all()
        corrections = BoostyCorrection.query.filter_by(operation_id=operation.id).order_by(BoostyCorrection.created_at.desc()).all()
        return render_template(
            "features/donations/hub/boosty/operation_detail.html",
            **self.template_args(
                operation=operation,
                forum_user=forum_user,
                discord_actions=discord_actions,
                deliveries=deliveries,
                corrections=corrections,
                ignore_form=IgnoreOperationForm(),
                correction_form=CorrectionForm(),
            ),
        )


class BoostySettingsView(BoostyAdminView):
    _keys = {
        "integration_enabled": "boosty_integration_enabled",
        "polling_interval": "boosty_polling_interval",
        "automatic_opyx_enabled": "boosty_automatic_opyx_enabled",
        "opyx_rate": "boosty_opyx_rate",
        "rounding": "boosty_rounding",
        "minimum_donation": "boosty_minimum_donation",
        "maximum_opyx_enabled": "boosty_maximum_opyx_enabled",
        "maximum_opyx": "boosty_maximum_opyx",
        "bonus_enabled": "boosty_bonus_enabled",
        "bonus_rules": "boosty_bonus_rules",
        "automatic_linking_enabled": "boosty_automatic_linking_enabled",
        "link_token_ttl_minutes": "boosty_link_token_ttl_minutes",
        "discord_sync_enabled": "boosty_discord_sync_enabled",
        "discord_guild_id": "boosty_discord_guild_id",
        "donator_role_id": "boosty_donator_role_id",
        "donator_role_mode": "boosty_donator_role_mode",
        "outgoing_webhooks_enabled": "boosty_outgoing_webhooks_enabled",
        "message_token": "boosty_message_token",
        "message_link_success": "boosty_message_link_success",
        "message_link_error": "boosty_message_link_error",
        "message_expired_token": "boosty_message_expired_token",
        "message_opyx_credited": "boosty_message_opyx_credited",
        "message_processing_error": "boosty_message_processing_error",
        "message_link_required": "boosty_message_link_required",
    }

    def _form(self):
        settings = get_settings()
        data = {field: settings.get(key, DEFAULT_SETTINGS.get(key)) for field, key in self._keys.items()}

        for field in ("polling_interval", "link_token_ttl_minutes"):
            key = self._keys[field]
            try:
                data[field] = int(data[field])
            except (TypeError, ValueError):
                data[field] = int(DEFAULT_SETTINGS[key])

        for field in ("opyx_rate", "minimum_donation", "maximum_opyx"):
            key = self._keys[field]
            try:
                data[field] = Decimal(str(data[field]))
            except (InvalidOperation, TypeError, ValueError):
                data[field] = Decimal(str(DEFAULT_SETTINGS[key]))

        return BoostySettingsForm(data=data)

    def get(self):
        guilds = [(str(guild.id), guild.name) for guild in getattr(discordClient, "guilds", [])]
        roles = DiscordRole.query.order_by(DiscordRole.title.asc()).all()
        return render_template("features/donations/hub/boosty/settings.html", **self.template_args(form=self._form(), guilds=guilds, roles=roles))

    def post(self):
        form = BoostySettingsForm()
        old_settings = get_settings()
        if form.validate_on_submit():
            plugin = PluginRegistry.query.filter_by(name="hub").first_or_404()
            values = {}
            for field, key in self._keys.items():
                value = getattr(form, field).data
                if isinstance(value, Decimal):
                    value = str(value)
                values[key] = value
            missing = {key: PLUGIN_SETTINGS[key] for key in values if key not in plugin.values}
            if missing:
                plugin.add_settings(missing)
            plugin.update_settings(values)
            event = None
            if old_settings.get("boosty_integration_enabled") != values["boosty_integration_enabled"]:
                event = "boosty.integration.enabled" if values["boosty_integration_enabled"] else "boosty.integration.disabled"
            if event:
                try:
                    from .webhooks import queue_event
                    queue_event(event, {"administratorId": current_user.id}, force=False)
                    db_hub.session.commit()
                except Exception:
                    db_hub.session.rollback()
                    current_app.logger.exception("Failed to queue Boosty integration state webhook")
            discord_keys = (
                "boosty_discord_sync_enabled",
                "boosty_discord_guild_id",
                "boosty_donator_role_id",
                "boosty_donator_role_mode",
            )
            if any(old_settings.get(key) != values.get(key) for key in discord_keys):
                old_guild_id = str(old_settings.get("boosty_discord_guild_id") or "")
                new_guild_id = str(values.get("boosty_discord_guild_id") or "")
                old_donator_role_id = str(old_settings.get("boosty_donator_role_id") or "")
                new_donator_role_id = str(values.get("boosty_donator_role_id") or "")
                if values.get("boosty_discord_sync_enabled") and old_guild_id:
                    roles_to_remove = set()
                    if old_guild_id != new_guild_id:
                        roles_to_remove.update(
                            item[0] for item in
                            BoostyDiscordRoleMapping.query.with_entities(BoostyDiscordRoleMapping.role_id)
                            .filter_by(guild_id=old_guild_id)
                            .all()
                        )
                    if old_donator_role_id and (
                        old_guild_id != new_guild_id or old_donator_role_id != new_donator_role_id
                    ):
                        roles_to_remove.add(old_donator_role_id)
                    if roles_to_remove:
                        account_ids = [
                            item[0] for item in
                            BoostyAccount.query.with_entities(BoostyAccount.id)
                            .join(BoostyAccountLink)
                            .all()
                        ]
                        for account_id in account_ids:
                            for role_id in roles_to_remove:
                                try:
                                    queue_role_removal(account_id, old_guild_id, role_id)
                                except Exception:
                                    current_app.logger.exception(
                                        "Failed to queue old Boosty Discord role removal for account %s",
                                        account_id,
                                    )
                _queue_linked_account_role_sync()
            audit_admin_action(current_user, "Boosty settings updated")
            flash("Boosty settings saved", "success")
            return redirect(url_for("hub.boosty_settings"))
        guilds = [(str(guild.id), guild.name) for guild in getattr(discordClient, "guilds", [])]
        roles = DiscordRole.query.order_by(DiscordRole.title.asc()).all()
        return render_template("features/donations/hub/boosty/settings.html", **self.template_args(form=form, guilds=guilds, roles=roles))


class BoostyLinksView(BoostyAdminView):
    def get(self):
        page = request.args.get("page", 1, type=int)
        pending_only = request.args.get("pending") == "1"
        query = BoostyAccount.query.outerjoin(BoostyAccountLink)
        if pending_only:
            query = query.filter(BoostyAccountLink.id.is_(None))
        pagination = query.order_by(BoostyAccount.last_seen_at.desc()).paginate(page, 30, False)
        user_ids = {account.link.forum_user_id for account in pagination.items if account.link}
        users = {user.id: user for user in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
        pagination_args = request.args.to_dict()
        pagination_args.pop("page", None)
        return render_template(
            "features/donations/hub/boosty/links.html",
            **self.template_args(accounts=pagination.items, pagination=pagination, users=users, form=ManualLinkForm()),
            pagination_url=url_for("hub.boosty_links", **pagination_args),
            pagination_with_args=bool(pagination_args),
        )


class BoostyDiscordView(BoostyAdminView):
    def get(self):
        mappings = BoostyDiscordRoleMapping.query.order_by(BoostyDiscordRoleMapping.tier_name.asc()).all()
        errors = BoostyDiscordAction.query.filter_by(status="Failed").order_by(BoostyDiscordAction.created_at.desc()).limit(100).all()
        roles = DiscordRole.query.order_by(DiscordRole.title.asc()).all()
        tiers = (
            BoostyAccount.query.with_entities(BoostyAccount.tier_id, BoostyAccount.tier_name)
            .filter(BoostyAccount.tier_id.isnot(None)).distinct().all()
        )
        form = DiscordRoleMappingForm(data={"guild_id": get_settings().get("boosty_discord_guild_id"), "enabled": True})
        return render_template("features/donations/hub/boosty/discord.html", **self.template_args(mappings=mappings, errors=errors, form=form, roles=roles, tiers=tiers))


class BoostyWebhooksView(BoostyAdminView):
    def get(self):
        endpoints = BoostyWebhookEndpoint.query.filter_by(deleted_at=None).order_by(BoostyWebhookEndpoint.name.asc()).all()
        deliveries = BoostyWebhookDelivery.query.order_by(BoostyWebhookDelivery.created_at.desc()).limit(100).all()
        return render_template(
            "features/donations/hub/boosty/webhooks.html",
            **self.template_args(endpoints=endpoints, deliveries=deliveries, form=WebhookEndpointForm(data={
                "enabled": True,
                "timeout_seconds": int(current_app.config.get("BOOSTY_WEBHOOK_DEFAULT_TIMEOUT_SECONDS", 10)),
                "retry_count": int(current_app.config.get("BOOSTY_WEBHOOK_DEFAULT_RETRY_COUNT", 5)),
            })),
        )


class BoostyIssuesView(BoostyAdminView):
    def get(self):
        issues = BoostyReconciliationIssue.query.order_by(BoostyReconciliationIssue.status.asc(), BoostyReconciliationIssue.severity.desc(), BoostyReconciliationIssue.last_seen_at.desc()).all()
        return render_template("features/donations/hub/boosty/issues.html", **self.template_args(issues=issues))


class BoostyLinkProfileView(MethodView):
    decorators = [login_required]

    def get(self):
        links = BoostyAccountLink.query.filter_by(forum_user_id=current_user.id).all()
        return render_template(
            "features/donations/boosty_link.html",
            form=BoostyLinkTokenForm(),
            request_form=BoostyLinkTokenRequestForm(),
            link_url=public_link_url(),
            links=links,
            actions=self._actions(),
        )

    def post(self):
        form = BoostyLinkTokenForm()
        request_form = BoostyLinkTokenRequestForm()
        action = request.form.get("action", "link")
        if action == "request_token" and request_form.validate_on_submit():
            try:
                result = request_new_link_token(request_form.email.data)
                if result == "failed":
                    flash("Не удалось отправить код через Boosty. Попробуйте повторить запрос позже.", "danger")
                elif result == "unavailable":
                    flash("Интеграция Boosty сейчас отключена. Попробуйте позже.", "warning")
                else:
                    flash(
                        "Если несвязанный Boosty-аккаунт с указанной почтой найден, "
                        "новый код отправлен в личные сообщения Boosty. Если запрос уже выполнялся недавно, "
                        "используйте код из последнего сообщения.",
                        "success",
                    )
                return redirect(url_for("donations.boosty_link"))
            except Exception:
                db_hub.session.rollback()
                current_app.logger.exception("Failed to request a replacement Boosty link token")
                flash("Не удалось запросить новый код. Попробуйте позже.", "danger")
        elif action == "link" and form.validate_on_submit():
            try:
                link, processed = redeem_link_token(form.token.data, current_user._get_current_object())
                flash(
                    "Boosty-аккаунт успешно привязан. Обработано ожидающих операций: {}.".format(processed),
                    "success",
                )
                return redirect(url_for("donations.boosty_link"))
            except ValueError as exc:
                db_hub.session.rollback()
                settings = get_settings()
                template = (
                    settings.get("boosty_message_expired_token")
                    if "expired" in str(exc).lower()
                    else settings.get("boosty_message_link_error")
                )
                from .service import format_message
                flash(format_message(
                    template,
                    user=current_user.display_name,
                    token="",
                    amount="",
                    opix="",
                    boostyName="",
                    expiresAt="",
                ), "danger")
        links = BoostyAccountLink.query.filter_by(forum_user_id=current_user.id).all()
        return render_template(
            "features/donations/boosty_link.html",
            form=form,
            request_form=request_form,
            link_url=public_link_url(),
            links=links,
            actions=self._actions(),
        )

    @staticmethod
    def _actions():
        return [
            NavigationLink(endpoint="donations.info", name=_("✨ Донат")),
            NavigationLink(endpoint="donations.points_transactions", name=_("🔆 Транзакции Опиксов")),
            NavigationLink(endpoint="donations.boosty_link", name=_("🔗 Привязать Boosty")),
        ]


class BoostyDashboardApiView(BoostyAdminView):
    def get(self):
        data = dashboard(request.args.get("period", "month"))
        return jsonify({
            "health": data["health"],
            "metrics": {key: str(value) if isinstance(value, Decimal) else value for key, value in data["current"].items()},
            "changePercent": str(data["changePercent"]) if data["changePercent"] is not None else None,
            "chart": data["chart"],
            "subscriptionChart": data["subscriptionChart"],
        })


class BoostyOperationsApiView(BoostyAdminView):
    def get(self):
        page = request.args.get("page", 1, type=int)
        pagination = _operation_query().paginate(page, 30, False)
        return jsonify({"items": [operation_data(item) for item in pagination.items], "page": page, "pages": pagination.pages, "total": pagination.total})


def sync_now():
    try:
        result = synchronize(force=True)
        flash("Boosty synchronization: received {received}, processed {processed}".format(**result), "success" if not result.get("skipped") else "warning")
    except Exception as exc:
        flash("Boosty synchronization failed: {}".format(exc), "danger")
    audit_admin_action(current_user, "Manual Boosty synchronization requested")
    return redirect(request.referrer or url_for("hub.boosty_dashboard"))


def retry_operation(operation_id):
    operation = BoostyOperation.query.get_or_404(operation_id)
    if operation.status == "Processed":
        flash("Operation is already processed; no Opyx were credited again", "warning")
    else:
        result = process_operation(operation.id, force=True)
        audit_admin_action(current_user, "Boosty operation {} retried; status {}".format(operation.external_id, result.status))
        flash("Operation status: {}".format(result.status), "success" if result.status == "Processed" else "warning")
    return redirect(url_for("hub.boosty_operation", operation_id=operation.id))


def ignore_operation(operation_id):
    operation = BoostyOperation.query.get_or_404(operation_id)
    form = IgnoreOperationForm()
    if form.validate_on_submit():
        try:
            mark_ignored(operation, form.reason.data, current_user)
            flash("Operation marked as ignored", "success")
        except ValueError as exc:
            db_hub.session.rollback()
            flash(str(exc), "danger")
    else:
        flash(_validation_message(form), "danger")
    return redirect(url_for("hub.boosty_operation", operation_id=operation.id))


def operation_preview(operation_id):
    operation = BoostyOperation.query.get_or_404(operation_id)
    value = preview_operation(operation)
    return jsonify({
        "eligible": value.eligible,
        "reason": value.reason,
        "amount": str(value.amount),
        "baseRate": str(value.base_rate),
        "bonusPercent": str(value.bonus_percent),
        "finalRate": str(value.final_rate),
        "opyx": str(value.opyx),
    })


def correct_operation(operation_id):
    operation = BoostyOperation.query.get_or_404(operation_id)
    form = CorrectionForm()
    if form.validate_on_submit():
        try:
            add_manual_correction(operation, form.amount.data, form.reason.data, current_user)
            flash("Separate Opyx correction transaction created", "success")
        except ValueError as exc:
            db_hub.session.rollback()
            flash(str(exc), "danger")
    else:
        flash(_validation_message(form), "danger")
    return redirect(url_for("hub.boosty_operation", operation_id=operation.id))


def link_account_manually():
    form = ManualLinkForm()
    if form.validate_on_submit():
        account = BoostyAccount.query.get_or_404(form.boosty_account_id.data)
        user = User.query.get_or_404(form.forum_user_id.data)
        try:
            link, processed = manual_link(account, user, current_user)
            flash("Account linked; pending donations processed: {}".format(processed), "success")
        except ValueError as exc:
            db_hub.session.rollback()
            flash(str(exc), "danger")
    else:
        flash(_validation_message(form), "danger")
    return redirect(url_for("hub.boosty_links"))


def unlink_account_admin(account_id):
    account = BoostyAccount.query.get_or_404(account_id)
    unlink_account(account, current_user)
    flash("Boosty account unlinked; processed operations were not changed", "success")
    return redirect(url_for("hub.boosty_links"))


def save_role_mapping(mapping_id=None):
    mapping = BoostyDiscordRoleMapping.query.get_or_404(mapping_id) if mapping_id else BoostyDiscordRoleMapping()
    old_guild_id = mapping.guild_id if mapping_id else None
    old_role_id = mapping.role_id if mapping_id else None
    form = DiscordRoleMappingForm()
    if form.validate_on_submit():
        configured_guild_id = str(get_settings().get("boosty_discord_guild_id") or "")
        if configured_guild_id and form.guild_id.data != configured_guild_id:
            flash("Mapping guild must match the guild selected in Boosty settings", "danger")
            return redirect(url_for("hub.boosty_discord"))
        mapping.guild_id = form.guild_id.data
        mapping.tier_id = form.tier_id.data
        mapping.tier_name = form.tier_name.data
        mapping.role_id = form.role_id.data
        mapping.enabled = form.enabled.data
        db_hub.session.add(mapping)
        try:
            db_hub.session.commit()
        except IntegrityError:
            db_hub.session.rollback()
            flash("A mapping for this guild and Boosty tier already exists", "danger")
            return redirect(url_for("hub.boosty_discord"))
        if old_role_id and (old_guild_id != mapping.guild_id or old_role_id != mapping.role_id):
            old_role_still_managed = BoostyDiscordRoleMapping.query.filter_by(
                guild_id=old_guild_id,
                role_id=old_role_id,
            ).count() > 0
            if get_settings().get("boosty_discord_sync_enabled") and not old_role_still_managed:
                for account in BoostyAccount.query.join(BoostyAccountLink).all():
                    try:
                        queue_role_removal(account.id, old_guild_id, old_role_id)
                    except Exception:
                        current_app.logger.exception(
                            "Failed to queue old Boosty Discord mapping role removal for account %s",
                            account.id,
                        )
        _queue_linked_account_role_sync()
        audit_admin_action(current_user, "Boosty Discord role mapping {} saved".format(mapping.id))
        flash("Discord role mapping saved", "success")
    else:
        flash(_validation_message(form), "danger")
    return redirect(url_for("hub.boosty_discord"))


def delete_role_mapping(mapping_id):
    mapping = BoostyDiscordRoleMapping.query.get_or_404(mapping_id)
    account_ids = [
        account.id for account in
        BoostyAccount.query.join(BoostyAccountLink).all()
    ]
    guild_id = mapping.guild_id
    role_id = mapping.role_id
    db_hub.session.delete(mapping)
    db_hub.session.commit()
    same_role_is_managed = BoostyDiscordRoleMapping.query.filter_by(guild_id=guild_id, role_id=role_id).count() > 0
    if get_settings().get("boosty_discord_sync_enabled") and not same_role_is_managed:
        for account_id in account_ids:
            try:
                queue_role_removal(account_id, guild_id, role_id)
            except Exception:
                current_app.logger.exception(
                    "Failed to queue deleted Boosty Discord mapping role removal for account %s",
                    account_id,
                )
    _queue_linked_account_role_sync()
    audit_admin_action(current_user, "Boosty Discord role mapping {} deleted".format(mapping_id))
    flash("Discord role mapping deleted", "success")
    return redirect(url_for("hub.boosty_discord"))


def retry_discord(action_id):
    action = BoostyDiscordAction.query.get_or_404(action_id)
    retry_discord_action(action)
    audit_admin_action(current_user, "Boosty Discord action {} retried".format(action_id))
    flash("Discord synchronization queued", "success")
    return redirect(url_for("hub.boosty_discord"))


def save_webhook(endpoint_id=None):
    endpoint = BoostyWebhookEndpoint.query.get_or_404(endpoint_id) if endpoint_id else BoostyWebhookEndpoint()
    if endpoint.deleted_at is not None:
        abort(404)
    form = WebhookEndpointForm()
    if form.validate_on_submit():
        if not endpoint_id and not form.secret.data:
            flash("Secret is required for a new webhook endpoint", "danger")
            return redirect(url_for("hub.boosty_webhooks"))
        endpoint.name = form.name.data
        endpoint.url = form.url.data
        endpoint.enabled = form.enabled.data
        endpoint.events = form.events.data
        endpoint.timeout_seconds = form.timeout_seconds.data
        endpoint.retry_count = form.retry_count.data
        if form.secret.data:
            endpoint.secret = form.secret.data
        db_hub.session.add(endpoint)
        db_hub.session.commit()
        audit_admin_action(current_user, "Boosty webhook endpoint {} saved".format(endpoint.id))
        flash("Webhook endpoint saved; its secret will no longer be displayed", "success")
    else:
        flash(_validation_message(form), "danger")
    return redirect(url_for("hub.boosty_webhooks"))


def delete_webhook(endpoint_id):
    endpoint = BoostyWebhookEndpoint.query.get_or_404(endpoint_id)
    endpoint.enabled = False
    endpoint.deleted_at = time_utcnow()
    db_hub.session.commit()
    audit_admin_action(current_user, "Boosty webhook endpoint {} deleted".format(endpoint_id))
    flash("Webhook endpoint archived; delivery history was preserved", "success")
    return redirect(url_for("hub.boosty_webhooks"))


def test_webhook(endpoint_id):
    endpoint = BoostyWebhookEndpoint.query.get_or_404(endpoint_id)
    queue_test(endpoint)
    db_hub.session.commit()
    audit_admin_action(current_user, "Boosty webhook endpoint {} test queued".format(endpoint_id))
    flash("Test webhook queued", "success")
    return redirect(url_for("hub.boosty_webhooks"))


def retry_webhook(delivery_id):
    delivery = BoostyWebhookDelivery.query.get_or_404(delivery_id)
    retry_delivery(delivery)
    db_hub.session.commit()
    audit_admin_action(current_user, "Boosty webhook delivery {} retried".format(delivery_id))
    flash("Webhook delivery queued for retry", "success")
    return redirect(url_for("hub.boosty_webhooks"))


def run_reconciliation():
    try:
        count = reconcile()
        audit_admin_action(current_user, "Manual Boosty reconciliation run; {} issues".format(count))
        flash("Reconciliation completed: {} open issues".format(count), "success")
    except Exception as exc:
        from .reconciliation import report_reconciliation_failure
        report_reconciliation_failure(exc)
        flash("Reconciliation failed: {}".format(exc), "danger")
    return redirect(url_for("hub.boosty_issues"))
