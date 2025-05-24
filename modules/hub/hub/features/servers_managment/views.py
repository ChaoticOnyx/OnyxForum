from flask import request, flash, redirect, url_for
from flaskbb.utils.helpers import render_template
from flask.views import MethodView
from flaskbb.utils.helpers import register_view
from flaskbb.extensions import db
from flaskbb.utils.requirements import IsAdmin
from flaskbb.utils.helpers import FlashAndRedirect
from flaskbb.extensions import allows
from flask_login import current_user
import json

from .forms import ServerForm
from ...servers_config import ServerDescriptor, ServerAdditionalLink
from ...gameserver_models import init_game_models


class ServerListView(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message="You are not allowed to access this page",
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self):
        servers = ServerDescriptor.query.order_by(ServerDescriptor.name).all()
        return render_template(
            "features/servers_managment/list.html",
            servers=servers
        )


class ServerManagementView(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message="You are not allowed to access this page",
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self, server_id=None):
        form = ServerForm()
        server = ServerDescriptor.query.get(server_id) if server_id else None
        return render_template(
            "features/servers_managment/edit.html",
            server=server,
            form=form
        )

    def post(self, server_id=None):
        form_data = request.form.to_dict()

        server = ServerDescriptor.query.get(server_id) if server_id else ServerDescriptor()

        server.id = form_data.get("id") if not server_id else server.id
        server.name = form_data.get("name")
        server.icon = form_data.get("icon")
        server.description = form_data.get("description")
        server.port = int(form_data.get("port"))
        server.service_name = form_data.get("service_name")
        server.path = form_data.get("path")
        server.branch_name = form_data.get("branch_name")
        server.dream_maker_binary = form_data.get("dream_maker_binary")
        server.dme_name = form_data.get("dme_name")
        server.configs_path = form_data.get("configs_path")
        server.configs_exclude = [x.strip() for x in form_data.get("configs_exclude", "").split(",") if x.strip()]
        server.logs_path = form_data.get("logs_path")

        server.discord_full_access_titles = [x.strip() for x in form_data.get("discord_full_access_titles", "").split(",") if x.strip()]
        server.discord_base_access_titles = [x.strip() for x in form_data.get("discord_base_access_titles", "").split(",") if x.strip()]
        server.discord_role_to_group = json.loads(form_data.get("discord_role_to_group", "{}"))
        server.whitelist_channel = form_data.get("whitelist_channel")
        server.whitelist_role = form_data.get("whitelist_role")

        # Обработка ссылок
        server.links.clear()
        for what, text, href in zip(
            request.form.getlist("link_what"),
            request.form.getlist("link_text"),
            request.form.getlist("link_href")
        ):
            server.links.append(ServerAdditionalLink(what=what, text=text, href=href))
        db.session.add(server)
        db.session.commit()

        flash("Сервер сохранён", "success")
        init_game_models()
        return redirect(url_for("servers_managment.manage_server", server_id=server.id))