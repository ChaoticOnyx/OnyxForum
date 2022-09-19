import logging
from flaskbb.user.models import User
from flaskbb.forum.models import Post
from hub.features.karma.post_rating import get_post_rating, get_all_user_posts_rating
from .models import CommunityRating
from flaskbb.extensions import scheduler

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

    CommunityRating_changes = CommunityRating.query.filter_by(user_id=user.id).all()
    summary = 0

    for CommunityRating_change in CommunityRating_changes:
        summary += CommunityRating_change.change

    return summary

@scheduler.task('interval', id='weekly_community_rating_updatge', weeks=1)
def weekly_community_rating_update():
    with scheduler.app.app_context():
        for user in User.query.all():
            user_community_rating = get_user_community_rating(user)

            if ((user_community_rating == -1) or (user_community_rating == 1)):
                change_user_community_rating(user, 0-user_community_rating)
            elif (user_community_rating >=2):
                    change_user_community_rating(user, -2)
            elif (user_community_rating <=-2):
                    change_user_community_rating(user, 2)
