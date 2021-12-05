import datetime
import logging
from typing import Tuple

from sqlalchemy import func
from sqlalchemy.orm import aliased

from flaskbb.extensions import db_hub
from flaskbb.user.models import User
from hub.features.karma.models import Karma
from hub.models import Player
from hub.utils import get_player_by_discord

logger = logging.getLogger('onyx')


def is_user_has_karma(discord_id):
    return bool(get_player_by_discord(discord_id))


def get_user_karma(discord_id):
    if not is_user_has_karma(discord_id):
        return None

    cursor: db_hub.Query = db_hub.session.query(0 + func.sum(Karma.change))\
        .join(Karma.player_to)\
        .filter(Player.discord_user_id == discord_id)
    return cursor.first()[0] or 0


def get_all_karma_changes_by_user(discord_id, begin_from: datetime = None) -> Tuple[Karma]:
    assert discord_id

    cursor: db_hub.Query = db_hub.session.query(Karma) \
        .join(Karma.player_from) \
        .filter(Player.discord_user_id == discord_id)

    if begin_from:
        cursor = cursor.filter(Karma.datetime >= begin_from)

    return cursor.all()


def __fetch_karma_change(to_discord_id, from_discord_id):
    assert to_discord_id
    assert from_discord_id

    player_to_type = aliased(Player)
    player_from_type = aliased(Player)

    cursor: db_hub.Query = db_hub.session.query(Karma) \
        .join(Karma.player_to.of_type(player_to_type)) \
        .join(Karma.player_from.of_type(player_from_type)) \
        .filter(player_to_type.discord_user_id == to_discord_id) \
        .filter(player_from_type.discord_user_id == from_discord_id)

    return cursor.one_or_none()


def get_current_choice(to_discord_id, from_discord_id):
    player_to: Player = get_player_by_discord(to_discord_id)
    player_from: Player = get_player_by_discord(from_discord_id)

    if not player_to or not player_from:
        return None

    karma = __fetch_karma_change(to_discord_id, from_discord_id)
    if not karma:
        return None

    return karma.change


def __log_karma_change(to: Player, _from: Player, value, change):
    summary = get_user_karma(to.discord_user_id)
    logger.info(
        "Karma change: {from_ckey} ({from_discord}) -> {to_ckey} ({to_discord}) "
        "(new value: {value}, change: {change}, summary: {summary})"
        .format(
            from_ckey=_from.ckey,
            from_discord=_from.discord_user_id,
            to_ckey=to.ckey,
            to_discord=to.discord_user_id,
            value=value,
            change=change,
            summary=summary))


def __update_player_rate_weight(discord_id):
    assert discord_id

    user: User = User.query.filter_by(discord=discord_id).first()
    karma = get_user_karma(discord_id)

    if karma >= 50:
        user.rate_weight = 3
    elif karma >= 30:
        user.rate_weight = 2
    else:
        user.rate_weight = 1

    user.save()


def change_user_karma(to_discord_id, from_discord_id, value):
    player_to: Player = get_player_by_discord(to_discord_id)
    player_from: Player = get_player_by_discord(from_discord_id)

    assert player_to
    assert player_from
    assert player_to != player_from

    karma = __fetch_karma_change(to_discord_id, from_discord_id)
    if karma:
        if value == 0:
            prev_value = karma.change
            karma.delete()
            __log_karma_change(player_to, player_from, value=value, change=value - prev_value)
            return
    else:
        assert value != 0
        karma = Karma(player_to_id=player_to.id, player_from_id=player_from.id)

    prev_value = karma.change or 0
    karma.change = value
    karma.save()
    __update_player_rate_weight(to_discord_id)
    __log_karma_change(player_to, player_from, value=value, change=value - prev_value)
