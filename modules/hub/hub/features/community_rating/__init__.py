from .community_rating import weekly_community_rating_update
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(weekly_community_rating_update, 'interval', weeks=1)
scheduler.start()