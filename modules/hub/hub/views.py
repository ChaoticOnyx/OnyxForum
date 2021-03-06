import enum
import os
import attr
import re
from collections import OrderedDict
from typing import List

from flask import Blueprint, redirect, request, url_for, current_app, abort, flash, send_file
from flask_babelplus import gettext as _
from flask_allows import Permission
from flask_login import current_user
from flask_sqlalchemy import Pagination
from flask.views import MethodView
from flaskbb.utils.helpers import FlashAndRedirect
from flaskbb.display.navigation import NavigationLink
from flaskbb.extensions import allows, db
from flaskbb.user.models import User, Group

from hub.forms import ConfigEditForm, BanSearchForm
from hub.permissions import CanAccessServerHub, CanAccessServerHubAdditional, CanAccessServerHubManagement
from hub.models import DiscordUser, DiscordUserRole, DiscordRole, HubLog
from hub.utils import hub_current_server
from hub.gameserver_models import game_models, ErroBan

from flaskbb.utils.helpers import (
    format_quote,
    real,
    register_view,
    render_template,
    time_utcnow,
)

hub = Blueprint("hub", __name__, template_folder="templates")


class FlashAndRedirectToHub(object):
    def __init__(self, message, level):
        self._message = message
        self._level = level

    def __call__(self, *a, **k):
        flash(self._message, self._level)
        return redirect(url_for("hub.index", server=hub_current_server.id))


def LogAction(user, message):
    log_entry = HubLog()
    log_entry.user = user
    log_entry.message = message
    log_entry.server_id = hub_current_server.id
    log_entry.save()


class ServerControl(MethodView):
    decorators = [
        allows.requires(
            CanAccessServerHubAdditional(),
            on_fail=FlashAndRedirectToHub(
                message=_("You are not allowed to use server controls"),
                level="danger"
            )
        )
    ]
    _action = "made unknown action with"

    def _report(self, user):
        LogAction(user, self._action + " server")


class StartServer(ServerControl):
    _action = "started"

    def get(self):
        if not hub_current_server:
            abort(404)

        command = "sudo systemctl start " + hub_current_server.service_name
        os.system(command)
        self._report(current_user)
        return redirect(url_for("hub.index", server=hub_current_server.id))


class StopServer(ServerControl):
    _action = "stopped"

    def get(self):
        if not hub_current_server:
            abort(404)

        command = "sudo systemctl stop " + hub_current_server.service_name
        os.system(command)
        self._report(current_user)
        return redirect(url_for("hub.index", server=hub_current_server.id))


class RestartServer(ServerControl):
    _action = "restarted"

    def get(self):
        if not hub_current_server:
            abort(404)

        command = "sudo systemctl restart " + hub_current_server.service_name
        os.system(command)
        self._report(current_user)
        return redirect(url_for("hub.index", server=hub_current_server.id))


