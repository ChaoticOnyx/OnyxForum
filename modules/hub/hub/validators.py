from wtforms import ValidationError
from flask_babelplus import gettext as _
from flaskbb.extensions import db_hub
from .utils import get_player_by_ckey
from .models import Player, Issue


class CkeyLinkedToDiscordValidator:
    def __init__(self):
        pass

    def __call__(self, form, field):
        player: Player = get_player_by_ckey(field.data)
        if player is None:
            raise ValidationError(_(
                    "%(ckey)s isn't found",
                    ckey=field.data,
                ))

        if not player.discord_user_id:
            raise ValidationError(_(
                "%(ckey)s isn't linked to any discord",
                ckey=field.data,
            ))

class IssueIsKnownValidator:
    def __init__(self):
        pass

    def __call__(self, form, field):
        if not field.data:
            return
        issue = db_hub.session.query(Issue).filter(Issue.id == field.data).one_or_none()
        if issue is None:
            raise ValidationError(_(
                    "Issue #%(issue)s is unknown",
                    issue=field.data,
                ))
