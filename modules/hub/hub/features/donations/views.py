from datetime import datetime
import string
import requests

from flask import Blueprint, Response, request, url_for
from flask.views import MethodView

from flask_babelplus import gettext as _

from flaskbb.display.navigation import NavigationLink
from flaskbb.utils.helpers import register_view, render_template

donations = Blueprint("donations", __name__, template_folder="templates")


class DonationsView(MethodView):
    def __get_actions(self):
        actions = []

        actions.append(
            NavigationLink(
                endpoint="donations.info",
                name=_("✨ Donate"),
            ))

        actions.append(
            NavigationLink(
                endpoint="donations.points_transactions",
                name=_("🔆 Opyxes Transactions"),
            ))

        actions.append(
            NavigationLink(
                endpoint="donations.money_transactions",
                name=_("💵 Money Transactions"),
            ))

        return actions

    def get_args(self):
        return {
            "actions": self.__get_actions()
        }

    def get(self):
        return render_template("features/donations/index.html", **self.get_args())


class InfoView(DonationsView):
    def get(self):
        return render_template("features/donations/info.html", **self.get_args())


class PointsTransactionsView(DonationsView):
    def get(self):
        return render_template("features/donations/points_transactions.html", **self.get_args())


class MoneyTransactionsView(DonationsView):
    def get(self):
        return render_template("features/donations/money_transactions.html", **self.get_args())


def parse_datetime(qiwi_format: str) -> datetime:
    return datetime.fromisoformat(qiwi_format)


class QiwiHook(MethodView):
    def post(self):
        content = request.get_json()

        print("----")
        print("Qiwi hook:")
        print("Request: " + str(request.__dict__))
        print("Json: " + str(content))
        print("----")

        if content['payment']['type'] != 'IN' or content['payment']['status'] != 'SUCCESS':
            print("Skip hook: Not suitable hook")
            return Response(status=200)

        if content['payment']['sum']['currency'] != 643:  # ruble
            print("Skip hook: Unknown currency")
            return Response(status=200)

        dt = parse_datetime(content['payment']['date'])
        ckey = content['payment']['comment'].split(' ')[0].lower().strip(string.punctuation)
        amount = content['payment']['sum']['amount']

        print("New donation from " + ckey + ". Amount: " + str(amount) + ". Datetime: " + dt.isoformat())
        return Response(status=200)


def register_webhooks_service(app):
    if "QIWI_TOKEN" not in app.config:
        print("Error: QIWI_TOKEN isn't specified")
        return

    headers = {
        "Authorization": "Bearer " + app.config["QIWI_TOKEN"],
        "Accept": "application/json"
    }

    res = requests.get("https://edge.qiwi.com/person-profile/v1/profile/current", headers=headers)
    print("QIWI Test:")
    print(res.__dict__)

    if not app.config["QIWI_HOOKS"]:
        print("QIWI Webhooks registration skipped")
        return

    params = {
        "hookType": 1,
        "param": url_for("donations.qiwi_hook", _external=True),
        "txnType": 0
    }
    headers = {
        "Authorization": "Bearer " + app.config["QIWI_TOKEN"],
        "Accept": "application/json"
    }
    res = requests.put("https://edge.qiwi.com/payment-notifier/v1/hooks", params=params, headers=headers)
    print("QIWI Webhooks registration result:")
    print("Request: " + str(res.request.__dict__))
    print("Res: " + str(res.__dict__))


register_view(
    donations,
    routes=["/"],
    view_func=DonationsView.as_view("index"),
)

register_view(
    donations,
    routes=["/info"],
    view_func=InfoView.as_view("info")
)

register_view(
    donations,
    routes=["/points_transactions"],
    view_func=PointsTransactionsView.as_view("points_transactions")
)

register_view(
    donations,
    routes=["/money_transactions"],
    view_func=MoneyTransactionsView.as_view("money_transactions")
)

register_view(
    donations,
    routes=['/qiwi_hook'],
    view_func=QiwiHook.as_view('qiwi_hook')
)
