from flask import request, current_app, jsonify
from flask.views import MethodView
from flaskbb.utils.requirements import IsAdmin
from flaskbb.utils.helpers import FlashAndRedirect
from flaskbb.utils.helpers import render_template
from flask_login import current_user
from flaskbb.extensions import allows, db

import asyncio
import datetime

from ...servers_config import ServerDescriptor
from ...gameserver_models import game_models
from .whitelist import WhitelistApplication, fetch_whitelist_applications, respond_to_application, remove_whitelist_emoji


class WhitelistView(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect(
                message="Вы не можете просматривать вайтлист",
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self, server):
        server = ServerDescriptor.query.get_or_404(server)
        page = request.args.get("page", 1, type=int)

        # Запустить Discord-таску безопасно в фоне (не блокируя Flask/Gunicorn)
        try:
            guild_id = int(current_app.config["COMMUNITY_GUILD_ID"])
            with current_app.app_context():
                fetch_whitelist_applications(server, guild_id)
        except Exception as e:
            current_app.logger.warning(f"Не удалось запустить фоновую задачу Discord: {e}")


        accepted = WhitelistApplication.query.filter_by(
            server_id=server.id,
            status='accepted'
        ).order_by(WhitelistApplication.ckey.asc()).all()

        pending_query = WhitelistApplication.query.filter_by(
            server_id=server.id,
            status='pending'
        ).order_by(WhitelistApplication.created_at.desc())

        pending = pending_query.paginate(page=page, per_page=9, error_out=False)

        return render_template(
            "features/whitelist/whitelist.html",
            server=server,
            accepted=accepted,
            pending=pending
        )


class WhitelistRespondView(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect("Нет доступа", "danger", "forum.index")
        )
    ]

    def post(self):
        data = request.get_json()
        app_id = data.get("id")
        action = data.get("action")  # "accept" / "reject"

        if action not in ("accept", "reject"):
            return jsonify({"error": "Invalid action"}), 400

        app = WhitelistApplication.query.get_or_404(app_id)
        app.status = "accepted" if action == "accept" else "rejected"
        db.session.commit()

        # Если заявка принята — заносим в erro_whitelist соответствующего сервера
        if action == "accept":
            server_id = app.server_id
            erro_whitelist_model = game_models[server_id]["ErroWhitelist"]

            exists = erro_whitelist_model.query.filter_by(ckey=app.ckey).first()

            if not exists:
                new_entry = erro_whitelist_model(
                    ckey=app.ckey,
                    text=app.message_text,
                    added_at=datetime.datetime.utcnow()
                )
                db.session.add(new_entry)
                db.session.commit()
        
        guild_id = int(current_app.config["COMMUNITY_GUILD_ID"])
        with current_app.app_context():
            respond_to_application(app, action, guild_id)

        return jsonify({"success": True})



class WhitelistRemoveView(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect("Нет доступа", "danger", "forum.index")
        )
    ]

    def post(self):
        data = request.get_json()
        app_id = data.get("id")

        app = WhitelistApplication.query.get_or_404(app_id)

        if app.status != "accepted":
            return jsonify({"error": "Not accepted"}), 400
        
        guild_id = int(current_app.config["COMMUNITY_GUILD_ID"])
        with current_app.app_context():
            remove_whitelist_emoji(app, guild_id)

        # также удалим из erro_whitelist
        server_id = app.server_id
        erro_whitelist_model = game_models[server_id]["ErroWhitelist"]

        erro_whitelist_model.query.filter_by(ckey=app.ckey).delete()
        db.session.delete(app)
        db.session.commit()

        return jsonify({"success": True})
