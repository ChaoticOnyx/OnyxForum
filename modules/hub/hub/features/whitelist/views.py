from flask import request, current_app, jsonify
from flask.views import MethodView
from flaskbb.utils.requirements import IsAdmin
from flaskbb.utils.helpers import FlashAndRedirect
from flaskbb.utils.helpers import render_template
from flask_login import current_user
from flaskbb.extensions import allows, db
from sqlalchemy import and_, or_, func, not_

import asyncio
import datetime

from ...servers_config import ServerDescriptor
from ...gameserver_models import game_models
from .whitelist import WhitelistApplication, fetch_whitelist_applications, respond_to_application, remove_whitelist_emoji
from .jobs import WHITEJOBS

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
                fetch_whitelist_applications(server, guild_id, int(server.whitelist_channel))
        except Exception as e:
            current_app.logger.warning(f"Не удалось запустить фоновую задачу Discord: {e}")

        jobs_is_empty = or_(
            WhitelistApplication.jobs.is_(None),
            func.lower(func.trim(WhitelistApplication.jobs)) == 'null',
            func.length(func.trim(WhitelistApplication.jobs)) == 0,
            WhitelistApplication.jobs.op('REGEXP')(r'^\s*\[\s*\]\s*$')
        )
        jobs_is_empty = or_(
            WhitelistApplication.jobs.is_(None),
            func.lower(func.trim(WhitelistApplication.jobs)) == 'null',
            func.length(func.trim(WhitelistApplication.jobs)) == 0,
            WhitelistApplication.jobs.op('REGEXP')(r'^\s*\[\s*\]\s*$')
        )

        accepted = WhitelistApplication.query.filter(
            WhitelistApplication.server_id == server.id,
            WhitelistApplication.status == 'accepted',
            jobs_is_empty
        ).order_by(WhitelistApplication.ckey.asc()).all()

        pending_query = WhitelistApplication.query.filter(
            WhitelistApplication.server_id == server.id,
            WhitelistApplication.status == 'pending',
            jobs_is_empty
        ).order_by(WhitelistApplication.created_at.desc())

        pending = pending_query.paginate(page=page, per_page=9, error_out=False)

        return render_template(
            "features/whitelist/whitelist.html",
            guild_id=guild_id,
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


# views.py (фрагмент)
from flask import request, current_app, jsonify
from flask.views import MethodView
from flaskbb.utils.requirements import IsAdmin
from flaskbb.utils.helpers import FlashAndRedirect, render_template
from flaskbb.extensions import allows, db
import datetime

from ...servers_config import ServerDescriptor
from ...gameserver_models import game_models
from .whitelist import WhitelistApplication, respond_to_application
from .jobs import WHITEJOBS


class JobWhitelistView(MethodView):
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

        # Запустить Discord-таску безопасно в фоне (не блокируя Flask/Gunicorn)
        try:
            guild_id = int(current_app.config["COMMUNITY_GUILD_ID"])
            with current_app.app_context():
                fetch_whitelist_applications(server, guild_id, int(server.job_whitelist_channel))
        except Exception as e:
            current_app.logger.warning(f"Не удалось запустить фоновую задачу Discord: {e}")

        
        jobs_is_not_empty = and_(
            WhitelistApplication.jobs.isnot(None),
            func.json_valid(WhitelistApplication.jobs) == 1,
            func.json_type(WhitelistApplication.jobs) == 'ARRAY',
            func.json_length(WhitelistApplication.jobs) > 0
        )
        
        accepted = (WhitelistApplication.query
            .filter(
                and_(
                    WhitelistApplication.server_id == server.id,
                    WhitelistApplication.status == 'accepted',
                    jobs_is_not_empty
                )
            )
            .order_by(WhitelistApplication.created_at.desc())
            .all()
        )

        # Ожидающие — с пагинацией (как в обычном WL)
        page = request.args.get('page', 1, type=int)

        pending = (WhitelistApplication.query
            .filter(
                and_(
                    WhitelistApplication.server_id == server.id,
                    WhitelistApplication.status == 'pending',
                    jobs_is_not_empty
                )
            )
            .order_by(WhitelistApplication.created_at.desc())
            .paginate(page=page, per_page=12, error_out=False)
        )

        return render_template(
            "features/whitelist/job_list.html",
            guild_id=guild_id,
            server=server,
            server_id=server.id,
            accepted=accepted,
            pending=pending,
        )


class JobWhitelistRespondView(MethodView):
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect("Нет доступа", "danger", "forum.index")
        )
    ]

    def post(self):
        """
        Пэйлоад:
        { "id": "<application_id>", "server_id": "<server_id>", "action": "accept" | "reject" }
        """
        data = request.get_json(silent=True) or {}
        app_id = data.get("id") or data.get("application_id")
        server_id = data.get("server_id")
        action = data.get("action")

        if action not in ("accept", "reject"):
            return jsonify({"ok": False, "error": "Invalid action"}), 400
        if not app_id or not server_id:
            return jsonify({"ok": False, "error": "Missing id or server_id"}), 400

        app = WhitelistApplication.query.get_or_404(app_id)

        # принадлежность серверу
        if str(app.server_id) != str(server_id):
            return jsonify({"ok": False, "error": "Application-server mismatch"}), 404

        if action == "accept":
            jobs = app.jobs or []
            unknown = app.jobs_unknown or []

            # Принимаем только валидные заявки: есть jobs, нет unknown, jobs_valid == True
            is_valid = bool(app.jobs_valid) and bool(jobs) and not unknown
            if not is_valid:
                return jsonify({
                    "ok": False,
                    "error": "Jobs invalid; cannot accept",
                    "details": {"jobs_valid": app.jobs_valid, "jobs": jobs, "unknown": unknown}
                }), 400

            # Сохранение в ErroJobWhitelist по одной записи на каждую профу (каноническое имя)
            erro_job_whitelist_model = game_models[server_id]["ErroJobWhitelist"]
            created = 0
            for job in jobs:
                # строго канонизированный формат
                if job not in WHITEJOBS:
                    return jsonify({"ok": False, "error": f"Non-canonical job in payload: {job}"}), 400

                exists = erro_job_whitelist_model.query.filter_by(ckey=app.ckey, job=job).first()
                if not exists:
                    entry = erro_job_whitelist_model(
                        ckey=app.ckey,
                        text=app.message_text,
                        job=job,
                        added_at=datetime.datetime.utcnow()
                    )
                    db.session.add(entry)
                    created += 1

            app.status = "accepted"
            app.jobs_valid_reason = None
            db.session.commit()

        else:
            app.status = "rejected"
            db.session.commit()

        # Discord-ответ — как в обычном WL
        guild_id = int(current_app.config["COMMUNITY_GUILD_ID"])
        respond_to_application(app, action, guild_id)

        return jsonify({"ok": True, "id": app.id, "status": app.status})

