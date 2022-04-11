import datetime
import logging
from dateutil import tz
from typing import Optional

from .hub.notifications import *
from . import money
from .utils import get_donations_host_user


logger = logging.getLogger('donations')


def add_donation_and_notify(dt: datetime.datetime, ckey: str, amount: float, type: str, registered_by: Optional[User]):
    utc_datetime = dt.astimezone(tz.tzutc())
    money_transaction, points_transaction = money.add_donation(utc_datetime, ckey, amount, type)
    if type != "patreon":
        report_money_transaction(money.get_current_balance(), money_transaction)

    donations_host_user = get_donations_host_user()
    if donations_host_user is not None and donations_host_user != registered_by:
        notify_user_about_points_transaction(donations_host_user._get_current_object(), points_transaction)

    registered_by_str = ""
    if registered_by is not None:
        notify_user_about_points_transaction(registered_by._get_current_object(), points_transaction)
        registered_by_str = "registered_by: {user} ({user_discord_id}), ".format(
            user=registered_by.display_name,
            user_discord_id=registered_by.discord)

    logger.info(
        "[AddDonation] "
        "{registered_by_str}"
        "datetime: {datetime}, "
        "ckey: {ckey}, "
        "amount: {amount}, "
        "type: {type}".format(
            registered_by_str=registered_by_str,
            datetime=dt.strftime("%d.%m.%Y %H:%M"),
            ckey=ckey,
            amount=amount,
            type=type))
