# -*- coding: utf-8 -*-
"""
    flaskbb.auth.views
    ~~~~~~~~~~~~~~~~~~

    This view provides user authentication, registration and a view for
    resetting the password of a user if he has lost his password

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
import traceback
from datetime import datetime

from flask import Blueprint, current_app, flash, g, redirect, request, url_for, session
from flask.views import MethodView
from flask_babelplus import gettext as _
from flask_login import (
    login_required,
    login_user,
    logout_user,
)
from flask_discord.models import User as DiscordUser

from flaskbb.extensions import limiter
from flaskbb.utils.helpers import (
    format_timedelta,
    register_view,
    render_template,
)
from flaskbb.utils.settings import flaskbb_config

from ..core.auth.registration import UserRegistrationInfo
from .plugins import impl
from .services import (
    authentication_manager_factory,
    registration_service_factory,
)

logger = logging.getLogger('onyx')


class DiscordAuthorize(MethodView):
    def get(self):
        session.get("_flashes", []).clear()  # clear "need refresh" message which is forces by Flask Login
        data = dict(redirect=request.args.get("next"))
        return current_app.discordAuth.create_session(data=data)


class DiscordAuthorizeCallback(MethodView):
    def __init__(self, authentication_manager_factory, registration_service_factory):
        self.authentication_manager_factory = authentication_manager_factory
        self.registration_service_factory = registration_service_factory

    def get(self):
        data = current_app.discordAuth.callback()
        redirect_to = data.get("redirect")
        discord_user: DiscordUser = current_app.discordAuth.fetch_user()
        logger.info("Login: {} ({})".format(discord_user, discord_user.id))

        user = None

        auth_manager = self.authentication_manager_factory()
        try:
            user = auth_manager.authenticate_via_discord(
                discord=str(discord_user.id)
            )
        except:
            pass

        if not user:
            registration_info = UserRegistrationInfo(
                discord=str(discord_user.id),
                display_name=discord_user.username,
                email=discord_user.email,
                group=4
            )

            service = self.registration_service_factory()
            try:
                service.register_via_discord(registration_info)
                user = auth_manager.authenticate_via_discord(
                    discord=str(discord_user.id)
                )
            except Exception as e:
                print(traceback.format_exc())
                flash("Failed authorize with Discord", "danger")

        if user:
            login_user(user, remember=True)

            current_app.pluggy.hook.flaskbb_event_user_registered(
                username=user.username
            )

            return redirect(redirect_to or url_for("forum.index"))

        return redirect(url_for("forum.index"))


class Logout(MethodView):
    decorators = [limiter.exempt, login_required]

    def get(self):
        current_app.discordAuth.revoke()
        logout_user()
        flash(_("Logged out"), "success")
        return redirect(url_for("forum.index"))


@impl(tryfirst=True)
def flaskbb_load_blueprints(app):
    auth = Blueprint("auth", __name__)

    def login_rate_limit():
        """Dynamically load the rate limiting config from the database."""
        # [count] [per|/] [n (optional)] [second|minute|hour|day|month|year]
        return "{count}/{timeout}minutes".format(
            count=flaskbb_config["AUTH_REQUESTS"],
            timeout=flaskbb_config["AUTH_TIMEOUT"]
        )

    def login_rate_limit_message():
        """Display the amount of time left until the user can access the requested
        resource again."""
        current_limit = getattr(g, 'view_rate_limit', None)
        if current_limit is not None:
            window_stats = limiter.limiter.get_window_stats(*current_limit)
            reset_time = datetime.utcfromtimestamp(window_stats[0])
            timeout = reset_time - datetime.utcnow()
        return "{timeout}".format(timeout=format_timedelta(timeout))

    @auth.before_request
    def check_rate_limiting():
        """Check the the rate limits for each request for this blueprint."""
        if not flaskbb_config["AUTH_RATELIMIT_ENABLED"]:
            return None
        return limiter.check()

    @auth.errorhandler(429)
    def login_rate_limit_error(error):
        """Register a custom error handler for a 'Too Many Requests'
        (HTTP CODE 429) error."""
        return render_template(
            "errors/too_many_logins.html", timeout=error.description
        )

    # Activate rate limiting on the whole blueprint
    limiter.limit(
        login_rate_limit, error_message=login_rate_limit_message
    )(auth)

    register_view(auth, routes=['/discord'], view_func=DiscordAuthorize.as_view('discord'))
    register_view(
        auth,
        routes=['/discord-callback'],
        view_func=DiscordAuthorizeCallback.as_view(
            'discord-callback',
            authentication_manager_factory=authentication_manager_factory,
            registration_service_factory=registration_service_factory)
    )

    register_view(auth, routes=['/logout'], view_func=Logout.as_view('logout'))

    app.register_blueprint(auth, url_prefix=app.config['AUTH_URL_PREFIX'])