class JobWhitelistDeleteView(MethodView):
    """
    Удаление всех записей из ErroJobWhitelist, соответствующих принятой заявке.
    Ожидаемый JSON:
      { "server_id": "<server_id>", "application_id": "<application_id>" }
    Дополнительный alias: "app_id".
    Поддерживает HTTP DELETE и POST (для клиентов без DELETE).
    """
    decorators = [
        allows.requires(
            IsAdmin,
            on_fail=FlashAndRedirect("Нет доступа", "danger", "forum.index")
        )
    ]

    def _perform_delete_by_application(self, data):
        server_id = data.get("server_id")
        application_id = data.get("application_id") or data.get("app_id")

        if not server_id:
            return jsonify({"ok": False, "error": "Missing server_id"}), 400
        if not application_id:
            return jsonify({"ok": False, "error": "Missing application_id"}), 400

        # Проверка сервера
        server = ServerDescriptor.query.get(server_id)
        if not server:
            return jsonify({"ok": False, "error": "Server not found"}), 404

        # Модель ErroJobWhitelist для данного сервера
        erro_job_whitelist_model = game_models.get(str(server_id), {}).get("ErroJobWhitelist")
        if erro_job_whitelist_model is None:
            return jsonify({"ok": False, "error": "ErroJobWhitelist model not available for this server"}), 500

        # Получаем заявку
        app = WhitelistApplication.query.get(application_id)
        if not app:
            return jsonify({"ok": False, "error": "WhitelistApplication not found"}), 404

        # Проверка принадлежности серверу
        if str(app.server_id) != str(server_id):
            return jsonify({"ok": False, "error": "Application-server mismatch"}), 404

        # Проверка, что заявка действительно принята
        if app.status != "accepted":
            return jsonify({"ok": False, "error": "Application is not accepted"}), 400

        jobs = app.jobs or []
        if not jobs:
            return jsonify({"ok": False, "error": "Application has no jobs to delete"}), 400

        
        deleted_total = 0
        try:
            # Удаляем записи по каждому job; delete() — эффективно
            for job in jobs:
                q = erro_job_whitelist_model.query.filter_by(ckey=app.ckey, job=job)
                deleted = q.delete(synchronize_session=False)
                deleted_total += deleted

            db.session.commit()
            current_app.logger.info(
                f"Deleted {deleted_total} ErroJobWhitelist entries for application {application_id} (ckey={app.ckey}) on server={server_id}"
            )

            if app.status != "accepted":
                return jsonify({"error": "Not accepted"}), 400
            
            guild_id = int(current_app.config["COMMUNITY_GUILD_ID"])
            with current_app.app_context():
                remove_whitelist_emoji(app, guild_id)
                
            db.session.delete(app)
            db.session.commit()
            return jsonify({"ok": True, "deleted_count": deleted_total}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(
                f"Failed to delete ErroJobWhitelist entries for application {application_id} on server={server_id}: {e}"
            )
            return jsonify({"ok": False, "error": "Failed to delete entries"}), 500

    def delete(self):
        data = request.get_json(silent=True) or {}
        return self._perform_delete_by_application(data)

    # Поддержка POST (для клиентов/форм, которые не могут посылать DELETE)
    def post(self):
        data = request.get_json(silent=True) or {}
        return self._perform_delete_by_application(data)
