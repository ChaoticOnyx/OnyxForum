import datetime
from typing import Tuple

from flaskbb.user.models import User
from flaskbb.forum.models import Post
from flaskbb.utils.requirements import has_permission
from flaskbb.utils.helpers import render_template, time_utcnow

from flask_login import current_user

from .karma import get_user_karma, is_user_has_karma, get_current_choice, get_all_karma_changes_by_user
from .post_rating import get_post_rating, get_current_post_rate, get_all_post_rates_by_user


def __is_user_can_change_karma_and_rating(user):
    assert user

    allowed_actions = get_user_karma(user.discord)

    if allowed_actions < 5:
        if not has_permission(user, "ignorekarma"):
            return False, "Your karma is not big enough"
        allowed_actions = 5

    begin_from = datetime.datetime.now() - datetime.timedelta(days=1)
    last_karma_changes = get_all_karma_changes_by_user(user.discord, begin_from)
    last_post_rates = get_all_post_rates_by_user(user, begin_from)
    actions_sum = len(last_karma_changes) + len(last_post_rates)

    if allowed_actions <= actions_sum:
        return False, "You have reached the day limit of karma changes"

    return True, ""


def is_user_can_change_karma(user, to_user=None) -> [bool, str]:
    assert user
    if not user.discord or not is_user_has_karma(user.discord):
        return False, "Your account is not linked with BYOND"

    if to_user and to_user.discord and get_current_choice(to_user.discord, user.discord):
        return True, ""

    if to_user and user == to_user:
        return False, "You can't change your own karma"

    return __is_user_can_change_karma_and_rating(user)


def is_user_can_rate_post(user: User, post: Post) -> [bool, str]:
    assert user
    assert post
    if not user.discord or not is_user_has_karma(user.discord):
        return False, "Your account is not linked with BYOND"

    if get_current_post_rate(user, post):
        return False, "You have rated this post already"

    if user == post.user:
        return False, "You can't rate your own posts"

    if post.date_created < time_utcnow() - datetime.timedelta(days=7):
        return False, "Post is too old"

    return __is_user_can_change_karma_and_rating(user)


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
        "features/karma/karma_label.html",
        user=user,
        post_id=post_id,
        karma=karma,
        karma_color=karma_color,
        available=available,
        user_cant_change_reason=user_cant_change_reason,
        current_choice=current_choice)


def render_post_rating(post: Post):
    assert post

    post_rating = get_post_rating(post)

    available = False
    user_cant_change_reason = ""

    if current_user and not current_user.is_anonymous:
        available = bool(
             post.user != current_user
             and get_current_post_rate(current_user, post) is None
        )
        if available:
            can_rate, reason = is_user_can_rate_post(current_user, post)
            if not can_rate:
                user_cant_change_reason = reason

    rating_color = ""
    if post_rating:
        rating_color = "rating-"
        if post_rating > 0:
            rating_color += "good"
        else:
            rating_color += "bad"

    return render_template(
        "features/karma/post_rating_label.html",
        post_id=post.id,
        post_rating=post_rating,
        rating_color=rating_color,
        available=available,
        user_cant_change_reason=user_cant_change_reason)
