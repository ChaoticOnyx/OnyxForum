import attr
import os
import socket
import struct
from typing import List, Optional
import urllib

from werkzeug.local import LocalProxy
from flask import request, current_app

from flaskbb.extensions import db_hub
from hub.models import Player
from hub.servers_config import ServerDescriptor, ServerAdditionalLink

configs_path = os.path.dirname(os.path.abspath(__file__)) + "/configs"


def byond_key_to_ckey(key) -> str:
    assert key
    key = key.lower()
    return "".join([c for c in key if c.isalnum()])


def get_player_by_discord(discord_id, create_if_not_exists = False) -> Player:
    assert discord_id
    player = db_hub.session.query(Player).filter(Player.discord_user_id == discord_id).one_or_none()
    if player or not create_if_not_exists:
        return player

    player = Player()
    player.discord_user_id = discord_id
    player.save()
    return player


def get_player_by_ckey(ckey) -> Player:
    assert ckey
    return db_hub.session.query(Player).filter(Player.ckey == ckey).one_or_none()


def get_byond_ckey(user) -> str:
    assert user
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


def byond_export(host, port, string):
    packet_id = b'\x83'
    try:
        sock = socket.create_connection((host, port))
    except socket.error:
        return

    packet = struct.pack('>xcH5x', packet_id, len(string)+6) + bytes(string, encoding='ascii') + b'\x00'
    sock.send(packet)

    data = sock.recv(5000)
    sock.close()
    data = str(data[5:-1], encoding='ascii')
    return urllib.parse.parse_qs(data, keep_blank_values=True)


@attr.s(auto_attribs=True)
class ServerStatus:
    players_count: int

def get_server_status(server: ServerDescriptor) -> Optional[ServerStatus]:
    data = byond_export('localhost', str(server.port), '?status')
    if not data:
        return None
    return ServerStatus(data['players'][0])


@attr.s(auto_attribs=True)
class IndexServerEntry:
    name: str
    icon: str
    description: str
    links: List[ServerAdditionalLink]
    is_online: bool = False
    players_count: int = 0


def get_servers_for_index():
    servers: List[ServerDescriptor] = current_app.config["BYOND_SERVERS"]

    entries = []
    for server in servers:
        status = get_server_status(server)

        entry = IndexServerEntry(
            name=server.name,
            icon=server.icon,
            description=server.description,
            links=server.links
        )

        if status:
            entry.is_online = True
            entry.players_count = status.players_count

        entries.append(entry)

    return entries
