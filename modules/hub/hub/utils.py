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
    db_hub.session.add(player)
    db_hub.session.commit()
    
    return db_hub.session.query(Player).filter(Player.discord_user_id == discord_id).one_or_none()


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
        sock = socket.create_connection((host, int(port)), timeout=3)
    except socket.error:
        return None

    try:
        try:
            string_bytes = bytes(string, encoding='ascii')
        except UnicodeEncodeError:
            return None

        packet = struct.pack('>xcH5x', packet_id, len(string_bytes) + 6) + string_bytes + b'\x00'
        sock.send(packet)

        data = sock.recv(5000)
        if len(data) < 6:
            return None

        parsed = str(data[5:-1], encoding='ascii', errors='ignore')
        return urllib.parse.parse_qs(parsed, keep_blank_values=True)
    except Exception:
        return None
    finally:
        sock.close()


@attr.s(auto_attribs=True)
class ServerStatus:
    is_online: bool
    players_count: int


def get_server_status(server: ServerDescriptor) -> ServerStatus:
    data = byond_export('localhost', server.port, '?status')
    try:
        if not data or 'players' not in data or not data['players']:
            return ServerStatus(is_online=False, players_count=0)
        return ServerStatus(
            is_online=True,
            players_count=int(data['players'][0])
        )
    except (KeyError, ValueError, IndexError):
        return ServerStatus(is_online=False, players_count=0)


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
            links=server.links,
            is_online=status.is_online,
            players_count=status.players_count
        )

        entries.append(entry)

    return entries
