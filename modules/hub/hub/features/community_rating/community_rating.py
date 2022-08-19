from flaskbb.user.models import User
from flaskbb.forum.models import Post
from hub.features.karma.post_rating import get_post_rating, get_all_user_posts_rating

def __log_community_rating(user, value):
    assert user
    assert value

    summary = get_community_rating(user)
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
    summary = get_all_user_posts_rating(user)

    for CommunityRating_change in CommunityRating_changes:
        summary += CommunityRating_change

    return summary