from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from flaskbb.extensions import cache, db


class ServerDescriptor(db.Model):
    __tablename__ = "servers"

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    port = db.Column(db.Integer, nullable=False)
    service_name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    branch_name = db.Column(db.String(255), nullable=False)
    dream_maker_binary = db.Column(db.String(255), nullable=False)
    dme_name = db.Column(db.String(255), nullable=False)
    configs_path = db.Column(db.String(255), nullable=False)
    configs_exclude = db.Column(db.JSON, default=list)
    logs_path = db.Column(db.String(255), nullable=False)
    whitelist_channel = db.Column(db.String(255), nullable=False)
    whitelist_role = db.Column(db.String(255), nullable=False)
    hub_visible = db.Column(db.Boolean, nullable=False, default=True)
    ss14 = db.Column(db.Boolean, nullable=False, default=False)

    discord_full_access_titles = db.Column(db.JSON, default=list)
    discord_base_access_titles = db.Column(db.JSON, default=list)
    discord_role_to_group = db.Column(db.JSON, default=dict)
    

    links = db.relationship("ServerAdditionalLink", cascade="all, delete-orphan", backref="server")


class ServerAdditionalLink(db.Model):
    __tablename__ = "server_links"

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(255), ForeignKey("servers.id"), nullable=False)
    what = db.Column(db.String(255), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    href = db.Column(db.String(255), nullable=False)
