# coding: utf-8
import attr
import datetime
import pytz
import logging

from flaskbb.extensions import db
from sqlalchemy import Column, DateTime, Integer, String, Text, Index
from sqlalchemy.dialects.mysql import TINYINT, INTEGER, SMALLINT, VARCHAR
from sqlalchemy import MetaData
from sqlalchemy import literal
from sqlalchemy.orm import column_property
from sqlalchemy.ext.declarative import declared_attr


from hub.utils import get_servers_config

logger = logging.getLogger(__name__)

# =================================================
# DTOs (НЕ МЕНЯЕМ)
# =================================================

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


@attr.s
class ConnectionRecord:
    datetime = attr.ib()
    ckey = attr.ib()
    ip = attr.ib()
    computerid = attr.ib()


@attr.s
class AdminRecord:
    ckey = attr.ib()
    rank = attr.ib()
    flags = attr.ib()


# =================================================
# Base (erro_*) models (НЕ МЕНЯЕМ)
# =================================================

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
        # Важно: astimezone() на naive datetime падает.
        # Предполагаем, что значения уже tz-aware (как было в исходнике).
        bt = self.bantime and self.bantime.astimezone(pytz.UTC)
        et = self.expiration_time and self.expiration_time.astimezone(pytz.UTC)

        bantype_l = (self.bantype or "").lower()

        expired = (
            bantype_l != "permaban"
            and bantype_l != "job_permaban"
            and et is not None
            and et < datetime.datetime.now(datetime.timezone.utc)
        )

        return BanRecord(
            ckey=self.ckey,
            bantime=bt,
            expiration_time=et,
            a_ckey=self.a_ckey,
            bantype=bantype_l,
            expired=expired,
            role=self.job,
            unbanned=self.unbanned,
            unbanned_ckey=self.unbanned_ckey,
            unbanned_datetime=self.unbanned_datetime and self.unbanned_datetime.astimezone(pytz.UTC),
            reason=self.reason,
        )


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
            computerid=self.computerid,
        )


class ErroAdmin:
    id = Column(Integer, primary_key=True)
    ckey = Column(VARCHAR(50), nullable=False)
    rank = Column(VARCHAR(50), nullable=False)
    flags = Column(INTEGER, nullable=False)

    def get_record(self):
        return AdminRecord(
            ckey=self.ckey,
            rank=self.rank,
            flags=self.flags,
        )


class ErroWhitelist:
    id = Column(Integer, primary_key=True)
    ckey = Column(String(50), nullable=False, unique=True)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    text = Column(Text, nullable=False)


class ErroJobWhitelist:
    id = Column(Integer, primary_key=True)
    ckey = Column(String(50), nullable=False, unique=True)
    job = Column(String(50), nullable=False, unique=True)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    text = Column(Text, nullable=False)


# =================================================
# Dynamic metadata per bind
# =================================================

metadata_by_bind = {}


def get_metadata_for(bind_key: str):
    if bind_key not in metadata_by_bind:
        metadata_by_bind[bind_key] = MetaData()
    return metadata_by_bind[bind_key]


def create_game_model(base_cls, tablename: str, bind_key: str, extra_fields=None):
    name = f"{base_cls.__name__}_{bind_key}"
    class_attrs = {
        "__tablename__": tablename,
        "__bind_key__": bind_key,
        "metadata": get_metadata_for(bind_key),
    }
    if extra_fields:
        class_attrs.update(extra_fields)
    return type(name, (db.Model, base_cls), class_attrs)


# =================================================
# tg_base adapters (НЕ РАЗДУВАЕМ DTO; не трогаем ErroBan/Connection/ErroAdmin)
#   Идея: те же "ключи" в game_models ("ErroBan"/"Connection"/"ErroAdmin"),
#   но при tg_base подсовываем классы с TG-таблицами и минимальными методами,
#   возвращающими те же DTO.
# =================================================

def _utc(dt: datetime.datetime | None) -> datetime.datetime | None:
    if dt is None:
        return None
    # TG-схема часто хранит naive DATETIME. Считаем их UTC.
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc)


class _TgAdmin:
    # TG: admin(ckey PK, rank, feedback)
    ckey = Column(VARCHAR(32), primary_key=True, nullable=False)
    rank = Column(VARCHAR(32), nullable=False)
    feedback = Column(VARCHAR(255))

    @declared_attr
    def flags(cls):
        return column_property(literal(0))

    def get_record(self):
        # flags в TG-таблице нет → возвращаем 0 (DTO НЕ МЕНЯЕМ)
        return AdminRecord(ckey=self.ckey, rank=self.rank, flags=0)


