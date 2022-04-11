
import math

from sqlalchemy import func

from flask import current_app
from flaskbb.user.models import User
from flaskbb.utils.helpers import render_template
from flaskbb.extensions import db_hub, discordClient

from hub.models import DiscordUser, Player, PointsTransaction

def get_user_points_sum(user: User) -> int:
    assert user

    cursor: db_hub.Query = db_hub.session.query(0 + func.sum(PointsTransaction.change)) \
        .join(PointsTransaction.player) \
        .filter(Player.discord_user_id == user.discord)

    return math.floor(cursor.first()[0] or 0)


def render_donations_label(user: User):
    assert user
    return render_template("features/donations_label.html", points_sum=get_user_points_sum(user))


def get_donations_host_user() -> DiscordUser:
    host_user: DiscordUser = discordClient.get_user(current_app.config["DONATIONS_HOST_DISCORD_ID"])
    if host_user is None:
        print("Error: Donations host cannot be found!")
    return host_user
