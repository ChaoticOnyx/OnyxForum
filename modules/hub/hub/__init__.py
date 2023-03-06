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
from hub.github import create_github_api
from .features.donations.utils import render_donations_label
from .features.donations.blueprint import donations
from .features.donations.qiwi_hook import register_webhooks_service
from .utils import get_byond_ckey, configs_path

from hub.features.development import status_monitor

__version__ = "1.0.0"
SETTINGS = None


hookimpl = HookimplMarker("flaskbb")


@hookimpl
def flaskbb_extensions(app):
    app.config.from_pyfile(configs_path + "/hub.cfg")
    app.config.from_pyfile(configs_path + "/patron_tiers.cfg")
    app.githubApi = create_github_api()


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
