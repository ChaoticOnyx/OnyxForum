from datetime import datetime
import logging
from dataclasses import dataclass
from typing import List

from flask import request, flash
from flask.views import MethodView
from flask_allows import Permission
from flask_babelplus import gettext as _
from flask_login import current_user
from flask_sqlalchemy import Pagination

from flaskbb.display.navigation import NavigationLink
from flaskbb.utils.requirements import IsAdmin
from flaskbb.utils.helpers import FlashAndRedirect
from flaskbb.extensions import allows
from hub.features.donations import discord_tasks, money, actions
from hub.models import PointsTransaction, MoneyTransaction
from hub.utils import get_player_by_discord
from .forms import AddDonationForm, AddMoneyTransactionForm, AddPointsTransactionForm
from .notifications import *

from flaskbb.utils.helpers import render_template

logger = logging.getLogger('donations')


class DonationsView(MethodView):
    def __get_actions(self):
        actions = []

        if Permission(IsAdmin):
            actions.append(
                NavigationLink(
                    endpoint="hub.add_donation",
                    name=_("Добавить Донат"),
                ))

            actions.append(
                NavigationLink(
                    endpoint="hub.money_transactions",
                    name=_("Денежные Транзакции"),
                ))

            actions.append(
                NavigationLink(
                    endpoint="hub.points_transactions",
                    name=_("Транзакции Опиксов"),
                ))

            actions.append(
                NavigationLink(
                    endpoint="hub.add_money_transaction",
                    name=_("Добавить Денежную Транзакцию"),
                ))

            actions.append(
                NavigationLink(
                    endpoint="hub.add_points_transaction",
                    name=_("Добавить Транзакцию Опиксов"),
                ))

        return actions

    def get_args(self):
        return {
            "actions": self.__get_actions()
        }

    def get(self):
        return render_template("features/donations/hub/index.html", **self.get_args())


class AddDonationView(DonationsView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access this page"),
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self):
        form = AddDonationForm()

        return render_template(
            "features/donations/hub/add_donation.html",
            **self.get_args(),
            form=form)

    def post(self):
        form = AddDonationForm()

        if form.validate_on_submit():
            player = get_player_by_discord(form.discord.data, create_if_not_exists=True)
            actions.add_donation_and_notify(form.datetime.data, player, form.amount.data, form.type.data, form.issue.data, current_user)
            flash("Donation is added", "success")

        return render_template(
            "features/donations/hub/add_donation.html",
            **self.get_args(),
            form=form)


class PointsTransactionsView(DonationsView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access this page"),
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self):
        page = request.args.get('page', 1, type=int)

        query = PointsTransaction.query\
            .order_by(PointsTransaction.datetime.desc())
        pagination: Pagination = query.paginate(page, 20)
        transactions: List[PointsTransaction] = pagination.items

        @dataclass
        class TransactionData:
            datetime: datetime
            player: str
            change: str
            comment: str

        data = []
        for transaction in transactions:
            player_str = ""
            if transaction.player:
                player_str = transaction.player.ckey or f"{transaction.player.discord_user.nickname} ({transaction.player.discord_user_id})"
            data.append(TransactionData(
                datetime=transaction.datetime,
                player=player_str,
                change="{:+2}".format(transaction.change).rstrip('0').rstrip('.') + " 🔆",
                comment=transaction.comment
            ))

        return render_template(
            "features/donations/hub/points_transactions.html",
            **self.get_args(),
            transactions=data,
            pagination=pagination)


class MoneyTransactionsView(DonationsView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access this page"),
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self):
        page = request.args.get('page', 1, type=int)

        query = MoneyTransaction.query\
            .order_by(MoneyTransaction.datetime.desc())
        pagination: Pagination = query.paginate(page, 20)
        transactions: List[MoneyTransaction] = pagination.items

        @dataclass
        class TransactionData:
            datetime: datetime
            change: str
            reason: str

        data = []
        for transaction in transactions:
            player_str = ""
            if transaction.player:
                player_str = transaction.player.ckey or f"{transaction.player.discord_user.nickname} ({transaction.player.discord_user_id})"
            data.append(TransactionData(
                datetime=transaction.datetime,
                change="{:+2}".format(transaction.change).rstrip('0').rstrip('.') + " ₽",
                reason=transaction.reason + f"({player_str})"
            ))

        return render_template(
            "features/donations/hub/money_transactions.html",
            **self.get_args(),
            transactions=data,
            pagination=pagination)


class AddMoneyTransactionView(DonationsView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access this page"),
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self):
        form = AddMoneyTransactionForm()

        return render_template(
            "features/donations/hub/add_money_transaction.html",
            **self.get_args(),
            form=form)

    def post(self):
        form = AddMoneyTransactionForm()

        if form.validate_on_submit():
            money_transaction = money.add_money_transaction(form.amount.data, form.reason.data, None)
            report_money_transaction(money.get_current_balance(), money_transaction)
            logger.info(
                "[AddMoneyTransaction] "
                "registered_by: {user} ({user_discord_id}), "
                "amount: {amount}, "
                "reason: {reason}".format(
                    user=current_user.display_name,
                    user_discord_id=current_user.discord,
                    amount=form.amount.data,
                    reason=form.reason.data))

            flash("Money Transaction is added", "success")

        return render_template(
            "features/donations/hub/add_money_transaction.html",
            **self.get_args(),
            form=form)


class AddPointsTransactionView(DonationsView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access this page"),
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self):
        form = AddPointsTransactionForm()

        return render_template(
            "features/donations/hub/add_points_transaction.html",
            **self.get_args(),
            form=form)

    def post(self):
        form = AddPointsTransactionForm()

        if form.validate_on_submit():
            player = get_player_by_discord(form.discord.data, create_if_not_exists=True)
            assert actions.add_points_transaction_and_notify(player, form.amount.data, form.reason.data, current_user)
            flash("Points Transaction is added", "success")

        return render_template(
            "features/donations/hub/add_points_transaction.html",
            **self.get_args(),
            form=form)
