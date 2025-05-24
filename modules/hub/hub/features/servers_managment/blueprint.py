from flask import Blueprint
from flaskbb.utils.helpers import register_view
from .views import *

servers_managment = Blueprint("servers_managment", __name__, template_folder="templates")

register_view(
    servers_managment,
    routes=["/servers"],
    view_func=ServerListView.as_view("list_servers")
)

register_view(
    servers_managment,
    routes=["/servers/add", "/servers/edit/<server_id>"],
    view_func=ServerManagementView.as_view("manage_server")
)
