from flaskbb.extensions import db, db_hub
from flaskbb.utils.database import UTCDateTime
from flaskbb.utils.helpers import time_utcnow
from sqlalchemy import Column, ForeignKey, String, Integer, Float, DateTime, text, Text, func
from sqlalchemy.orm import relationship

class CommunityRating(db.Model):
    __tablename__ = 'community_rating'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', ForeignKey('users.id'), nullable=False, index=True)
    change = Column(Integer, nullable=False)
    datetime = Column(UTCDateTime(timezone=True), default=time_utcnow, nullable=False)

    user = relationship("User")
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
