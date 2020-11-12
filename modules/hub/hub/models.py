from flaskbb.extensions import db
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
