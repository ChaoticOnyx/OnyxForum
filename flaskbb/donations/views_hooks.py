import requests

from flask import Flask, Blueprint, Response, request, url_for
from flask.views import MethodView
from flaskbb.utils.helpers import register_view
from pluggy import HookimplMarker

impl = HookimplMarker("flaskbb")


class QiwiHook(MethodView):
    def get(self):
        print("----")
        print("Qiwi hook:")
        print(request.__dict__)
        print("----")

        return Response(status=200)


def register_webhooks_service(app):
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

    args = {
        "hookType": 1,
        "param": url_for("donations.qiwi_hook"),
        "txnType": 0
    }
    headers = {
        "Authorization": "Bearer " + app.config["QIWI_TOKEN"],
        "Accept": "application/json"
    }
    res = requests.post("https://edge.qiwi.com/payment-notifier/v1/hooks", headers=headers, json=args)
    print("QIWI Webhooks registration result: \n" + str(res.__dict__))


@impl(tryfirst=True)
def flaskbb_load_blueprints(app: Flask):
    donations = Blueprint("donations", __name__)

    register_view(
        donations,
        routes=['/qiwi_hook'],
        view_func=QiwiHook.as_view('qiwi_hook')
    )

    app.register_blueprint(donations)
    app.before_first_request(lambda: register_webhooks_service(app))