class _TgBan:
    # TG: ban (см. describe ban)
    id = Column(Integer, primary_key=True, nullable=False)

    bantime = Column(DateTime, nullable=False)
    server_ip = Column(Integer, nullable=False)
    server_port = Column(SMALLINT, nullable=False)
    round_id = Column(Integer)

    role = Column(VARCHAR(32))
    expiration_time = Column(DateTime)  # может быть NULL
    applies_to_admins = Column(TINYINT(1), nullable=False, default=0)

    reason = Column(VARCHAR(2048), nullable=False)

    ckey = Column(VARCHAR(32))
    ip = Column(Integer)
    computerid = Column(VARCHAR(32))

    a_ckey = Column(VARCHAR(32), nullable=False)
    a_ip = Column(Integer, nullable=False)
    a_computerid = Column(VARCHAR(32), nullable=False)

    who = Column(VARCHAR(2048), nullable=False)
    adminwho = Column(VARCHAR(2048), nullable=False)
    edits = Column(Text)

    unbanned_datetime = Column(DateTime)
    unbanned_ckey = Column(VARCHAR(32))
    unbanned_ip = Column(Integer)
    unbanned_computerid = Column(VARCHAR(32))
    unbanned_round_id = Column(Integer)

    def get_ban_record(self):
        bt = _utc(self.bantime)
        et = _utc(self.expiration_time)

        # В TG нет bantype. Для совместимости:
        # - если role задан → считаем "job_ban" (или "job_permaban" при et=None)
        # - иначе → "ban" (или "permaban" при et=None)
        if et is None:
            bantype = "job_permaban" if self.role else "permaban"
        else:
            bantype = "job_ban" if self.role else "ban"

        expired = (et is not None and et < datetime.datetime.now(datetime.timezone.utc))

        # В TG нет флага unbanned; эквивалент — наличие unbanned_datetime
        unbanned = 1 if self.unbanned_datetime is not None else 0

        return BanRecord(
            ckey=self.ckey,
            bantime=bt and bt.astimezone(pytz.UTC),
            expiration_time=et and et.astimezone(pytz.UTC),
            a_ckey=self.a_ckey,
            bantype=bantype,
            expired=expired,
            role=self.role,
            unbanned=unbanned,
            unbanned_ckey=self.unbanned_ckey,
            unbanned_datetime=_utc(self.unbanned_datetime) and _utc(self.unbanned_datetime).astimezone(pytz.UTC),
            reason=self.reason,
        )


class _TgConnectionLog:
    # TG: connection_log (см. describe connection_log)
    id = Column(Integer, primary_key=True, nullable=False)
    datetime = Column(DateTime)
    server_ip = Column(Integer, nullable=False)
    server_port = Column(SMALLINT, nullable=False)
    round_id = Column(Integer)
    ckey = Column(VARCHAR(32))
    ip = Column(Integer, nullable=False)
    computerid = Column(VARCHAR(45))

    def get_record(self):
        dt = _utc(self.datetime)
        # ip в TG int; DTO ip у вас строка/any — возвращаем строкой, чтобы не ломать UI/шаблоны
        ip_str = str(self.ip) if self.ip is not None else None
        return ConnectionRecord(
            datetime=dt and dt.astimezone(pytz.UTC),
            ckey=self.ckey,
            ip=ip_str,
            computerid=self.computerid,
        )


# =================================================
# Model registry
# =================================================

game_models = {}


def load_dynamic_game_models():
    models = {}
    servers = get_servers_config()

    for server in servers:
        if server.id in game_models.keys():
            continue

        sid = server.id

        # По умолчанию (не TG)
        ban_tablename = "erro_ban"
        conn_tablename = "connection"
        admin_tablename = "erro_admin"

        ban_base = ErroBan
        conn_base = Connection
        admin_base = ErroAdmin

        ban_args = {}

        # TG base (tgstation / tg_base)
        if getattr(server, "tg_base", False):
            ban_tablename = "ban"
            conn_tablename = "connection_log"
            admin_tablename = "admin"

            ban_base = _TgBan
            conn_base = _TgConnectionLog
            admin_base = _TgAdmin

            # Индексы (опционально). Включайте только если реально нужны и совпадают поля.
            # ban_args["__table_args__"] = (
            #     Index('idx_ban_isbanned_details', 'ckey', 'ip', 'computerid', 'role', 'unbanned_datetime', 'expiration_time'),
            #     Index('idx_ban_count', 'bantime', 'a_ckey', 'applies_to_admins', 'unbanned_datetime', 'expiration_time'),
            #     Index('idx_ban_isbanned', 'ckey', 'role', 'unbanned_datetime', 'expiration_time'),
            # )

        models[sid] = {
            # Ключи НЕ меняем: потребители ожидают game_models[sid]["ErroBan"] и т.п.
            "ErroBan": create_game_model(ban_base, ban_tablename, sid, ban_args),
            "Connection": create_game_model(conn_base, conn_tablename, sid),
            "ErroAdmin": create_game_model(admin_base, admin_tablename, sid),
            "ErroWhitelist": create_game_model(ErroWhitelist, "erro_whitelist", sid),
            "ErroJobWhitelist": create_game_model(ErroJobWhitelist, "erro_job_whitelist", sid),
        }

    logger.info(f"Loaded dynamic game models for: {list(models.keys())}")
    return models


def init_game_models():
    global game_models
    game_models.update(load_dynamic_game_models())

