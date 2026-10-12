from flask import Blueprint
from flaskbb.utils.helpers import register_view

from .views import *
from .features.donations.hub.views import *
from .features.donations.boosty.views import (
    BoostyDashboardApiView, BoostyDashboardView, BoostyDiscordView,
    BoostyIssuesView, BoostyLinksView, BoostyOperationDetailView,
    BoostyOperationsApiView, BoostyOperationsView, BoostySettingsView,
    BoostyStatisticsView, BoostyWebhooksView, admin_required,
    correct_operation, delete_role_mapping, delete_webhook, ignore_operation,
    link_account_manually, operation_preview, retry_discord,
    retry_operation, retry_webhook, run_reconciliation, save_role_mapping,
    save_webhook, sync_now, test_webhook, unlink_account_admin,
)
from .features.karma.views import *

hub = Blueprint(
    "hub",
    __name__,
    template_folder="templates",
    static_folder="static",
)

register_view(
    hub,
    routes=["/"],
    view_func=Hub.as_view("index"),
)

register_view(
    hub,
    routes=["/control"],
    view_func=ControlView.as_view("control")
)

register_view(
    hub,
    routes=["/control/logs"],
    view_func=ControlLogsView.as_view("control_logs")
)

register_view(
    hub,
    routes=["/start"],
    view_func=StartServer.as_view("start"),
)

register_view(
    hub,
    routes=["/stop"],
    view_func=StopServer.as_view("stop"),
)

register_view(
    hub,
    routes=["/restart"],
    view_func=RestartServer.as_view("restart"),
)

register_view(
    hub,
    routes=["/update"],
    view_func=UpdateServer.as_view("update")
)

register_view(
    hub,
    routes=["/configs"],
    view_func=ConfigsView.as_view("configs"),
)

register_view(
    hub,
    routes=["/config_edit"],
    view_func=ConfigEditView.as_view("config_edit"),
)

register_view(
    hub,
    routes=["/gamelogs"],
    view_func=LogsView.as_view("gamelogs")
)

register_view(
    hub,
    routes=["/download_gamelog"],
    view_func=LogDownload.as_view("download_gamelog")
)

register_view(
    hub,
    routes=["/team"],
    view_func=TeamView.as_view("team")
)

register_view(
    hub,
    routes=["/bans"],
    view_func=BansView.as_view("bans")
)

register_view(
    hub,
    routes=["/connections"],
    view_func=ConnectionsView.as_view("connections")
)

register_view(
    hub,
    routes=["/admins"],
    view_func=AdminsView.as_view("admins"),
)

register_view(
    hub,
    routes=["/admins/json"],
    view_func=AdminsView.as_view("admins_json"),
)

register_view(
    hub,
    routes=["/karma"],
    view_func=KarmaView.as_view("karma")
)

register_view(
    hub,
    routes=["/post_rate"],
    view_func=PostRateView.as_view("post_rate")
)

register_view(
    hub,
    routes=["/donations"],
    view_func=DonationsView.as_view("donations"),
)

register_view(
    hub,
    routes=["/donations/add_donation"],
    view_func=AddDonationView.as_view("add_donation"),
)

register_view(
    hub,
    routes=["/donations/money_transactions"],
    view_func=MoneyTransactionsView.as_view("money_transactions"),
)

register_view(
    hub,
    routes=["/donations/points_transactions"],
    view_func=PointsTransactionsView.as_view("points_transactions"),
)

register_view(
    hub,
    routes=["/donations/add_money_transaction"],
    view_func=AddMoneyTransactionView.as_view("add_money_transaction"),
)

register_view(
    hub,
    routes=["/donations/add_points_transaction"],
    view_func=AddPointsTransactionView.as_view("add_points_transaction"),
)

