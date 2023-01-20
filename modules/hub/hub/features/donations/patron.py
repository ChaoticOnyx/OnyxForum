import datetime
from dateutil import relativedelta

from flask import current_app

from flaskbb.extensions import db_hub, scheduler

from hub.models import Player
from hub.features.donations import actions
from hub.features.donations.hub.notifications import report_patron_tier_update, notify_user_about_patron_tier_update

@scheduler.task('interval', id='daily_patron_tiers_update', minutes=1)
def daily_patron_tiers_update():
    with scheduler.app.app_context():
        tiers = current_app.config["PATRON_TIERS"]
        player: Player
        for player in db_hub.session.query(Player).filter(Player.patron_until_date <= datetime.datetime.utcnow().date()).all():
            points_transaction = None
            if player.patron_type:
                tier = tiers[player.patron_type.id - 1]
                reason = f"Подписка патрона уровня {tier['title']}"      
                points_transaction = actions.try_charge_points_transaction_and_notify(player, tier["price_opyxes"], reason)
            if not points_transaction:
                player.patron_type = None
                player.patron_type_charged = None
                player.patron_until_date = None

                db_hub.session.add(player)
                db_hub.session.commit()
                db_hub.session.expunge(player)

                report_patron_tier_update(player)
                notify_user_about_patron_tier_update(player)
            else:
                player.patron_type_charged = player.patron_type
                player.patron_until_date = datetime.datetime.utcnow().date() + relativedelta.relativedelta(months=1)
                db_hub.session.add(player)
                db_hub.session.commit()
            
