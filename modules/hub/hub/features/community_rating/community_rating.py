import logging

from flaskbb.user.models import User
from flaskbb.forum.models import Post
from flaskbb.extensions import db, scheduler

from hub.features.karma.post_rating import get_post_rating
from .models import CommunityRating

from sqlalchemy.sql import func
from math import copysign


logger = logging.getLogger('onyx')

def __log_community_rating(user, value):
    assert user
    assert value

    summary = get_user_community_rating(user)
    logger.info(
        "User community rating change: #{user_id}({username}, {discord}) community rating changed as {value}"
        "(new rating: {summary})"
        .format(
            user_id=user.id,
            username=user.display_name,
            discord=user.discord,
            value=value,
            summary=summary))


def change_user_community_rating(user, value):
    assert user
    assert value

    community_rating = CommunityRating(user_id=user.id, change=value)
    community_rating.save()

    __log_community_rating(user, value=value)


def get_user_community_rating(user):
    assert user
    return db.session.query(0 + func.sum(CommunityRating.change))\
        .filter(CommunityRating.user_id == user.id)\
        .scalar() or 0


@scheduler.task('interval', id='weekly_community_rating_update', weeks=1)
def weekly_community_rating_update():
    with scheduler.app.app_context():
        for user in User.query.all():
            user_community_rating = get_user_community_rating(user)
            if not user_community_rating:
                continue
            change_user_community_rating(user, -copysign(min(2, abs(user_community_rating)), user_community_rating))
