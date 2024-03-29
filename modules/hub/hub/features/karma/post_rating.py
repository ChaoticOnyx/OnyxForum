import datetime
import logging
from typing import Tuple

from sqlalchemy import func

from flask_login import current_user

from flaskbb.user.models import User
from flaskbb.forum.models import Post
from flaskbb.utils.helpers import render_template
from flaskbb.extensions import db
from flaskbb.utils.requirements import has_permission
from hub.features.karma.models import PostRate
from hub.features.community_rating.models import CommunityRating
from .karma import is_user_has_karma, get_user_karma

logger = logging.getLogger('onyx')


def get_post_rating(post):
    assert post
    return db.session.query(0 + func.sum(PostRate.change))\
        .filter(PostRate.post_id == post.id)\
        .scalar() or 0


def get_all_post_rates_by_user(user, begin_from: datetime = None) -> Tuple[PostRate]:
    assert user

    cursor: db.Query = db.session.query(PostRate) \
        .join(PostRate.user) \
        .filter(PostRate.user == user)

    if begin_from:
        cursor = cursor.filter(PostRate.datetime >= begin_from)

    return cursor.all()


def get_all_post_rates_by_post(post):
    post_rate_records = PostRate.query.filter_by(post_id=post.id).order_by(PostRate.change).all()
    return post_rate_records


def __fetch_post_rate(user, post):
    assert user
    assert post

    cursor: db.Query = db.session.query(PostRate) \
        .join(PostRate.user) \
        .join(PostRate.post) \
        .filter(PostRate.user == user) \
        .filter(PostRate.post == post)

    return cursor.one_or_none()


def get_current_post_rate(user, post):
    assert user
    assert post

    rate = __fetch_post_rate(user, post)
    if not rate:
        return None

    return rate.change


def __log_post_rate(user, post, value):
    summary = get_post_rating(post)
    logger.info(
        "Post rated: #{post_number} is rated by {username} ({discord}) as {value}"
        "(new rating: {summary})"
        .format(
            post_number=post.id,
            username=user.display_name,
            discord=user.discord,
            value=value,
            summary=summary))


def change_post_rating(user: User, post: Post, value: int):
    assert user
    assert post

    rate = __fetch_post_rate(user, post)
    if rate:
        if value == 0:
            rate.delete()
            __log_post_rate(user, post, value=value)
            return
    else:
        assert value != 0
        rate = PostRate(user=user, post=post)

    if not rate.community_rating_record:
        rate.community_rating_record = CommunityRating()

    if user.rate_weight:
        value *= user.rate_weight

    rate.change = value
    rate.community_rating_record.user_id = post.user_id
    rate.community_rating_record.change = value
    rate.save()
    __log_post_rate(user, post, value=value)
