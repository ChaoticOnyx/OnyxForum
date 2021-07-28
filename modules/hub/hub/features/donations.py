
import math

from sqlalchemy import func

from flaskbb.user.models import User
from flaskbb.utils.helpers import render_template
from flaskbb.extensions import db_hub

from hub.models import Player, PointsTransaction


def get_user_points_sum(user: User) -> int:
    assert user

    cursor: db_hub.Query = db_hub.session.query(0 + func.sum(PointsTransaction.change)) \
        .join(PointsTransaction.player) \
        .filter(Player.discord_user_id == user.discord)

    return math.floor(cursor.first()[0]) or 0


def render_donations_label(user: User):
    assert user
    return render_template("features/donations_label.html", points_sum=get_user_points_sum(user))
