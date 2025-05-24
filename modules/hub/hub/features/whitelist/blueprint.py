from flask import Blueprint
from flaskbb.utils.helpers import register_view
from .views import *

whitelist = Blueprint("whitelist", __name__, template_folder="templates")

register_view(
    whitelist,
    routes=["/<server>"],
    view_func=WhitelistView.as_view("server_whitelist")
)

register_view(
    whitelist,
    routes=["/respond"],
    view_func=WhitelistRespondView.as_view("whitelist_respond")
)
register_view(
    whitelist,
    routes=["/remove"],
    view_func=WhitelistRemoveView.as_view("whitelist_remove")
)