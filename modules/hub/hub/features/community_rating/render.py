from .community_rating import get_user_community_rating
from flaskbb.utils.helpers import render_template, time_utcnow
def render_community_rating(user):
    community_rating = get_user_community_rating(user)
    if community_rating is None:
        return
    community_rating_color = ""
    if community_rating:
        community_rating_color = "community_rating-"
        if community_rating > 0:
            community_rating_color += "good"
        else:
            community_rating_color += "bad"
        if abs(community_rating) < 10:
            community_rating_color += "1"
        elif abs(community_rating) < 30:
            community_rating_color += "2"
        elif abs(community_rating) < 50:
            community_rating_color += "3"
        elif abs(community_rating) < 100:
            community_rating_color += "4"
        else:
            community_rating_color += "5"

    return render_template(
        "features/community_rating_label.html",
        user=user,
        community_rating=community_rating,
        community_rating_color=community_rating_color
        )