register_view(hub, routes=["/donations/boosty"], view_func=BoostyDashboardView.as_view("boosty_dashboard"))
register_view(hub, routes=["/donations/boosty/statistics"], view_func=BoostyStatisticsView.as_view("boosty_statistics"))
register_view(hub, routes=["/donations/boosty/operations"], view_func=BoostyOperationsView.as_view("boosty_operations"))
register_view(hub, routes=["/donations/boosty/operations/<int:operation_id>"], view_func=BoostyOperationDetailView.as_view("boosty_operation"))
register_view(hub, routes=["/donations/boosty/settings"], view_func=BoostySettingsView.as_view("boosty_settings"))
register_view(hub, routes=["/donations/boosty/links"], view_func=BoostyLinksView.as_view("boosty_links"))
register_view(hub, routes=["/donations/boosty/discord"], view_func=BoostyDiscordView.as_view("boosty_discord"))
register_view(hub, routes=["/donations/boosty/webhooks"], view_func=BoostyWebhooksView.as_view("boosty_webhooks"))
register_view(hub, routes=["/donations/boosty/issues"], view_func=BoostyIssuesView.as_view("boosty_issues"))
register_view(hub, routes=["/donations/boosty/api/dashboard"], view_func=BoostyDashboardApiView.as_view("boosty_api_dashboard"))
register_view(hub, routes=["/donations/boosty/api/operations"], view_func=BoostyOperationsApiView.as_view("boosty_api_operations"))

register_view(hub, routes=["/donations/boosty/sync"], view_func=admin_required(sync_now), endpoint="boosty_sync", methods=["POST"])
register_view(hub, routes=["/donations/boosty/operations/<int:operation_id>/retry"], view_func=admin_required(retry_operation), endpoint="boosty_operation_retry", methods=["POST"])
register_view(hub, routes=["/donations/boosty/operations/<int:operation_id>/ignore"], view_func=admin_required(ignore_operation), endpoint="boosty_operation_ignore", methods=["POST"])
register_view(hub, routes=["/donations/boosty/operations/<int:operation_id>/preview"], view_func=admin_required(operation_preview), endpoint="boosty_operation_preview", methods=["GET"])
register_view(hub, routes=["/donations/boosty/operations/<int:operation_id>/correction"], view_func=admin_required(correct_operation), endpoint="boosty_operation_correction", methods=["POST"])
register_view(hub, routes=["/donations/boosty/links/manual"], view_func=admin_required(link_account_manually), endpoint="boosty_link_manual", methods=["POST"])
register_view(hub, routes=["/donations/boosty/links/<int:account_id>/unlink"], view_func=admin_required(unlink_account_admin), endpoint="boosty_unlink", methods=["POST"])
register_view(hub, routes=["/donations/boosty/discord/mappings"], view_func=admin_required(save_role_mapping), endpoint="boosty_discord_mapping_add", methods=["POST"])
register_view(hub, routes=["/donations/boosty/discord/mappings/<int:mapping_id>"], view_func=admin_required(save_role_mapping), endpoint="boosty_discord_mapping_edit", methods=["POST"])
register_view(hub, routes=["/donations/boosty/discord/mappings/<int:mapping_id>/delete"], view_func=admin_required(delete_role_mapping), endpoint="boosty_discord_mapping_delete", methods=["POST"])
register_view(hub, routes=["/donations/boosty/discord/actions/<int:action_id>/retry"], view_func=admin_required(retry_discord), endpoint="boosty_discord_retry", methods=["POST"])
register_view(hub, routes=["/donations/boosty/webhooks"], view_func=admin_required(save_webhook), endpoint="boosty_webhook_add", methods=["POST"])
register_view(hub, routes=["/donations/boosty/webhooks/<int:endpoint_id>"], view_func=admin_required(save_webhook), endpoint="boosty_webhook_edit", methods=["POST"])
register_view(hub, routes=["/donations/boosty/webhooks/<int:endpoint_id>/delete"], view_func=admin_required(delete_webhook), endpoint="boosty_webhook_delete", methods=["POST"])
register_view(hub, routes=["/donations/boosty/webhooks/<int:endpoint_id>/test"], view_func=admin_required(test_webhook), endpoint="boosty_webhook_test", methods=["POST"])
register_view(hub, routes=["/donations/boosty/webhook-deliveries/<int:delivery_id>/retry"], view_func=admin_required(retry_webhook), endpoint="boosty_webhook_retry", methods=["POST"])
register_view(hub, routes=["/donations/boosty/reconcile"], view_func=admin_required(run_reconciliation), endpoint="boosty_reconcile", methods=["POST"])
