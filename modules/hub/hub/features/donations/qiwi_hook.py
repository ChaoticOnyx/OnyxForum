import datetime
import requests
import traceback
import string
from datetime import datetime

from flask import Response, request, url_for
from flask.views import MethodView

from hub.models import Player
from hub.utils import get_player_by_ckey
from hub.features.donations.hub.notifications import notify_user_donation_registration_error
from . import actions


def parse_datetime(qiwi_format: str) -> datetime:
    return datetime.fromisoformat(qiwi_format)


class QiwiHook(MethodView):
    def post(self):
        content = request.get_json()

        print("[QIWI Webhooks] Received:")
        print("-- Content: " + str(content))

        if content['payment']['type'] != 'IN' or content['payment']['status'] != 'SUCCESS':
            print("-- Skip hook: Not suitable hook")
            return Response(status=200)

        if content['payment']['sum']['currency'] != 643:  # ruble
            print("-- Skip hook: Unknown currency")
            return Response(status=200)

        dt = parse_datetime(content['payment']['date'])
        amount = content['payment']['sum']['amount']
        ckey = content['payment']['comment'].split(' ')[0].lower().strip(string.punctuation)

        player: Player = get_player_by_ckey(ckey) if ckey else None
        if player is None:
            ckey = "".join(filter(str.isalpha, content['payment']['comment'].lower()))
            player: Player = get_player_by_ckey(ckey) if ckey else None

        print("-- New donation from " + ckey + ". Amount: " + str(amount) + ". Datetime: " + dt.isoformat())

        if player is None:
            notify_user_donation_registration_error(dt, amount, content['payment']['comment'])
            print("-- Failed to process donation automatically (comment: \"{}\")".format(content['payment']['comment']))
        else:
            actions.add_donation_and_notify(dt, ckey, float(amount), type="qiwi", registered_by=None)

        return Response(status=200)


def register_qiwi_webhook(token):
    params = {
        "hookType": 1,
        "param": url_for("donations.qiwi_hook", _external=True),
        "txnType": 0
    }
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json"
    }
    res = requests.put("https://edge.qiwi.com/payment-notifier/v1/hooks", params=params, headers=headers)
    print("[QIWI Webhooks] registration")
    print("-- Request: " + str(res.request.__dict__))
    print("-- Res: " + str(res.__dict__))

    if not res.ok:
        print("[QIWI Webhooks] Failed to register webhook")
        return

    print("[QIWI Webhooks] Webhook is successfuly registered")

def get_qiwi_webhook_id(token):
    params = { }
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json"
    }
    res: requests.Response = requests.get("https://edge.qiwi.com/payment-notifier/v1/hooks/active", params=params, headers=headers)

    print("[QIWI Webhook] Get webhook")
    print("-- Request: " + str(res.request.__dict__))
    print("-- Res: " + str(res.__dict__))

    if not res.ok:
        print("[QIWI Webhooks] Webhook isn't registered")
        return None

    return res.json()["hookId"]

def delete_qiwi_webhook(token):
    hookId = get_qiwi_webhook_id(token)
    if not hookId:
        return

    params = { }
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json"
    }
    res: requests.Response = requests.delete("https://edge.qiwi.com/payment-notifier/v1/hooks/{}".format(hookId), params=params, headers=headers)

    print("[QIWI Webhook] Delete webhook")
    print("-- Request: " + str(res.request.__dict__))
    print("-- Res: " + str(res.__dict__))

    if not res.ok:
        print("[QIWI Webhooks] Failed to delete webhook")
        return

    print("[QIWI Webhooks] Webhook is deleted successfuly")

def register_webhooks_service(app):
    try:
        if "QIWI_TOKEN" not in app.config:
            print("Error: QIWI_TOKEN isn't specified")
            return
        if not app.config["QIWI_HOOKS"]:
            print("QIWI Webhooks registration skipped")
            return

        token = app.config["QIWI_TOKEN"]
        delete_qiwi_webhook(token)
        register_qiwi_webhook(token)
    except Exception:
        print("Error: Exception is caught during QIWI hook registration:")
        traceback.print_exc()
