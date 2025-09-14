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

register_view(
    whitelist,
    routes=["/<server>/jobs"],
    view_func=JobWhitelistView.as_view("server_job_whitelist")
)

register_view(
    whitelist,
    routes=["/jobs/respond"],
    view_func=JobWhitelistRespondView.as_view("job_whitelist_respond")
)
register_view(
    whitelist,
    routes=["/jobs/remove"],
    view_func=JobWhitelistDeleteView.as_view("job_whitelist_remove")
)
