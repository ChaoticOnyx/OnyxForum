from flask import Blueprint
from flaskbb.utils.helpers import register_view

from .views import *
from .features.donations.hub.views import *
from .features.karma.views import *

hub = Blueprint("hub", __name__, template_folder="templates")

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
