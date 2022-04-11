from datetime import datetime
from dataclasses import dataclass
from typing import List
import string

from flask import request, url_for, redirect
from flask.views import MethodView

from flask_babelplus import gettext as _
from flask_login import current_user, login_required
from flask_sqlalchemy import Pagination

from flaskbb.display.navigation import NavigationLink
from flaskbb.utils.helpers import render_template

from hub.utils import configs_path
from hub.models import Player, PointsTransaction, MoneyTransaction, DonationType

class UserDonationsView(MethodView):
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
                name=_("💵 Donations History"),
            ))

        return actions

    def get_args(self):
        return {
            "actions": self.__get_actions()
        }

    def get(self):
        return redirect(url_for("donations.info"))


class DonationsInfoView(UserDonationsView):
    decorators = [login_required]

    def get(self):
        content = ""
        with open(configs_path + "/donations_info.html", "r") as content_html:
            content = content_html.read()
        return render_template("features/donations/info.html", **self.get_args(), content=content)


class UserPointsTransactionsView(UserDonationsView):
    decorators = [login_required]

    def get(self):
        page = request.args.get('page', 1, type=int)

        query = PointsTransaction.query\
            .join(Player)\
            .filter(Player.discord_user_id == current_user.discord)\
            .order_by(PointsTransaction.datetime.desc())
        pagination: Pagination = query.paginate(page, 20)
        transactions = pagination.items

        @dataclass
        class TransactionData:
            datetime: datetime
            change: string
            comment: string

        data = []
        for transaction in transactions:
            data.append(TransactionData(
                datetime=transaction.datetime,
                change="{:+2}".format(transaction.change).rstrip('0').rstrip('.') + " 🔆",
                comment=transaction.comment
            ))

        return render_template(
            "features/donations/points_transactions.html",
            **self.get_args(),
            transactions=data,
            pagination=pagination)


class UserMoneyTransactionsView(UserDonationsView):
    decorators = [login_required]

    def get(self):
        page = request.args.get('page', 1, type=int)

        query = MoneyTransaction.query\
            .join(Player)\
            .join(DonationType)\
            .filter(Player.discord_user_id == current_user.discord)\
            .order_by(MoneyTransaction.datetime.desc())
        pagination: Pagination = query.paginate(page, 20)
        transactions: List[MoneyTransaction] = pagination.items

        @dataclass
        class TransactionData:
            datetime: datetime
            change: string
            comment: string

        data = []
        for transaction in transactions:
            type_str = transaction.donation_type.type
            if type_str == "qiwi":
                type_str = "Пожертвование через QIWI"
            elif type_str == "patreon":
                type_str = "Подписка Patreon"

            data.append(TransactionData(
                datetime=transaction.datetime,
                change="{:+2}".format(transaction.change).rstrip('0').rstrip('.') + " ₽",
                comment=type_str
            ))

        return render_template(
            "features/donations/money_transactions.html",
            **self.get_args(),
            transactions=data,
            pagination=pagination)
