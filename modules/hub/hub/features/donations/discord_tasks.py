import discord
import typing

from flask import current_app
from flaskbb.extensions import discordClient, db_hub
from flaskbb.utils.helpers import discord_task

from hub.models import Player, PatronType

@discord_task
async def add_opyxholder_role(user_discord_id):
    assert user_discord_id

    guild: discord.Guild = await discordClient.fetch_guild(current_app.config["COMMUNITY_GUILD_ID"])
    member: discord.Member = await guild.fetch_member(int(user_discord_id))

    discordRoles: map = current_app.config["DISCORD_ROLES"]
    await member.add_roles(guild.get_role(discordRoles["Opyxholder"]))


def __get_all_patron_roles(guild: discord.Guild) -> typing.List[discord.Role]:
    all_patron_role_ids = []
    patron_types: typing.List[PatronType] = db_hub.session.query(PatronType).all()
    for patron_type in patron_types:
        if patron_type.discord_role:
            all_patron_role_ids.append(patron_type.discord_role)

    all_patron_roles = []
    for role_id in all_patron_role_ids:
        role = guild.get_role(int(role_id))
        if role:
            all_patron_roles.append(role)

    return all_patron_roles


@discord_task
async def update_patron_role(player: Player):
    guild: discord.Guild = await discordClient.fetch_guild(current_app.config["COMMUNITY_GUILD_ID"])
    member: discord.Member = await guild.fetch_member(int(player.discord_user_id))

    assert member

    role = player.patron_type and player.patron_type.discord_role

    discordRoles: map = current_app.config["DISCORD_ROLES"]
    await member.remove_roles(*__get_all_patron_roles(guild))

    if role:
        await member.add_roles(guild.get_role(discordRoles["Patron"]), guild.get_role(int(role)))
    else:
        await member.remove_roles(guild.get_role(discordRoles["Patron"]))
