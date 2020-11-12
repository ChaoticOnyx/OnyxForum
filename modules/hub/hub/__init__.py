# -*- coding: utf-8 -*-
import os

from pluggy import HookimplMarker

from flaskbb.utils.helpers import render_template

from .views import hub
from .permissions import can_access_hub

__version__ = "1.0.0"
SETTINGS = None


hookimpl = HookimplMarker("flaskbb")


@hookimpl
def flaskbb_load_migrations():
    return os.path.join(os.path.dirname(__file__), "migrations")


@hookimpl
def flaskbb_load_translations():
    return os.path.join(os.path.dirname(__file__), "translations")


@hookimpl
def flaskbb_load_blueprints(app):
    app.register_blueprint(
        hub, url_prefix=app.config.get("PLUGIN_HUB_URL_PREFIX", "/hub")
    )


@hookimpl
def flaskbb_tpl_navigation_before():
    return render_template("hub/navigation_snippet.html")


@hookimpl
def flaskbb_jinja_directives(app):
    app.jinja_env.filters["can_access_hub"] = can_access_hub