class Hub(MethodView):
    decorators = [
        allows.requires(
            CanAccessServerHub(),
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access the hub"),
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def __get_actions(self, server_status):
        actions = []

        actions.append(
            NavigationLink(
                endpoint="hub.hublogs",
                name=_("Logs"),
                icon="fa fa-clock-o",
                urlforkwargs={"server": hub_current_server.id},
            ))

        if Permission(CanAccessServerHubAdditional()):
            if server_status == "online":
                actions.append(
                    NavigationLink(
                        endpoint="hub.stop",
                        name=_("Stop"),
                        icon="fa fa-power-off",
                        urlforkwargs={"server": hub_current_server.id},
                    ))

                actions.append(
                    NavigationLink(
                        endpoint="hub.restart",
                        name=_("Restart"),
                        icon="fa fa-undo",
                        urlforkwargs={"server": hub_current_server.id},
                    ))

            else:
                actions.append(
                    NavigationLink(
                        endpoint="hub.start",
                        name=_("Start"),
                        icon="fa fa-power-off",
                        urlforkwargs={"server": hub_current_server.id},
                    ))

        if Permission(CanAccessServerHubAdditional()):
            actions.append(
                NavigationLink(
                    endpoint="hub.configs",
                    name=_("Configs"),
                    icon="fa fa-wrench",
                    urlforkwargs={"server": hub_current_server.id},
                ))

        actions.append(
            NavigationLink(
                endpoint="hub.gamelogs",
                name=_("Game Logs"),
                icon="fa fa-file",
                urlforkwargs={"server": hub_current_server.id},
            ))

        actions.append(
            NavigationLink(
                endpoint="hub.bans",
                name=_("Bans"),
                icon="fa fa-wheelchair-alt",
                urlforkwargs={"server": hub_current_server.id},
            )
        )

        if Permission(CanAccessServerHubManagement()):
            actions.append(
                NavigationLink(
                    endpoint="hub.team",
                    name=_("Team"),
                    icon="fa fa-group",
                    urlforkwargs={"server": hub_current_server.id},
                ))

        return actions

    def get_args(self):
        command = "systemctl status " + hub_current_server.service_name
        status = os.system(command)
        if not status:
            status = "online"
        else:
            status = "offline"

        return {
            "server": hub_current_server,
            "server_status": status,
            "actions": self.__get_actions(server_status=status)
        }

    def get(self):
        return redirect(url_for("hub.hublogs", server=hub_current_server.id))


class HubLogView(Hub):
    def get(self):
        logs = db.session.query(HubLog)\
            .filter(HubLog.server_id == hub_current_server.id)\
            .order_by(HubLog.id.desc())\
            .limit(100)\
            .all()
        return render_template("hub/hublogs.html", **self.get_args(), logs=logs)


class ConfigsView(Hub):
    decorators = [
        allows.requires(
            CanAccessServerHubAdditional(),
            on_fail=FlashAndRedirect(
                message=_("You are not allowed to access the hub"),
                level="danger",
                endpoint="forum.index"
            )
        )
    ]

    def get(self):
        server_id = request.args["server"]
        servers = current_app.config["BYOND_SERVERS"]

        for server in servers:
            if server.id == server_id:
                config_folder_entries = [os.path.join(server.configs_path, f) for f in os.listdir(server.configs_path)]
                config_files = [f for f in config_folder_entries if os.path.isfile(f)]

                config_files_names = [os.path.split(f)[1] for f in config_files]
                config_files_names = [f for f in config_files_names if f not in server.configs_exclude]
                config_files_names.sort()

                return render_template("hub/configs.html", **self.get_args(), configs=config_files_names)

        return render_template("hub/configs.html", **self.get_args())


class ConfigEditView(Hub):
    decorators = [
        allows.requires(
            CanAccessServerHubAdditional(),
            on_fail=FlashAndRedirectToHub(
                message=_("You are not allowed to access the hub"),
                level="danger"
            )
        )
    ]

    def get(self):
        server_id = request.args["server"]
        config_name = request.args["config_name"]

        servers = current_app.config["BYOND_SERVERS"]
        server = None

        for srv in servers:
            if srv.id == server_id:
                server = srv
                break

        if server is None:
            abort(404)

        form = self.form()
        with open(os.path.join(server.configs_path, config_name)) as f:
            form.content.data = f.read()

        return render_template("hub/config_edit.html", **self.get_args(), config_name=config_name, form=form)

    def post(self):
        server_id = request.args["server"]
        config_name = request.args["config_name"]

        servers = current_app.config["BYOND_SERVERS"]
        server = None

        for srv in servers:
            if srv.id == server_id:
                server = srv
                break

        if server is None:
            abort(404)

        form = self.form()
        if form.validate_on_submit():
            with open(os.path.join(server.configs_path, config_name), "w") as f:
                f.write(form.content.data)
                LogAction(current_user, 'updated server\'s config file "{}"'.format(config_name))
                flash("Configuration file was saved!")

        return render_template("hub/config_edit.html", **self.get_args(), config_name=config_name, form=form)

    def form(self):
        return ConfigEditForm()


class LogsView(Hub):
    # returns list [{"name": name, "url": url)]
    @staticmethod
    def get_title_parent_folders(server_id, root_path, current_path):
        folders = []

        path = current_path
        while root_path != path:
            name = os.path.split(path)[1]
            url = url_for("hub.gamelogs", server=server_id, path=os.path.relpath(path, root_path))
            folders.insert(0, {"name": name, "url": url})
            path = os.path.dirname(path)

        name = "logs"
        url = url_for("hub.gamelogs", server=server_id)
        folders.insert(0, {"name": name, "url": url})

        if len(folders):
            folders[-1]["url"] = None

        return folders

    def get(self, **kwargs):
        server_id = request.args["server"]
        path = None
        if "path" in request.args:
            path = request.args["path"]
        servers = current_app.config["BYOND_SERVERS"]

        server = None

        for srv in servers:
            if srv.id == server_id:
                server = srv
                break

        if server is None:
            abort(404)

        current_path = server.logs_path
        if path:
            current_path = os.path.realpath(os.path.join(current_path, path))
            if not current_path.startswith(server.logs_path + os.sep):
                abort(404)

        title_parent_folders = self.get_title_parent_folders(server_id, server.logs_path, current_path)

        logs_folder_entries = [os.path.join(current_path, f) for f in os.listdir(current_path)]
        entries = {}

        for entry in logs_folder_entries:
            entry_pure = os.path.split(entry)[1]
            if os.path.isfile(entry):
                entries[entry_pure] = url_for("hub.download_gamelog", server=server_id, path=os.path.relpath(entry, server.logs_path))
            else:
                lll = os.path.relpath(entry, server.logs_path)
                entries[entry_pure] = url_for("hub.gamelogs", server=server_id, path=os.path.relpath(entry, server.logs_path))

        return render_template(
            "hub/gamelogs.html",
            **self.get_args(),
            entries=sorted(entries.items()),
            title_parent_folders=title_parent_folders
        )


class LogDownload(Hub):
    def get(self):
        server_id = request.args["server"]
        path = request.args["path"]
        servers = current_app.config["BYOND_SERVERS"]

        assert path
        assert server_id

        server = None

        for srv in servers:
            if srv.id == server_id:
                server = srv
                break

        if server is None:
            abort(404)

        file_path = os.path.join(server.logs_path, path)
        return send_file(file_path, as_attachment=True)


class TeamView(Hub):
    decorators = [
        allows.requires(
            CanAccessServerHubManagement(),
            on_fail=FlashAndRedirectToHub(
                message=_("You are not allowed to access the server team view"),
                level="danger"
            )
        )
    ]

    def __add_group_to_user(self, user_discord_id):
        roles = DiscordRole.query\
            .join(DiscordUserRole)\
            .join(DiscordUser)\
            .filter(DiscordUser.id == user_discord_id)\
            .all()

        user = User.query.filter(User.discord == user_discord_id).first()
        for role in roles:
            if role.id in hub_current_server.discord_role_to_group:
                group_id = hub_current_server.discord_role_to_group[role.id]
                group = Group.query.filter(Group.id == group_id).first()
                if not user:
                    discord_user = DiscordUser.query.filter(DiscordUser.id == user_discord_id).first()
                    assert discord_user
                    user = User(discord=user_discord_id, display_name=discord_user.pure_name, activated=True)
                    user.primary_group = group
                else:
                    last_group = user.primary_group
                    user.primary_group = group
                    user.add_to_group(last_group)

                user.save()
                LogAction(current_user, "added user {name} (discord: {discord_id}) to group {group}".format(
                    name=user.display_name,
                    discord_id=user_discord_id,
                    group=group.name
                ))
                flash("User {} was added to group {}".format(user.display_name, group.name))
                return True

        flash("Failed to find appropriate group for user {}".format(user.display_name), "danger")
        return False

    def __remove_group_from_user(self, user_discord_id):
        user = User.query.filter(User.discord == user_discord_id).first()
        assert user.primary_group.id in hub_current_server.discord_role_to_group.values()

        removed_group = user.primary_group

        secondary_groups = user.secondary_groups.all()
        if len(secondary_groups):
            user.primary_group = secondary_groups[0]
        else:
            user.primary_group = Group.get_member_group()
        user.save()
        LogAction(current_user, "removed user {name} (discord: {discord_id}) from group {group}".format(
            name=user.display_name,
            discord_id=user_discord_id,
            group=removed_group.name
        ))
        flash("User {} was removed from group {}".format(user.display_name, removed_group.name))

    def get(self):
        if "user_to_add" in request.args:
            self.__add_group_to_user(request.args["user_to_add"])
            return redirect(url_for("hub.team", server=hub_current_server.id))

        if "user_to_remove_group" in request.args:
            self.__remove_group_from_user(request.args["user_to_remove_group"])
            return redirect(url_for("hub.team", server=hub_current_server.id))

        @attr.s
        class TeamMember:
            id = attr.ib()
            username = attr.ib()
            group = attr.ib(default="")
            discord_role = attr.ib(default="")
            url = attr.ib(default="")
            remove_group_url = attr.ib(default="")

        members = []
        for user in User.query.all():
            if Permission(CanAccessServerHub(), identity=user):
                new_member = TeamMember(
                        id=user.discord,
                        username=user.display_name,
                        group=user.primary_group.name,
                        url=user.url)

                if user.primary_group.id in hub_current_server.discord_role_to_group.values():
                    new_member.remove_group_url = \
                        url_for("hub.team", server=hub_current_server.id, user_to_remove_group=user.discord)

                members.append(new_member)

        discord_users_with_pedalique_role = db.session.query(DiscordUser)\
            .join(DiscordUserRole)\
            .join(DiscordRole)\
            .filter(DiscordUserRole.role.in_(hub_current_server.discord_full_access_titles))\
            .distinct(DiscordUser.id)\
            .add_entity(DiscordRole)\
            .all()

        members_from_discord = []
        for discord_user, discord_role in discord_users_with_pedalique_role:
            found = False
            for member in members:
                if member.id == discord_user.id:
                    member.discord_role = discord_role.title
                    found = True
                    break
            if not found:
                members_from_discord.append(TeamMember(id=discord_user.id, username=discord_user.pure_name, discord_role=discord_role.title))

        return render_template(
            "hub/team.html",
            **self.get_args(),
            members=members + members_from_discord
        )


def bans_records_from_db_records(bans_records: List[ErroBan]):
    bans = list()
    for ban in bans_records:
        ban_record = ban.get_ban_record()

        description = ban_record.bantype
        if ban_record.bantype == "tempban" or ban_record.bantype == "job_tempban":
            description = str(int((ban_record.expiration_time - ban_record.bantime).total_seconds() / 60)) + "m"
        elif ban_record.bantype == "permaban" or ban_record.bantype == "job_permaban":
            description = "Permaban"

        if ban_record.bantype == "job_tempban" or ban_record.bantype == "job_permaban":
            description += ", Job: " + ban_record.role

        ban_record.desc = description

        bans.append(ban_record)

    return bans


class BansView(Hub):
    def get(self):
        page = request.args.get('page', 1, type=int)
        server_ban = game_models[hub_current_server.id]["ErroBan"]

        bans_records_page: Pagination = server_ban.query \
            .order_by(server_ban.id.desc()) \
            .paginate(page, 50)

        bans = bans_records_from_db_records(bans_records_page.items)

        form = BanSearchForm()
        return render_template("hub/bans.html", **self.get_args(), bans=bans, page=bans_records_page, form=form)

    def post(self):
        page = request.args.get('page', 1, type=int)
        form = BanSearchForm()

        server_ban = game_models[hub_current_server.id]["ErroBan"]
        query = server_ban.query \
            .order_by(server_ban.id.desc())

        if form.validate_on_submit() and form.searchText.data:
            if form.searchType.data == "Ckey":
                ckey = re.sub(r'[^\w\d]', '', form.searchText.data)
                query = query.filter(server_ban.ckey == ckey)
            elif form.searchType.data == "Admin":
                ckey = re.sub(r'[^\w\d]', '', form.searchText.data)
                query = query.filter(server_ban.a_ckey == ckey)
            elif form.searchType.data == "Reason":
                query = query.filter(server_ban.reason.contains(form.searchText.data))

        bans_records_page: Pagination = query.paginate(page, 50)
        bans = bans_records_from_db_records(bans_records_page.items)
        return render_template("hub/bans.html", **self.get_args(), bans=bans, page=bans_records_page, form=form)


register_view(
    hub,
    routes=["/"],
    view_func=Hub.as_view("index"),
)

register_view(
    hub,
    routes=["/hublogs"],
    view_func=HubLogView.as_view("hublogs")
)

register_view(
    hub,
    routes=["/start"],
    view_func=StartServer.as_view("start"),
)

register_view(
    hub,
    routes=["/stop"],
    view_func=StopServer.as_view("stop"),
)

register_view(
    hub,
    routes=["/restart"],
    view_func=RestartServer.as_view("restart"),
)

register_view(
    hub,
    routes=["/configs"],
    view_func=ConfigsView.as_view("configs"),
)

register_view(
    hub,
    routes=["/config_edit"],
    view_func=ConfigEditView.as_view("config_edit"),
)

register_view(
    hub,
    routes=["/gamelogs"],
    view_func=LogsView.as_view("gamelogs")
)

register_view(
    hub,
    routes=["/download_gamelog"],
    view_func=LogDownload.as_view("download_gamelog")
)

register_view(
    hub,
    routes=["/team"],
    view_func=TeamView.as_view("team")
)

register_view(
    hub,
    routes=["/bans"],
    view_func=BansView.as_view("bans")
)
