
from flask.views import MethodView
from flask_login import current_user

from flaskbb.forum.models import Topic, Forum
from flaskbb.user.models import User, Group
from flaskbb.utils.helpers import render_template
from flaskbb.utils.settings import flaskbb_config

from hub.utils import get_servers_for_index

class IndexView(MethodView):
    def get(self):
        forum_ids = flaskbb_config.get("FORUM_IDS", None)
        news = ()
        if forum_ids:
            group_ids = [group.id for group in current_user.groups]
            forums = Forum.query.filter(Forum.groups.any(Group.id.in_(group_ids)))
            news_ids = [f.id for f in forums.filter(Forum.id.in_(forum_ids)).all()]
            news = Topic.query.filter(Topic.forum_id.in_(news_ids)) \
                .order_by(Topic.id.desc()).all()

        return render_template(
            "index.html",
            news=news,
            servers=get_servers_for_index())
