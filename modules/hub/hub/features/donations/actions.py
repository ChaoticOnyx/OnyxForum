from datetime import datetime
import logging
from dateutil import tz
from typing import Optional

from .hub.notifications import *
from . import money


logger = logging.getLogger('donations')


def add_donation_and_notify(dt: datetime, ckey: str, amount: float, type: str, registered_by: Optional[User]):
    utc_datetime = dt.astimezone(tz.tzutc())
    money_transaction, points_transaction = money.add_donation(utc_datetime, ckey, amount, type)
    if type != "patreon":
        report_money_transaction(money.get_current_balance(), money_transaction)
    report_points_transaction(points_transaction)
    notify_user_about_points_transaction(None if registered_by is None else registered_by._get_current_object(), points_transaction)
    registered_by_str = ""
    if registered_by is not None:
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
