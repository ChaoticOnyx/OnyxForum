from flask import Blueprint
from flaskbb.utils.helpers import register_view
from .views import *
from .qiwi_hook import QiwiHook


donations = Blueprint("donations", __name__, template_folder="templates")

register_view(
    donations,
    routes=["/"],
    view_func=UserDonationsView.as_view("index"),
)

register_view(
    donations,
    routes=["/info"],
    view_func=DonationsInfoView.as_view("info")
)

register_view(
    donations,
    routes=["/points_transactions"],
    view_func=UserPointsTransactionsView.as_view("points_transactions")
)

register_view(
    donations,
    routes=["/money_transactions"],
    view_func=UserMoneyTransactionsView.as_view("money_transactions")
)

register_view(
    donations,
    routes=['/qiwi_hook'],
    view_func=QiwiHook.as_view('qiwi_hook')
)
