import copy
import datetime
from dateutil import relativedelta
from dataclasses import dataclass
from typing import List
import string

from flask import request, url_for, redirect, current_app, abort, flash
from flask.views import MethodView

from flask_babelplus import gettext as _
from flask_login import current_user, login_required
from flask_sqlalchemy import Pagination

from flaskbb.display.navigation import NavigationLink
from flaskbb.utils.helpers import render_template
from flaskbb.extensions import db_hub

from hub.utils import configs_path, get_player_by_discord
from hub.models import Player, PointsTransaction, MoneyTransaction, DonationType, PatronType
from hub.features.donations import actions
from hub.features.donations.utils import get_player_points_sum
from hub.features.donations.discord_tasks import update_patron_role
from hub.features.donations.hub.notifications import notify_user_about_patron_tier_update, report_patron_tier_update

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
                endpoint="donations.patron",
                name=_("🫅 Patron Tier"),
                active=(request.endpoint == "donations.choose_tier"),
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
            datetime: datetime.datetime
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
            datetime: datetime.datetime
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


class PatronView(UserDonationsView):
    decorators = [login_required]

    def get(self):
        player = get_player_by_discord(current_user.discord)
        if not player:
            abort(404)

        if player.patron_type_id:
            tier = current_app.config["PATRON_TIERS"][player.patron_type_id - 1]
        else:
            return redirect(url_for("donations.choose_tier"))
        if player.patron_until_date:
            until_date = datetime.datetime.combine(player.patron_until_date, datetime.time())

        return render_template(
            "features/donations/patron.html",
            tier=tier,
            until_date=until_date,
            **self.get_args())


def _evaluate_charge_amount(patron_tier: str, patron_tier_charged: str, patron_until_date: datetime.date) -> int:
    if not patron_tier_charged or patron_until_date and patron_until_date <= datetime.datetime.utcnow().date():
        return patron_tier["price_opyxes"]

    if patron_tier_charged["price_opyxes"] >= patron_tier["price_opyxes"]:
        return 0

    charge_amount = patron_tier["price_opyxes"] - patron_tier_charged["price_opyxes"]

    days_left = (patron_until_date - datetime.datetime.utcnow().date()).days
    days_in_period = (patron_until_date - (patron_until_date - relativedelta.relativedelta(months=1))).days
    month_part_left = float(days_left) / days_in_period

    charge_amount = int(charge_amount * month_part_left)
    return charge_amount


class PatronChooseTierView(UserDonationsView):
    decorators = [login_required]

    def get(self):
        tiers = copy.deepcopy(current_app.config["PATRON_TIERS"])

        current_tier = None
        player = get_player_by_discord(current_user.discord)
        if not player:
            abort(404)
        if player.patron_type_id:
            current_tier = tiers[player.patron_type_id - 1]
        
        available_points = get_player_points_sum(player)
        if player.patron_type_charged_id:
            charged_tier = tiers[player.patron_type_charged_id - 1]
            for tier in tiers:
                tier["charge_amount"] = _evaluate_charge_amount(tier, charged_tier, player.patron_until_date)
                tier["available"] = (available_points >= tier["charge_amount"])
        else:
            available_points = get_player_points_sum(player)
            for tier in tiers:
                tier["available"] = (available_points >= tier["price_opyxes"])

        return render_template(
            "features/donations/choose_patron_tier.html",
            tiers=tiers,
            current_tier=current_tier,
            **self.get_args())

    def post(self):
        tier_type = request.args["tier_type"]
        patron_type: PatronType = db_hub.session.query(PatronType).filter(PatronType.type == tier_type).one_or_none()
        player = get_player_by_discord(current_user.discord)
        if not patron_type or not player:
            abort(404)

        tiers = current_app.config["PATRON_TIERS"]
        tier = tiers[patron_type.id - 1]
        charged_tier = player.patron_type_charged_id and tiers[player.patron_type_charged_id - 1]
        charge_amount = _evaluate_charge_amount(tier, charged_tier, player.patron_until_date)
        
        if charge_amount > 0:
            reason = f"Подписка патрона уровня {tier['title']}"
            points_transaction = actions.try_charge_points_transaction_and_notify(player, charge_amount, reason, current_user)
            if not points_transaction:
                flash(_(f"Недостаточно опиксов для подписки уровня {tier['title']}"), "danger")
                return redirect(url_for("donations.patron"))

        if not player.patron_type_charged_id or player.patron_type_charged_id < patron_type.id:
            player.patron_type_charged_id = patron_type.id
        player.patron_type_id = patron_type.id

        if not player.patron_until_date or player.patron_until_date <= datetime.datetime.utcnow().date():
            player.patron_until_date = datetime.datetime.utcnow().date() + relativedelta.relativedelta(months=1)

        db_hub.session.add(player)
        db_hub.session.commit()
        db_hub.session.expunge(player)

        notify_user_about_patron_tier_update(player)
        report_patron_tier_update(player)
        update_patron_role(player)

        return redirect(url_for("donations.patron"))


class PatronRevokeTierView(UserDonationsView):
    decorators = [login_required]

    def post(self):
        player = get_player_by_discord(current_user.discord)
        player.patron_type = None
        db_hub.session.commit()

        notify_user_about_patron_tier_update(player)
        report_patron_tier_update(player)
        update_patron_role(player)

        return redirect(url_for("donations.patron"))
