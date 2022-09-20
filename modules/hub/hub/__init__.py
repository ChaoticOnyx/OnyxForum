# -*- coding: utf-8 -*-
import os

from pluggy import HookimplMarker
import discord
import traceback

from flaskbb.utils.helpers import render_template
from flask import current_app, url_for

from flask_login import current_user

from .blueprint import hub
from .permissions import can_access_hub
from hub.features.karma.render import render_karma, render_post_rating
from hub.features.community_rating.render import render_community_rating
from .features.donations.utils import render_donations_label
from .features.donations.blueprint import donations
from .features.donations.qiwi_hook import register_webhooks_service
from .utils import get_byond_ckey, configs_path

__version__ = "1.0.0"
SETTINGS = None


hookimpl = HookimplMarker("flaskbb")


@hookimpl
def flaskbb_extensions(app):
    app.config.from_pyfile(configs_path + "/hub.cfg")


@hookimpl
def flaskbb_load_migrations():
    return os.path.join(os.path.dirname(__file__), "migrations")


@hookimpl
def flaskbb_load_translations():
    return os.path.join(os.path.dirname(__file__), "translations")


@hookimpl
def flaskbb_load_blueprints(app):
    app.register_blueprint(hub, url_prefix="/hub")
    app.register_blueprint(donations, url_prefix="/donations")

    app.before_first_request(lambda: register_webhooks_service(app))


@hookimpl
def flaskbb_tpl_navigation_before():
    return render_template("hub/navigation_snippet.html")


@hookimpl
def flaskbb_jinja_directives(app):
    app.jinja_env.filters["can_access_hub"] = can_access_hub

@hookimpl
def flaskbb_event_topic_save_after(topic, is_new):
    if "SENAT_FORUM_ID" not in current_app.config or "SENAT_JOURNAL_WEBHOOK" not in current_app.config:
        print("SENAT_JOURNAL isn't configured")
        return

    if not is_new:
        return

    if topic.forum_id == current_app.config["SENAT_FORUM_ID"]:
        try:
            webhook = discord.Webhook.from_url(current_app.config["SENAT_JOURNAL_WEBHOOK"], adapter=discord.RequestsWebhookAdapter())

            desc = topic.first_post.content
            desc = (desc[:2000] + "\n...") if len(desc) > 2000 else desc

            url = url_for("forum.view_topic", topic_id=topic.id, slug=topic.slug, _external=True)
            embed = discord.Embed(title=topic.title, description=desc, url=url)
            embed.add_field(name="Author:", value=topic.user.display_name)

            webhook.send(embed=embed)
        except Exception:
            print(traceback.format_exc())

@hookimpl
def flaskbb_event_post_save_after(post, is_new):
    if "SENAT_FORUM_ID" not in current_app.config or "SENAT_JOURNAL_WEBHOOK" not in current_app.config:
        print("SENAT_JOURNAL isn't configured")
        return

    if not is_new or not post.topic.first_post_id:
        return

    if post.topic.forum_id == current_app.config["SENAT_FORUM_ID"]:
        try:
            webhook = discord.Webhook.from_url(current_app.config["SENAT_JOURNAL_WEBHOOK"], adapter=discord.RequestsWebhookAdapter())

            desc = post.content
            desc = (desc[:2000] + "\n...") if len(desc) > 2000 else desc

            url = url_for("forum.view_post", post_id=post.id,  _external=True)
            title = post.user.display_name + " answered to \"" + post.topic.title + "\""
            embed = discord.Embed(title=title, description=desc, url=url)

            webhook.send(embed=embed)
        except Exception:
            print(traceback.format_exc())


@hookimpl
def flaskbb_tpl_post_menu_before(post):
    return render_post_rating(post)


@hookimpl
def flaskbb_tpl_post_author_info_after(user, post):
    return (render_karma(user) + render_community_rating(user))


@hookimpl
def flaskbb_tpl_profile_sidebar_stats(user):
    return (render_karma(user) + render_community_rating(user))


@hookimpl
def flaskbb_tpl_profile_contacts(user):
    return render_template(
        "features/profile_contacts.html",
        ckey=get_byond_ckey(user),
        ckey_hidden=(get_byond_ckey(current_user) is None))


@hookimpl
def flaskbb_tpl_user_nav_loggedin_before():
    return render_donations_label(current_user)
