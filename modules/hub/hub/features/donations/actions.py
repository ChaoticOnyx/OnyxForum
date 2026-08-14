from datetime import datetime
import logging
from dateutil import tz
from typing import Optional

from hub.models import Player, PointsTransaction

from .hub.notifications import *
from . import discord_tasks, money


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


def add_points_transaction_and_notify(
    player: Player,
    amount: float,
    reason: str,
    registered_by: Optional[User] = None,
    commit: bool = True,
    notify: bool = True,
    transaction_type: str = "other",
):
    assert player
    assert amount
    assert reason
    if notify and not commit:
        raise ValueError("Points notifications can only be dispatched after commit")

    points_transaction = money.add_points_transaction(
        player,
        amount,
        reason,
        commit=commit,
        transaction_type=transaction_type,
    )
    if notify:
        dispatch_points_transaction_notifications(points_transaction, registered_by)

    return points_transaction


def dispatch_points_transaction_notifications(
    points_transaction: PointsTransaction,
    registered_by: Optional[User] = None,
):
    """Run the standard HUB side effects for a committed Points change."""
    assert points_transaction
    assert points_transaction.player
    assert points_transaction.change

    registered_by_user = registered_by
    get_current_object = getattr(registered_by, "_get_current_object", None)
    if get_current_object is not None:
        registered_by_user = get_current_object()

    report_points_transaction(points_transaction)
    notify_user_about_points_transaction(registered_by_user, points_transaction)
    if points_transaction.player.discord_user_id and points_transaction.change > 0:
        discord_tasks.add_opyxholder_role(points_transaction.player.discord_user_id)
    registered_by_str = ""
    if registered_by_user is not None:
        registered_by_str = "registered_by: {user} ({user_discord_id}), ".format(
            user=registered_by_user.display_name,
            user_discord_id=registered_by_user.discord)
    player = points_transaction.player
    logger.info(
        "[AddPointsTransaction] "
        "{registered_by_str}"
        "player: {ckey} ({discord} - {discord_id}), "
        "amount: {amount}, "
        "reason: {reason}".format(
            registered_by_str=registered_by_str,
            ckey=player.ckey,
            discord=player.discord_user.nickname,
            discord_id=player.discord_user_id,
            amount=points_transaction.change,
            reason=points_transaction.comment))


def try_charge_points_transaction_and_notify(player: Player, amount: float, reason: str, registered_by: Optional[User] = None):
    assert player
    assert amount > 0
    assert reason

    if amount > get_player_points_sum(player):
        return None

    return add_points_transaction_and_notify(player, -amount, reason, registered_by)
