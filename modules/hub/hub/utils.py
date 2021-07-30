import os

from werkzeug.local import LocalProxy
from flask import request, current_app

from flaskbb.extensions import db_hub
from hub.models import Player

configs_path = os.path.dirname(os.path.abspath(__file__)) + "/configs"


def get_player_by_discord(discord_id):
    if not discord_id:
        return None
    return db_hub.session.query(Player).filter(Player.discord_user_id == discord_id).one_or_none()


def get_byond_ckey(user):
    player: Player = get_player_by_discord(user.discord)
    if player is None:
        return None
    return player.ckey


@LocalProxy
def hub_current_server():
    if "server" not in request.args:
        return

    server_id = request.args["server"]

    servers = current_app.config["BYOND_SERVERS"]
    for server in servers:
        if server.id == server_id:
            return server
