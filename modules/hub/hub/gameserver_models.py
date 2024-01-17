# coding: utf-8
import attr
import datetime
import pytz
from flaskbb.extensions import db_chaotic, db_onyx, db_eos, db_dragon
from sqlalchemy import Column, DateTime, Integer, String, Text, Index, text
from sqlalchemy.dialects.mysql import TINYINT, INTEGER, SMALLINT, VARCHAR


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


class ErroBanChaotic(db_chaotic.Model, ErroBan):
    __bind_key__ = 'chaotic'
    __tablename__ = 'erro_ban'


class ErroBanEos(db_eos.Model, ErroBan):
    __bind_key__ = 'eos'
    __tablename__ = 'erro_ban'

class ErroBanOnyx(db_onyx.Model, ErroBan):
    __bind_key__ = 'onyx'
    __tablename__ = 'erro_ban'

class ErroBanDragon(db_dragon.Model):
    __bind_key__ = 'dragon'
    __tablename__ = 'SS13_ban'
    __table_args__ = (
        Index('idx_ban_isbanned_details', 'ckey', 'ip', 'computerid', 'role', 'unbanned_datetime', 'expiration_time'),
        Index('idx_ban_count', 'bantime', 'a_ckey', 'applies_to_admins', 'unbanned_datetime', 'expiration_time'),
        Index('idx_ban_isbanned', 'ckey', 'role', 'unbanned_datetime', 'expiration_time')
    )

    id = Column(INTEGER, primary_key=True)
    bantime = Column(DateTime, nullable=False)
    server_name = Column(String(32))
    server_ip = Column(INTEGER, nullable=False)
    server_port = Column(SMALLINT, nullable=False)
    round_id = Column(INTEGER, nullable=False)
    role = Column(String(32))
    expiration_time = Column(DateTime)
    applies_to_admins = Column(TINYINT, nullable=False, server_default=text("'0'"))
    reason = Column(String(2048), nullable=False)
    ckey = Column(String(32))
    ip = Column(INTEGER)
    computerid = Column(String(32))
    a_ckey = Column(String(32), nullable=False)
    a_ip = Column(INTEGER, nullable=False)
    a_computerid = Column(String(32), nullable=False)
    who = Column(String(2048), nullable=False)
    adminwho = Column(String(2048), nullable=False)
    edits = Column(Text)
    unbanned_datetime = Column(DateTime)
    unbanned_ckey = Column(String(32))
    unbanned_ip = Column(INTEGER)
    unbanned_computerid = Column(String(32))
    unbanned_round_id = Column(INTEGER)
    global_ban = Column(TINYINT, nullable=False, server_default=text("'1'"))
    hidden = Column(TINYINT, nullable=False, server_default=text("'0'"))

    def get_ban_record(self):
        bantype = ""
        if self.role == "Server":
            if self.expiration_time:
                bantype = "tempban"
            else:
                bantype = "permaban"
        else:
            if self.expiration_time:
                bantype = "job_tempban"
            else:
                bantype = "job_permaban"

        return BanRecord(
            ckey=self.ckey,
            bantime=self.bantime and self.bantime.astimezone(pytz.UTC),
            expiration_time=self.expiration_time and self.expiration_time.astimezone(pytz.UTC),
            a_ckey=self.a_ckey,
            bantype=bantype,
            expired=(bantype != "permaban" and
                     bantype != "job_permaban" and
                     self.expiration_time.astimezone(pytz.UTC) < datetime.datetime.now(datetime.timezone.utc)),
            role=self.role,
            unbanned=bool(self.unbanned_datetime),
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


class Connection():
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


class ConnectionChaotic(db_chaotic.Model, Connection):
    __bind_key__ = 'chaotic'
    __tablename__ = 'connection'


class ConnectionEos(db_eos.Model, Connection):
    __bind_key__ = 'eos'
    __tablename__ = 'connection'

class ConnectionOnyx(db_onyx.Model, Connection):
    __bind_key__ = 'onyx'
    __tablename__ = 'connection'

class ConnectionDragon(db_dragon.Model):
    __bind_key__ = 'dragon'
    __tablename__ = 'SS13_connection_log'

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    server_name = Column(String(32))
    server_ip = Column(INTEGER, nullable=False)
    server_port = Column(SMALLINT, nullable=False)
    round_id = Column(INTEGER, nullable=False)
    ckey = Column(String(45))
    ip = Column(INTEGER, nullable=False)
    computerid = Column(String(45))

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

class ErroAdmin():
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

class ErroAdminChaotic(db_chaotic.Model, ErroAdmin):
    __bind_key__ = 'chaotic'
    __tablename__ = 'erro_admin'


class ErroAdminEos(db_eos.Model, ErroAdmin):
    __bind_key__ = 'eos'
    __tablename__ = 'erro_admin'

class ErroAdminOnyx(db_onyx.Model, ErroAdmin):
    __bind_key__ = 'onyx'
    __tablename__ = 'erro_admin'

game_models = {
    "chaotic":
        {
            "ErroBan": ErroBanChaotic,
            "Connection": ConnectionChaotic,
            "ErroAdmin": ErroAdminChaotic
        },
    "eos":
        {
            "ErroBan": ErroBanEos,
            "Connection": ConnectionEos,
            "ErroAdmin": ErroAdminEos
        },
    "malachite":
        {
            "ErroBan": ErroBanEos,
            "Connection": ConnectionEos,
            "ErroAdmin": ErroAdminEos,
        },
    "dragon":
        {
            "ErroBan": ErroBanDragon,
            "Connection": ConnectionDragon
        },
    "onyx":
        {
            "ErroBan": ErroBanOnyx,
            "Connection": ConnectionOnyx,
            "ErroAdmin": ErroAdminOnyx,
        },
}
