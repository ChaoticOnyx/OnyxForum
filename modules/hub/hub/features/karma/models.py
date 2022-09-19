from flaskbb.extensions import db, db_hub
from flaskbb.utils.database import UTCDateTime
from flaskbb.utils.helpers import time_utcnow
from sqlalchemy import Column, ForeignKey, String, Integer, Float, DateTime, text, Text, func
from sqlalchemy.orm import relationship


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


class PostRate(db.Model):
    id = Column(Integer, primary_key=True)
    post_id = Column('post', ForeignKey('posts.id'), nullable=False, index=True)
    user_id = Column('user', ForeignKey('users.id'), nullable=False, index=True)
    change = Column(Integer, nullable=False)
    datetime = Column(UTCDateTime(timezone=True), default=time_utcnow, nullable=False)
    community_rating_record_id = Column('community_rating_record', ForeignKey('community_rating.id' , ondelete="CASCADE"), index=True)

    post = relationship("Post")
    user = relationship("User")
    community_rating_record = relationship("CommunityRating", cascade="all, delete")

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
