# -*- coding: utf-8 -*-
"""
    flaskbb.extensions
    ~~~~~~~~~~~~~~~~~~

    The extensions that are used by FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import asyncio

from celery import Celery
from sqlalchemy import MetaData
import discord
from discord import app_commands

from flask_alembic import Alembic
from flask_allows import Allows
from flask_babelplus import Babel
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_themes2 import Themes
from flask_whooshee import Whooshee
from flask_wtf.csrf import CSRFProtect
from flask_apscheduler import APScheduler
from flask_migrate import Migrate

from flaskbb.exceptions import AuthorizationRequired

import copy


# Permissions Manager
allows = Allows(throws=AuthorizationRequired)

# Database
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

metadata_hub = copy.deepcopy(metadata)
metadata_openkeep  = copy.deepcopy(metadata)
metadata_onyx = copy.deepcopy(metadata)

db_hub = SQLAlchemy(metadata=metadata_hub, session_options={"expire_on_commit": False})
db_openkeep = SQLAlchemy(metadata=metadata_openkeep )
db_onyx = SQLAlchemy(metadata=metadata_onyx)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate(db)

# Whooshee (Full Text Search)
whooshee = Whooshee()

# Login
login_manager = LoginManager()

# Mail
mail = Mail()

# Caching
cache = Cache()

# Redis
redis_store = FlaskRedis()

# Debugtoolbar
debugtoolbar = DebugToolbarExtension()

# Migrations
alembic = Alembic()

# Themes
themes = Themes()

# Babel
babel = Babel()

# CSRF
csrf = CSRFProtect()

# Rate Limiting
limiter = Limiter(auto_check=False, key_func=get_remote_address)

# Celery
celery = Celery("flaskbb")

# APScheduler
scheduler = APScheduler()

asyncio.set_event_loop(asyncio.SelectorEventLoop())
discordClient: discord.Client = discord.Client(intents=discord.Intents.default())
discordCommandsTree: app_commands.CommandTree = app_commands.CommandTree(discordClient)
