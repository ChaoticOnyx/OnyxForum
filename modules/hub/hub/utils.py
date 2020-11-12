
from werkzeug.local import LocalProxy
from flask import request, current_app


@LocalProxy
def hub_current_server():
    if "server" not in request.args:
        return

    server_id = request.args["server"]

    servers = current_app.config["BYOND_SERVERS"]
    for server in servers:
        if server.id == server_id:
            return server