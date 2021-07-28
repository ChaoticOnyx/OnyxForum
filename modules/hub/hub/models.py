from flaskbb.utils.database import UTCDateTime
from flaskbb.utils.helpers import time_utcnow
from flaskbb.extensions import db, db_hub
from sqlalchemy import Column, ForeignKey, String, Integer, Float, DateTime, text, Text, func
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

    id = Column('id', Integer, primary_key=True)
    type = Column('type', String(32), nullable=False)


class Player(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    ckey = Column(String(50), nullable=False, unique=True)
    discord_user_id = Column('discord', ForeignKey('discord_users.id'), index=True)
    patron_type_id = Column('patron_type', ForeignKey('patron_types.id'), index=True, server_default=text("0"))

    discord_user = relationship('DiscordUser')
    patron_type = relationship('PatronType')


class Karma(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'karma'

    id = Column(Integer, primary_key=True)
    player_to_id = Column('to', ForeignKey('players.id'), nullable=False, index=True)
    player_from_id = Column('from', ForeignKey('players.id'), nullable=False, index=True)
    change = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False, default=func.now())

    player_to = relationship('Player', primaryjoin='Karma.player_to_id == Player.id')
    player_from = relationship('Player', primaryjoin='Karma.player_from_id == Player.id')

    def save(self):
        db_hub.session.add(self)
        db_hub.session.commit()
        return self

    def delete(self):
        db_hub.session.delete(self)
        db_hub.session.commit()
        return self


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
    datetime = Column('datetime', DateTime, nullable=False)
    change = Column('change', Float, nullable=False)
    comment = Column('comment', Text)

    player = relationship('Player')
    type = relationship('PointsTransactionType')


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

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    currency_id = Column(ForeignKey('money_currencies.id'), nullable=False, index=True)
    change = Column(Integer, nullable=False, server_default=text("0"))
    reason = Column(Text, nullable=False, server_default=text("''"))
    player_id = Column(ForeignKey('players.id'), index=True)
    donation_type_id = Column(ForeignKey('donations_types.id'), index=True)
    issue_id = Column(ForeignKey('issues.id'), index=True)

    currency = relationship('MoneyCurrency')
    donations_type = relationship('DonationType')
    issue = relationship('Issue')
    player = relationship('Player')


class Token(db_hub.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'tokens'

    token = Column(String(50), primary_key=True)
    discord_user_id = Column(ForeignKey('discord_users.id'), nullable=False, index=True)

    discord_user = relationship('DiscordUser')
