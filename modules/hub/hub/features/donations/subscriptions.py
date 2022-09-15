import discord
import datetime
from dateutil.relativedelta import relativedelta
from typing import List
import logging

from yahoo_fin import stock_info

from flaskbb.extensions import discordClient, db_hub
from flaskbb.utils.helpers import discord_task

from hub.models import Player, MoneyTransaction, PatronSubscription, PatronType
from hub.utils import *

from flaskbb.utils.helpers import time_utcnow
from .hub.notifications import notify_user_about_subscription_update, report_subscription_update

logger = logging.getLogger('donations')

def __convert_rubles_to_dollars(amount: float, date: datetime.date) -> float:
    data = stock_info.get_data("USDRUB=x", start_date=date - datetime.timedelta(weeks=1), end_date=date)
    rate = data.iloc[-1].close
    return amount / rate

def __convert_donation_summary_to_patron_type(donations_summary_in_dollars: float) -> PatronType:
    patron_types: List[PatronType] = db_hub.session.query(PatronType) \
        .order_by(PatronType.cost_dollars.desc()) \
        .all()

    PermittedErrorCoeff = 0.9

    for patron_type in patron_types:
        if patron_type.cost_dollars == 0 or donations_summary_in_dollars >= patron_type.cost_dollars * PermittedErrorCoeff:
            return patron_type


def __sync_player_patron_type(player: Player, subscriptions: List[PatronSubscription]):
    max_patron_type: PatronType = None
    for subscription in subscriptions:
        if not max_patron_type or max_patron_type.cost_dollars < subscription.patron_type.cost_dollars:
            max_patron_type = subscription.patron_type
    player.patron_type = max_patron_type
    db_hub.session.commit()


@discord_task
async def __add_patron_roles(player: Player, subscriptions: List[PatronSubscription]):
    guild: discord.Guild = await discordClient.fetch_guild(current_app.config["COMMUNITY_GUILD_ID"])
    member: discord.Member = await guild.fetch_member(int(player.discord_user_id))

    all_patron_role_ids = []
    max_patron_type: PatronType = None
    for subscription in subscriptions:
        if not max_patron_type or max_patron_type.cost_dollars < subscription.patron_type.cost_dollars:
            max_patron_type = subscription.patron_type
        role = max_patron_type.discord_role
        if role and not role in all_patron_role_ids:
            all_patron_role_ids.append(role)

    all_patron_roles = []
    for role_id in all_patron_role_ids:
        role = guild.get_role(int(role_id))
        if role:
            all_patron_roles.append(role)

    discordRoles: map = current_app.config["DISCORD_ROLES"]
    await member.remove_roles(*all_patron_roles)
    await member.add_roles(guild.get_role(discordRoles["Patron"]), guild.get_role(int(max_patron_type.discord_role)))


def __create_or_update_subscription(player: Player, donations_summary_in_dollars: float, start_date: datetime.date) \
        -> PatronSubscription:
    patron_type = __convert_donation_summary_to_patron_type(donations_summary_in_dollars)

    cursor: db_hub.Query = db_hub.session.query(PatronSubscription) \
        .filter(PatronSubscription.player_id == player.id) \
        .filter(PatronSubscription.start_date + start_date)
    subscription: PatronSubscription = cursor.one_or_none()

    old_patron_type: PatronType = None
    if subscription:
        if patron_type.cost_dollars <= subscription.patron_type.cost_dollars:
            return None
        old_patron_type = subscription.patron_type
    else:
        subscription = PatronSubscription()
        subscription.player_id = player.id
        subscription.start_date = start_date
        subscription.end_date = start_date + relativedelta(months=1)

    subscription.patron_type = patron_type
    subscription.registered_datetime = time_utcnow()

    db_hub.session.add(subscription)
    db_hub.session.commit()

    db_hub.session.refresh(subscription)

    if not old_patron_type:
        logger.info(
            "[CreateSubscription] "
            "ckey: {ckey}, "
            "start_date: {start_date}, "
            "end_date: {end_date}, "
            "patron_type: {patron_type}".format(
                ckey=player.ckey,
                start_date=subscription.start_date.strftime("%d.%m.%Y"),
                end_date=subscription.end_date.strftime("%d.%m.%Y"),
                patron_type=subscription.patron_type.type))
    else:
        logger.info(
            "[UpdateSubscription] "
            "ckey: {ckey}, "
            "start_date: {start_date}, "
            "end_date: {end_date}, "
            "patron_type: {old_patron_type} -> {patron_type}".format(
                ckey=player.ckey,
                start_date=subscription.start_date.strftime("%d.%m.%Y"),
                end_date=subscription.end_date.strftime("%d.%m.%Y"),
                old_patron_type=old_patron_type.type,
                patron_type=subscription.patron_type.type))

    return subscription


def update_subscriptions(player: Player):
    cursor: db_hub.Query = db_hub.session.query(MoneyTransaction) \
        .filter(MoneyTransaction.player_id == player.id) \
        .filter(MoneyTransaction.datetime >= time_utcnow() - relativedelta(months=1))

    money_transactions = cursor.all()

    money_summary_in_dollars = 0
    subscriptions: List[PatronSubscription] = []
    transaction: MoneyTransaction = None
    for transaction in reversed(money_transactions):
        start_date = transaction.datetime.date()
        money_summary_in_dollars += __convert_rubles_to_dollars(transaction.change, start_date)
        subscription = __create_or_update_subscription(player, money_summary_in_dollars, start_date)
        if subscription and not subscription in subscriptions:
            subscriptions.append(subscription)

    if not len(subscriptions):
        return

    __sync_player_patron_type(player, subscriptions)
    __add_patron_roles(player, subscriptions)

    notify_user_about_subscription_update(subscriptions)
    report_subscription_update(subscriptions)
