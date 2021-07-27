import datetime
import logging
from typing import Tuple

from sqlalchemy import func
from sqlalchemy.orm import aliased

from flask_login import current_user

from flaskbb.extensions import db_hub
from flaskbb.utils.requirements import has_permission
from flaskbb.utils.helpers import render_template
from hub.models import Player, Karma
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


def __fetch_all_karma_changes_by_user(discord_id, begin_from: datetime = None) -> Tuple[Karma]:
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


def is_user_can_change_karma(user, to_user=None) -> [bool, str]:
    assert user
    if not user.discord or not is_user_has_karma(user.discord):
        return False, "Your account is not linked with BYOND"

    if to_user and to_user.discord and __fetch_karma_change(to_user.discord, user.discord):
        return True, ""

    allowed_karma_changes = get_user_karma(user.discord)

    if allowed_karma_changes < 5:
        if not has_permission(user, "ignorekarma"):
            return False, "Your karma is not big enough"
        allowed_karma_changes = 5

    begin_from = datetime.datetime.now() - datetime.timedelta(days=1)
    last_karma_changes = __fetch_all_karma_changes_by_user(user.discord, begin_from)
    last_karma_changes_sum = len(last_karma_changes)

    if allowed_karma_changes <= last_karma_changes_sum:
        return False, "You have reached the day limit of karma changes"

    return True, ""


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
    __log_karma_change(player_to, player_from, value=value, change=value - prev_value)


def render_karma(user, post_id=None):
    karma = get_user_karma(user.discord)
    if karma is None:
        return

    available = False
    user_cant_change_reason = ""
    current_choice = 0

    if current_user and not current_user.is_anonymous:
        available = bool(
            user != current_user
        )
        if available:
            can_change, reason = is_user_can_change_karma(current_user, to_user=user)
            if not can_change:
                user_cant_change_reason = reason
            else:
                current_choice = get_current_choice(user.discord, current_user.discord)

    karma_color = ""
    if karma:
        karma_color = "karma-"
        if karma > 0:
            karma_color += "good"
        else:
            karma_color += "bad"
        if abs(karma) < 10:
            karma_color += "1"
        elif abs(karma) < 30:
            karma_color += "2"
        elif abs(karma) < 50:
            karma_color += "3"
        elif abs(karma) < 100:
            karma_color += "4"
        else:
            karma_color += "5"

    return render_template(
        "features/karma_label.html",
        user=user,
        post_id=post_id,
        karma=karma,
        karma_color=karma_color,
        available=available,
        user_cant_change_reason=user_cant_change_reason,
        current_choice=current_choice)
