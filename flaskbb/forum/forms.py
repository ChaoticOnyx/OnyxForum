# -*- coding: utf-8 -*-
"""
    flaskbb.forum.forms
    ~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the forum views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
from sqlalchemy import or_

from flask import current_app
from flask_babelplus import lazy_gettext as _
from flask_wtf import FlaskForm
from wtforms import (BooleanField, SelectField, SelectMultipleField, StringField,
                     SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length, Optional

from flaskbb.forum.models import Forum, Post, Report, Topic
from flaskbb.user.models import Group, User
from flaskbb.utils.helpers import time_utcnow

logger = logging.getLogger(__name__)


class PostForm(FlaskForm):
    content = TextAreaField(
        _("Content"),
        validators=[
            DataRequired(message=_("You cannot post a reply without content."))
        ],
    )

    submit = SubmitField(_("Reply"))

    def save(self, user, topic):
        post = Post(content=self.content.data)
        current_app.pluggy.hook.flaskbb_form_post_save(form=self, post=post)
        return post.save(user=user, topic=topic)


class QuickreplyForm(PostForm):
    pass


class ReplyForm(PostForm):
    track_topic = BooleanField(
        _("Track this topic"), default=False, validators=[Optional()]
    )

    def __init__(self, *args, **kwargs):
        self.post = kwargs.get("obj", None)
        PostForm.__init__(self, *args, **kwargs)

    def save(self, user, topic):
        # new post
        if self.post is None:
            self.post = Post(content=self.content.data)
        else:
            self.post.date_modified = time_utcnow()
            self.post.modified_by = user.display_name
            self.post.modified_by_user_id = user.id

        if self.track_topic.data:
            user.track_topic(topic)
        else:
            user.untrack_topic(topic)

        current_app.pluggy.hook.flaskbb_form_post_save(
            form=self, post=self.post
        )
        return self.post.save(user=user, topic=topic)


class TopicForm(FlaskForm):
    title = StringField(
        _("Topic title"),
        validators=[
            DataRequired(message=_("Please choose a title for your topic."))
        ],
    )

    content = TextAreaField(
        _("Content"),
        validators=[
            DataRequired(message=_("You cannot post a reply without content."))
        ],
    )

    track_topic = BooleanField(
        _("Track this topic"), default=False, validators=[Optional()]
    )

    submit = SubmitField(_("Post topic"))

    def save(self, user, forum):
        topic = Topic(title=self.title.data, content=self.content.data)

        if self.track_topic.data:
            user.track_topic(topic)
        else:
            user.untrack_topic(topic)

        current_app.pluggy.hook.flaskbb_form_topic_save(form=self, topic=topic)
        return topic.save(user=user, forum=forum)


class NewTopicForm(TopicForm):
    pass


class EditTopicForm(TopicForm):

    submit = SubmitField(_("Save topic"))

    def __init__(self, *args, **kwargs):
        self.topic = kwargs.get("obj").topic
        TopicForm.__init__(self, *args, **kwargs)

    def populate_obj(self, *objs):
        """
        Populates the attributes of the passed `obj`s with data from the
        form's fields. This is especially useful to populate the topic and
        post objects at the same time.
        """
        for obj in objs:
            super(EditTopicForm, self).populate_obj(obj)

    def save(self, user, forum):
        if self.track_topic.data:
            user.track_topic(self.topic)
        else:
            user.untrack_topic(self.topic)

        if (
            self.topic.last_post_id == forum.last_post_id
            and self.title.data != forum.last_post_title
        ):
            forum.last_post_title = self.title.data

        self.topic.first_post.date_modified = time_utcnow()
        self.topic.first_post.modified_by = user.display_name
        self.topic.first_post.modified_by_user_id = user.id

        current_app.pluggy.hook.flaskbb_form_topic_save(
            form=self, topic=self.topic
        )
        return self.topic.save(user=user, forum=forum)


class ReportForm(FlaskForm):
    reason = TextAreaField(
        _("Reason"),
        validators=[
            DataRequired(
                message=_("What is the reason for reporting this post?")
            )
        ],
    )

    submit = SubmitField(_("Report post"))

    def save(self, user, post):
        report = Report(reason=self.reason.data)
        return report.save(post=post, user=user)


class UserSearchForm(FlaskForm):
    search_type = SelectField(
        _("Search by"),
        choices=[
            ("text", _("Username / display name")),
            ("primary_group", _("Primary group")),
            ("secondary_group", _("Secondary group")),
            ("discord", _("Discord ID / name")),
        ],
        default="text",
    )
    search_query = StringField(
        _("Search"), validators=[DataRequired(), Length(min=3, max=50)]
    )

    submit = SubmitField(_("Search"))

    def get_results(self):
        query = self.search_query.data
        pattern = "%{}%".format(query)
        if self.search_type.data == "primary_group":
            return User.query.join(User.primary_group).filter(Group.name.like(pattern))
        if self.search_type.data == "secondary_group":
            return User.query.filter(User.secondary_groups.any(Group.name.like(pattern)))
        if self.search_type.data == "discord":
            discord_ids = []
            try:
                from flaskbb.extensions import db_hub
                from hub.models import DiscordUser
                discord_ids = [
                    item[0] for item in
                    db_hub.session.query(DiscordUser.id)
                    .filter(or_(DiscordUser.id.like(pattern), DiscordUser.nickname.like(pattern)))
                    .limit(500)
                    .all()
                ]
            except Exception:
                logger.exception("Discord display-name lookup failed")
            return User.query.filter(or_(User.discord.like(pattern), User.discord.in_(discord_ids)))
        return User.query.whooshee_search(query)


class SearchPageForm(FlaskForm):
    search_query = StringField(
        _("Criteria"), validators=[DataRequired(), Length(min=3, max=50)]
    )

    search_types = SelectMultipleField(
        _("Content"),
        validators=[DataRequired()],
        choices=[
            ("post", _("Post")),
            ("topic", _("Topic")),
            ("forum", _("Forum")),
            ("user", _("Users")),
        ],
    )

    submit = SubmitField(_("Search"))

    def get_results(self):
        # Because the DB is not yet initialized when this form is loaded,
        # the query objects cannot be instantiated in the class itself
        search_actions = {
            "post": Post.query.whooshee_search,
            "topic": Topic.query.whooshee_search,
            "forum": Forum.query.whooshee_search,
            "user": User.query.whooshee_search,
        }

        query = self.search_query.data
        types = self.search_types.data
        results = {}

        for search_type in search_actions.keys():
            if search_type in types:
                results[search_type] = search_actions[search_type](query)

        return results
