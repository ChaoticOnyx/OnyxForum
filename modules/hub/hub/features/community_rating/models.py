class CommunityRating(db.Model):
    __bind_key__ = 'hub'
    __tablename__ = 'community_rating'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    change = Column(Integer, nullable=False)
    datetime = Column(UTCDateTime(timezone=True), default=time_utcnow, nullable=False)

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self