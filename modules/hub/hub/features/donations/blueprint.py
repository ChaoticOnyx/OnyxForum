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
    routes=["/patron"],
    view_func=PatronView.as_view("patron")
)

register_view(
    donations,
    routes=["/choose_tier"],
    view_func=PatronChooseTierView.as_view("choose_tier")
)

register_view(
    donations,
    routes=["/revoke_tier"],
    view_func=PatronRevokeTierView.as_view("revoke_tier")
)

register_view(
    donations,
    routes=['/qiwi_hook'],
    view_func=QiwiHook.as_view('qiwi_hook')
)

register_view(
    donations,
    routes=['/create_payment'],
    view_func=CreatePayment.as_view('create_payment')
)

register_view(
    donations,
    routes=['/payment'],
    view_func=PaymentView.as_view('payment')
)