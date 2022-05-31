import discord

from flask import current_app
from flaskbb.extensions import discordClient
from flaskbb.utils.helpers import discord_task

@discord_task
async def add_opyxholder_role_if_needed(user_discord_id):
    assert user_discord_id

    guild: discord.Guild = await discordClient.fetch_guild(current_app.config["COMMUNITY_GUILD_ID"])
    member: discord.Member = await guild.fetch_member(int(user_discord_id))

    discordRoles: map = current_app.config["DISCORD_ROLES"]

    role: discord.Role = None
    for role in member.roles:
        if role.id in [
            discordRoles["Opyxholder"],
            discordRoles["Patron"],
            discordRoles["Nitro Booster"]
        ]:
            return

    await member.add_roles(guild.get_role(discordRoles["Opyxholder"]))
