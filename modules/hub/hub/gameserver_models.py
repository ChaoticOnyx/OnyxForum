# coding: utf-8
import attr
import datetime
import pytz
import types
import logging
from flaskbb.extensions import db
from sqlalchemy import Column, DateTime, Integer, String, Text, Index, text
from sqlalchemy.dialects.mysql import TINYINT, INTEGER, SMALLINT, VARCHAR
from hub.utils import get_servers_config
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

@attr.s
class BanRecord:
    ckey = attr.ib()
    bantime = attr.ib()
    expiration_time = attr.ib()
    a_ckey = attr.ib()
    bantype = attr.ib()
    expired = attr.ib()
    role = attr.ib()
    unbanned = attr.ib()
    unbanned_ckey = attr.ib()
    unbanned_datetime = attr.ib()
    reason = attr.ib()
    desc = attr.ib(default="")


class ErroBan:
    id = Column(Integer, primary_key=True, nullable=False)
    bantime = Column(DateTime, nullable=False)
    serverip = Column(String(32), nullable=False)
    bantype = Column(String(32), nullable=False)
    reason = Column(Text, nullable=False)
    job = Column(String(32))
    duration = Column(Integer, nullable=False)
    rounds = Column(Integer)
    expiration_time = Column(DateTime, nullable=False)
    ckey = Column(String(32), nullable=False)
    computerid = Column(String(32), nullable=False)
    ip = Column(String(32), nullable=False)
    a_ckey = Column(String(32), nullable=False)
    a_computerid = Column(String(32), nullable=False)
    a_ip = Column(String(32), nullable=False)
    who = Column(Text, nullable=False)
    adminwho = Column(Text, nullable=False)
    edits = Column(Text)
    unbanned = Column(TINYINT(1))
    unbanned_datetime = Column(DateTime)
    unbanned_reason = Column(Text)
    unbanned_ckey = Column(String(32))
    unbanned_computerid = Column(String(32))
    unbanned_ip = Column(String(32))
    server_id = Column(String(32), primary_key=True, nullable=False)

    def get_ban_record(self):
        return BanRecord(
            ckey=self.ckey,
            bantime=self.bantime and self.bantime.astimezone(pytz.UTC),
            expiration_time=self.expiration_time and self.expiration_time.astimezone(pytz.UTC),
            a_ckey=self.a_ckey,
            bantype=self.bantype.lower(),
            expired=(self.bantype.lower() != "permaban" and
                     self.bantype.lower() != "job_permaban" and
                     self.expiration_time.astimezone(pytz.UTC) < datetime.datetime.now(datetime.timezone.utc)),
            role=self.job,
            unbanned=self.unbanned,
            unbanned_ckey=self.unbanned_ckey,
            unbanned_datetime=self.unbanned_datetime and self.unbanned_datetime.astimezone(pytz.UTC),
            reason=self.reason
        )


@attr.s
class ConnectionRecord:
    datetime = attr.ib()
    ckey = attr.ib()
    ip = attr.ib()
    computerid = attr.ib()


class Connection:
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    ckey = Column(VARCHAR(50))
    ip = Column(VARCHAR(50), nullable=False)
    computerid = Column(VARCHAR(50), nullable=False)

    def get_record(self):
        return ConnectionRecord(
            datetime=self.datetime.astimezone(pytz.UTC),
            ckey=self.ckey,
            ip=self.ip,
            computerid=self.computerid
        )


@attr.s
class AdminRecord:
    ckey = attr.ib()
    rank = attr.ib()
    flags = attr.ib()


class ErroAdmin:
    id = Column(Integer, primary_key=True)
    ckey = Column(VARCHAR(50), nullable=False)
    rank = Column(VARCHAR(50), nullable=False)
    flags = Column(INTEGER, nullable=False)

    def get_record(self):
        return AdminRecord(
            ckey=self.ckey,
            rank=self.rank,
            flags=self.flags
        )

class ErroWhitelist:
    id = Column(Integer, primary_key=True)
    ckey = Column(String(50), nullable=False, unique=True)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    text = Column(Text, nullable=False)

metadata_by_bind = {}
def get_metadata_for(bind_key: str):
    if bind_key not in metadata_by_bind:
        metadata_by_bind[bind_key] = MetaData()
    return metadata_by_bind[bind_key]

def create_game_model(base_cls, tablename: str, bind_key: str, extra_fields=None):
    name = f"{base_cls.__name__}_{bind_key}"
    class_attrs = {
        '__tablename__': tablename,
        '__bind_key__': bind_key,
        'metadata': get_metadata_for(bind_key)
    }
    if extra_fields:
        class_attrs.update(extra_fields)
    return type(name, (db.Model, base_cls), class_attrs)


game_models = {}
def load_dynamic_game_models():
    models = {}
    servers = get_servers_config()

    for server in servers:

        if(server.id in game_models.keys()):
            continue

        sid = server.id
        erro_ban_tablename = "erro_ban"
        connection_tablename = "connection"
        admin_tablename = "erro_admin"
        whitelist_tablename = "erro_whitelist"

        erro_ban_args = {}
        if sid == "openkeep":
            erro_ban_args["__table_args__"] = (
                Index('idx_ban_isbanned_details', 'ckey', 'ip', 'computerid', 'role', 'unbanned_datetime', 'expiration_time'),
                Index('idx_ban_count', 'bantime', 'a_ckey', 'applies_to_admins', 'unbanned_datetime', 'expiration_time'),
                Index('idx_ban_isbanned', 'ckey', 'role', 'unbanned_datetime', 'expiration_time')
            )

        models[sid] = {
            "ErroBan": create_game_model(ErroBan, erro_ban_tablename, sid, erro_ban_args),
            "Connection": create_game_model(Connection, connection_tablename, sid),
            "ErroAdmin": create_game_model(ErroAdmin, admin_tablename, sid),
            "ErroWhitelist": create_game_model(ErroWhitelist, whitelist_tablename, sid)
        }

    logger.info(f"Loaded dynamic game models for: {list(models.keys())}")
    return models

def init_game_models():
    global game_models
    game_models.update(load_dynamic_game_models())