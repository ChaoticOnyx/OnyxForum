from flask import Blueprint
from pluggy import HookimplMarker

from flaskbb.utils.helpers import (register_view)

from .view import IndexView

hookimpl = HookimplMarker("flaskbb")

@hookimpl
def flaskbb_load_blueprints(app):
    index = Blueprint("index", __name__)
    register_view(index, routes=["/index"], view_func=IndexView.as_view("index"))
    app.register_blueprint(index)
