from flaskbb.extensions import db
from flaskbb.utils.database import UTCDateTime
from flaskbb.utils.helpers import time_utcnow
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import relationship


class DiscordRole(db.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'discord_roles'

    id = Column(String(50), primary_key=True)
    title = Column(String(50), nullable=False)


class DiscordUser(db.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'discord_users'

    id = Column(String(50), primary_key=True)
    nickname = Column(VARCHAR(50))

    # name without #XXXX id on the end
    @property
    def pure_name(self):
        return self.nickname[:-5]


class DiscordUserRole(db.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'discord_user_roles'

    id = Column(String(50), primary_key=True)
    user = Column(ForeignKey('discord_users.id'), nullable=False, index=True)
    role = Column(ForeignKey('discord_roles.id'), nullable=False, index=True)

    discord_role = relationship('DiscordRole')
    discord_user = relationship('DiscordUser')


class HubLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(
        UTCDateTime(timezone=True), default=time_utcnow, nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    message = db.Column(db.Text, nullable=False)

    user = db.relationship("User", lazy="joined", foreign_keys=[user_id])

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self
