from datetime import datetime
import logging
from dateutil import tz
from typing import Optional

from hub.models import Player

from .hub.notifications import *
from . import discord_tasks, money, subscriptions


logger = logging.getLogger('donations')


def add_donation_and_notify(
    dt: datetime,
    player: Player,
    amount: float,
    type: str,
    issue: Optional[int] = None,
    registered_by: Optional[User] = None
):
    utc_datetime = dt.astimezone(tz.tzutc())
    money_transaction, points_transaction = money.add_donation(utc_datetime, player, amount, type, issue)
    if type != "patreon":
        report_money_transaction(money.get_current_balance(), money_transaction)
    report_points_transaction(points_transaction)
    notify_user_about_points_transaction(None if registered_by is None else registered_by._get_current_object(), points_transaction)
    if points_transaction.player.discord_user_id:
        discord_tasks.add_opyxholder_role(points_transaction.player.discord_user_id)
    registered_by_str = ""
    if registered_by is not None:
        registered_by_str = "registered_by: {user} ({user_discord_id}), ".format(
            user=registered_by.display_name,
            user_discord_id=registered_by.discord)

    logger.info(
        "[AddDonation] "
        "{registered_by_str}"
        "datetime: {datetime}, "
        "player: {ckey} ({discord} - {discord_id}), "
        "amount: {amount}, "
        "type: {type}".format(
            registered_by_str=registered_by_str,
            datetime=dt.strftime("%d.%m.%Y %H:%M"),
            ckey=player.ckey,
            discord=player.discord_user.nickname,
            discord_id=player.discord_user_id,
            amount=amount,
            type=type))

    subscriptions.update_subscriptions(points_transaction.player)
