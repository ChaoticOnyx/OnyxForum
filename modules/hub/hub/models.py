import datetime

from flaskbb.utils.database import UTCDateTime
from flaskbb.utils.helpers import time_utcnow
from flaskbb.extensions import db, db_hub
from sqlalchemy import Column, ForeignKey, String, Integer, Float, Date, text, Text, ForeignKeyConstraint
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import relationship


class DiscordRole(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'discord_roles'

    id = Column(String(50), primary_key=True)
    title = Column(String(50), nullable=False)


class DiscordUser(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'discord_users'

    id = Column(String(50), primary_key=True)
    nickname = Column(VARCHAR(50))

    # name without #XXXX id on the end
    @property
    def pure_name(self):
        return self.nickname[:-5]

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self


class DiscordUserRole(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'discord_user_roles'

    id = Column(String(50), primary_key=True)
    user = Column(ForeignKey('discord_users.id'), nullable=False, index=True)
    role = Column(ForeignKey('discord_roles.id'), nullable=False, index=True)

    discord_role = relationship('DiscordRole')
    discord_user = relationship('DiscordUser')


class PatronType(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'patron_types'

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(32), nullable=False)
    cost_dollars = Column(Float, nullable=False)
    discord_role = Column(String(50), nullable=False)


class Player(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    ckey = Column(String(50), unique=True)
    discord_user_id = Column('discord', ForeignKey('discord_users.id'), index=True)
    patron_type_id = Column('patron_type', ForeignKey('patron_types.id'), index=True, server_default=text("0"))
    patron_type_charged_id = Column('patron_type_charged', ForeignKey('patron_types.id'))
    patron_until_date = Column(Date, nullable=True)

    discord_user: DiscordUser = relationship('DiscordUser', lazy='immediate')
    patron_type: PatronType = relationship('PatronType', lazy='immediate', primaryjoin='Player.patron_type_id == PatronType.id')
    patron_type_charged: PatronType = relationship('PatronType', lazy='immediate', primaryjoin='Player.patron_type_charged_id == PatronType.id')

    def get_str(self):
        return self.ckey or f"{self.discord_user.nickname} ({self.discord_user_id})"


class HubLog(db.Model):
    id = Column(Integer, primary_key=True)
    server_id = Column(String(50), nullable=False)
    datetime = Column(
        UTCDateTime(timezone=True), default=time_utcnow, nullable=False
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    message = Column(Text, nullable=False)

    user = relationship("User", lazy="joined", foreign_keys=[user_id])

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self


class Issue(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'issues'

    id = Column(Integer, primary_key=True)
    votes = Column(Integer)
    points = Column(Float)
    close_votes = Column(Integer)
    bounty = Column(Integer)


class PointsTransactionType(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'points_transactions_types'

    id = Column('id', Integer, primary_key=True)
    type = Column('type', String(32))


class PointsTransaction(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'points_transactions'

    id = Column('id', Integer, primary_key=True)
    player_id = Column('player', ForeignKey('players.id'), nullable=False, index=True)
    type_id = Column('type', ForeignKey('points_transactions_types.id'), nullable=False, index=True)
    datetime = Column('datetime', UTCDateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
    change = Column('change', Float, nullable=False)
    comment = Column('comment', Text)

    player = relationship('Player', lazy='immediate')
    type = relationship('PointsTransactionType', lazy='immediate')


class MoneyCurrency(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'money_currencies'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    division = Column(Integer, nullable=False)


class DonationType(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'donations_types'

    id = Column('id', Integer, primary_key=True)
    type = Column('type', String(32))


class MoneyTransaction(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'money_transactions'

    id = Column('id', Integer, primary_key=True)
    datetime = Column('datetime', UTCDateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
    currency_id = Column('currency', ForeignKey('money_currencies.id'), nullable=False, index=True)
    change_raw = Column('change', Integer, nullable=False, server_default=text("0"))
    reason = Column('reason', Text, nullable=False, server_default=text("''"))
    player_id = Column('player', ForeignKey('players.id'), index=True)
    donation_type_id = Column('donation_type', ForeignKey('donations_types.id'), index=True)
    issue_id = Column('issue', ForeignKey('issues.id'), index=True)

    currency = relationship('MoneyCurrency', lazy='immediate')
    donation_type = relationship('DonationType', lazy='immediate')
    issue = relationship('Issue', lazy='immediate')
    player = relationship('Player', lazy='immediate')

    @property
    def change(self):
        return self.change_raw / self.currency.division

    @change.setter
    def change(self, value):
        self.change_raw = int(value * self.currency.division)


class Token(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'tokens'

    token = Column(String(50), primary_key=True)
    discord_user_id = Column('discord', ForeignKey('discord_users.id'), nullable=False, index=True)

    discord_user = relationship('DiscordUser')

    def delete(self):
        db_hub.session.delete(self)
        db_hub.session.commit()
        return self

class IssueFull(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'issues_full'

    repository = Column(String(50), primary_key=True, nullable=False)
    number = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    author = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    created_datetime = Column(UTCDateTime(timezone=True), nullable=False)
    updated_datetime = Column(UTCDateTime(timezone=True), nullable=False)
    state = Column(String(50), nullable=False)

    labels = relationship("IssueLabel", back_populates="issue_full", cascade="all, delete-orphan")

class IssueLabel(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'issue_labels'
    __table_args__ = (
        ForeignKeyConstraint(['repository', 'issue_number'], ['issues_full.repository', 'issues_full.number']),
    )

    repository = Column(String(50), primary_key=True, nullable=False)
    issue_number = Column(Integer, primary_key=True, nullable=False)
    label = Column(String(50), primary_key=True, nullable=False)

    issue_full = relationship('IssueFull', back_populates="labels")
