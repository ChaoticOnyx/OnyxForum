import datetime
import math
from typing import Optional

from sqlalchemy import func

from flaskbb.extensions import db_hub

from hub.models import MoneyTransaction, MoneyCurrency, DonationType, PointsTransaction, PointsTransactionType
from hub.utils import get_player_by_ckey


def __donation_type_to_description(donation_type):
    if donation_type == "qiwi":
        return "Пожертвование через QIWI"
    elif donation_type == "patreon":
        return "Подписка Patreon"
    else:
        return donation_type


def add_donation(dt: datetime.datetime, ckey: str, donation: float, donation_type: str) \
        -> (MoneyTransaction, PointsTransaction):
    assert dt
    assert ckey
    assert donation
    assert donation_type

    money_transaction = MoneyTransaction()
    money_transaction.datetime = dt
    money_transaction.player = get_player_by_ckey(ckey)

    money_transaction.currency = \
        db_hub.session.query(MoneyCurrency).filter(MoneyCurrency.name == "ruble").one_or_none()
    money_transaction.change = donation
    money_transaction.donation_type = \
        db_hub.session.query(DonationType).filter(DonationType.type == donation_type).one_or_none()
    money_transaction.reason = 'Пожертвование игрока'

    points_transaction = PointsTransaction()
    points_transaction.player = money_transaction.player
    points_transaction.change = money_transaction.change / 10
    points_transaction.comment = __donation_type_to_description(money_transaction.donation_type.type)
    points_transaction.type = \
        db_hub.session.query(PointsTransactionType).filter(PointsTransactionType.type == "donation").one_or_none()

    db_hub.session.add_all([money_transaction, points_transaction])
    db_hub.session.commit()

    db_hub.session.refresh(money_transaction)
    db_hub.session.refresh(points_transaction)
    db_hub.session.expunge_all()

    return money_transaction, points_transaction


def add_money_transaction(change: float, reason: str, ckey: Optional[str]):
    assert change
    assert reason

    money_transaction = MoneyTransaction()
    if ckey:
        money_transaction.player = get_player_by_ckey(ckey)

    money_transaction.currency = \
        db_hub.session.query(MoneyCurrency).filter(MoneyCurrency.name == "ruble").one_or_none()
    money_transaction.change = change
    money_transaction.reason = reason

    db_hub.session.add(money_transaction)
    db_hub.session.commit()

    db_hub.session.refresh(money_transaction)
    db_hub.session.expunge_all()

    return money_transaction


def add_points_transaction(ckey: str, change: float, reason: str):
    assert ckey
    assert change
    assert reason

    points_transaction = PointsTransaction()
    if ckey:
        points_transaction.player = get_player_by_ckey(ckey)
    points_transaction.change = change
    points_transaction.comment = reason
    points_transaction.type = \
        db_hub.session.query(PointsTransactionType).filter(PointsTransactionType.type == "other").one_or_none()

    db_hub.session.add(points_transaction)
    db_hub.session.commit()

    db_hub.session.refresh(points_transaction)
    db_hub.session.expunge_all()

    return points_transaction


def get_current_balance():
    cursor: db_hub.Query = db_hub.session.query(0 + func.sum(MoneyTransaction.change_raw)) \
        .join(MoneyTransaction.currency) \
        .filter(MoneyCurrency.name == "ruble")

    currency: MoneyCurrency = db_hub.session.query(MoneyCurrency).filter(MoneyCurrency.name == "ruble").one_or_none()

    return math.floor(cursor.first()[0] / currency.division or 0)
